"""
Main Flask application.
Handles HTTP requests and serves the UI.
"""
import os
from flask import Flask, request, jsonify
from werkzeug.utils import secure_filename
from config import Config
from models import db, Product, Webhook

app = Flask(__name__)
app.config.from_object(Config)

# Initialize extensions
db.init_app(app)

# Import after app is created to avoid circular imports
from celery.result import AsyncResult
from celery_app import celery

# Ensure upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)


def allowed_file(filename):
    """Check if file has allowed extension"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() == 'csv'


# ============================================================================
# Test Routes
# ============================================================================

@app.route('/')
def index():
    """Test route to verify Flask is working"""
    return jsonify({
        'message': 'Product Importer API',
        'status': 'running',
        'version': '1.0.0'
    })


@app.route('/ui')
def ui():
    """Main UI"""
    from flask import render_template
    return render_template('index.html')


@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({'status': 'healthy'})


@app.route('/health/celery')
def health_celery():
    """Check if Celery worker is available"""
    try:
        from celery_app import celery
        # Try to ping the worker with timeout
        inspect = celery.control.inspect(timeout=3.0)
        stats = inspect.stats()
        
        if stats:
            return jsonify({
                'status': 'healthy',
                'workers': len(stats),
                'worker_info': stats
            })
        else:
            return jsonify({
                'status': 'unhealthy',
                'error': 'No workers available',
                'redis_url': Config.REDIS_URL.split('@')[-1] if '@' in Config.REDIS_URL else 'localhost'
            }), 503
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'error': str(e),
            'error_type': type(e).__name__,
            'redis_url': Config.REDIS_URL.split('@')[-1] if '@' in Config.REDIS_URL else 'localhost'
        }), 503


@app.route('/debug/config')
def debug_config():
    """Debug endpoint to check configuration (remove in production)"""
    return jsonify({
        'redis_url_host': Config.REDIS_URL.split('@')[-1] if '@' in Config.REDIS_URL else Config.REDIS_URL.split('//')[1].split('/')[0],
        'database_connected': db.engine.url.database,
        'upload_folder': Config.UPLOAD_FOLDER,
        'batch_size': Config.BATCH_SIZE
    })


# ============================================================================
# Product Import Routes
# ============================================================================

@app.route('/api/upload', methods=['POST'])
def upload_file():
    """
    Handle CSV file upload and queue import task.
    Returns task ID for progress tracking.
    """
    # Import here to avoid circular import issues
    from tasks import process_csv_import
    
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if not allowed_file(file.filename):
        return jsonify({'error': 'Only CSV files are allowed'}), 400
    
    try:
        # Read CSV content into memory
        csv_content = file.read().decode('utf-8')
        filename = secure_filename(file.filename)
        
        # Try to queue Celery task with CSV content (not file path)
        try:
            task = process_csv_import.delay(csv_content, filename)
            
            return jsonify({
                'task_id': task.id,
                'status': 'queued',
                'message': 'File uploaded successfully. Processing started.'
            }), 202
        except Exception as celery_error:
            # Celery is unavailable - log the error and return helpful message
            app.logger.error(f"Celery connection failed: {str(celery_error)}")
            return jsonify({
                'error': 'Task queue is currently unavailable',
                'details': 'The background worker service is not responding. Please try again in a few moments or contact support.',
                'technical_details': str(celery_error)
            }), 503
    
    except UnicodeDecodeError:
        return jsonify({'error': 'Invalid CSV file encoding. Please use UTF-8 encoding.'}), 400
    except Exception as e:
        app.logger.error(f"Upload error: {str(e)}")
        return jsonify({'error': f'Upload failed: {str(e)}'}), 500


@app.route('/api/progress/<task_id>', methods=['GET'])
def get_progress(task_id):
    """
    Get progress of import task.
    Frontend polls this endpoint to update progress bar.
    """
    task = AsyncResult(task_id, app=celery)
    
    if task.state == 'PENDING':
        response = {
            'state': task.state,
            'status': 'Task is waiting to start...'
        }
    elif task.state == 'PROGRESS':
        response = {
            'state': task.state,
            'current': task.info.get('current', 0),
            'total': task.info.get('total', 1),
            'status': task.info.get('status', ''),
            'created': task.info.get('created', 0),
            'updated': task.info.get('updated', 0),
            'errors': task.info.get('errors', 0)
        }
    elif task.state == 'SUCCESS':
        response = {
            'state': task.state,
            'result': task.info
        }
    elif task.state == 'FAILURE':
        # Task failed with exception
        response = {
            'state': task.state,
            'status': 'Task failed',
            'error': str(task.info) if task.info else 'Unknown error'
        }
    else:
        # Other states (RETRY, REVOKED, etc.)
        response = {
            'state': task.state,
            'status': str(task.info) if task.info else 'Task in unknown state'
        }
    
    return jsonify(response)


@app.route('/api/cancel/<task_id>', methods=['POST'])
def cancel_task(task_id):
    """Cancel/revoke a running task"""
    from celery_app import celery
    celery.control.revoke(task_id, terminate=True, signal='SIGKILL')
    return jsonify({'message': 'Task cancelled'})


# ============================================================================
# Product CRUD Routes
# ============================================================================

@app.route('/api/products', methods=['GET'])
def get_products():
    """Get paginated list of products with optional filters"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    sku_filter = request.args.get('sku', '')
    name_filter = request.args.get('name', '')
    active_filter = request.args.get('active', '')
    
    query = Product.query
    
    if sku_filter:
        query = query.filter(Product.sku.ilike(f'%{sku_filter}%'))
    if name_filter:
        query = query.filter(Product.name.ilike(f'%{name_filter}%'))
    if active_filter:
        active_bool = active_filter.lower() == 'true'
        query = query.filter(Product.active == active_bool)
    
    pagination = query.order_by(Product.created_at.desc()).paginate(
        page=page,
        per_page=per_page,
        error_out=False
    )
    
    return jsonify({
        'products': [p.to_dict() for p in pagination.items],
        'total': pagination.total,
        'pages': pagination.pages,
        'current_page': page
    })


@app.route('/api/products/<int:product_id>', methods=['GET'])
def get_product(product_id):
    """Get single product by ID"""
    product = Product.query.get_or_404(product_id)
    return jsonify(product.to_dict())


@app.route('/api/products', methods=['POST'])
def create_product():
    """Create new product"""
    data = request.get_json()
    
    if not data.get('sku') or not data.get('name'):
        return jsonify({'error': 'SKU and name are required'}), 400
    
    sku = data['sku'].strip().upper()
    existing = Product.query.filter(db.func.upper(Product.sku) == sku).first()
    if existing:
        return jsonify({'error': 'Product with this SKU already exists'}), 409
    
    product = Product(
        sku=sku,
        name=data['name'].strip(),
        description=data.get('description', '').strip(),
        price=data.get('price'),
        active=data.get('active', True)
    )
    
    db.session.add(product)
    db.session.commit()
    
    return jsonify(product.to_dict()), 201


@app.route('/api/products/<int:product_id>', methods=['PUT'])
def update_product(product_id):
    """Update existing product"""
    product = Product.query.get_or_404(product_id)
    data = request.get_json()
    
    if 'name' in data:
        product.name = data['name'].strip()
    if 'description' in data:
        product.description = data['description'].strip()
    if 'price' in data:
        product.price = data['price']
    if 'active' in data:
        product.active = data['active']
    
    db.session.commit()
    
    return jsonify(product.to_dict())


@app.route('/api/products/<int:product_id>', methods=['DELETE'])
def delete_product(product_id):
    """Delete single product"""
    product = Product.query.get_or_404(product_id)
    db.session.delete(product)
    db.session.commit()
    
    return jsonify({'message': 'Product deleted successfully'})


@app.route('/api/products/bulk-delete', methods=['DELETE'])
def bulk_delete_products():
    """Delete all products"""
    count = Product.query.delete()
    db.session.commit()
    
    return jsonify({
        'message': f'Successfully deleted {count} products',
        'count': count
    })


# ============================================================================
# Webhook Routes
# ============================================================================

@app.route('/api/webhooks', methods=['GET'])
def get_webhooks():
    """Get all webhooks"""
    webhooks = Webhook.query.all()
    return jsonify([w.to_dict() for w in webhooks])


@app.route('/api/webhooks', methods=['POST'])
def create_webhook():
    """Create new webhook"""
    data = request.get_json()
    
    if not data.get('url') or not data.get('event_type'):
        return jsonify({'error': 'URL and event_type are required'}), 400
    
    webhook = Webhook(
        url=data['url'],
        event_type=data['event_type'],
        enabled=data.get('enabled', True)
    )
    
    db.session.add(webhook)
    db.session.commit()
    
    return jsonify(webhook.to_dict()), 201


@app.route('/api/webhooks/<int:webhook_id>', methods=['PUT'])
def update_webhook(webhook_id):
    """Update webhook"""
    webhook = Webhook.query.get_or_404(webhook_id)
    data = request.get_json()
    
    if 'url' in data:
        webhook.url = data['url']
    if 'event_type' in data:
        webhook.event_type = data['event_type']
    if 'enabled' in data:
        webhook.enabled = data['enabled']
    
    db.session.commit()
    
    return jsonify(webhook.to_dict())


@app.route('/api/webhooks/<int:webhook_id>', methods=['DELETE'])
def delete_webhook(webhook_id):
    """Delete webhook"""
    webhook = Webhook.query.get_or_404(webhook_id)
    db.session.delete(webhook)
    db.session.commit()
    
    return jsonify({'message': 'Webhook deleted successfully'})


# ============================================================================
# Database Initialization
# ============================================================================

@app.cli.command()
def init_db():
    """Initialize database tables"""
    db.create_all()
    print("Database tables created successfully!")


if __name__ == '__main__':
    print("=" * 60)
    print("Flask app starting...")
    print(f"Routes registered: {[str(rule) for rule in app.url_map.iter_rules()]}")
    print("=" * 60)
    app.run(debug=True, host='127.0.0.1', port=5000)
