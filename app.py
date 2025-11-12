"""
Main Flask application.
Handles HTTP requests and serves the UI.
"""
import os
from flask import Flask, request, jsonify
from werkzeug.utils import secure_filename
from config import Config
from models import db

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


@app.route('/test')
def test_page():
    """Test upload page"""
    from flask import render_template
    return render_template('test_upload.html')


@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({'status': 'healthy'})


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
        # Save file securely
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        # Queue Celery task
        task = process_csv_import.delay(filepath)
        
        return jsonify({
            'task_id': task.id,
            'status': 'queued',
            'message': 'File uploaded successfully. Processing started.'
        }), 202
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


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
    else:
        # Task failed
        response = {
            'state': task.state,
            'status': str(task.info)
        }
    
    return jsonify(response)


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
