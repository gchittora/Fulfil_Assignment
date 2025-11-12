"""
Main Flask application.
Handles HTTP requests and serves the UI.
"""
import os
from flask import Flask, jsonify
from flask_cors import CORS
from config import Config
from models import db

app = Flask(__name__)
app.config.from_object(Config)

# Initialize extensions
db.init_app(app)
CORS(app)

# Ensure upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)


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


@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({'status': 'healthy'})


# ============================================================================
# Database Initialization
# ============================================================================

@app.cli.command()
def init_db():
    """Initialize database tables"""
    db.create_all()
    print("Database tables created successfully!")


if __name__ == '__main__':
    app.run(debug=True)
