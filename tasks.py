"""
Celery tasks for background processing.
These run in separate worker processes and handle long-running operations.
"""
import csv
import os
from datetime import datetime
from celery import current_task
from celery_app import celery
from models import db, Product
from flask import Flask
from config import Config


def create_app():
    """Create Flask app for Celery context"""
    app = Flask(__name__)
    app.config.from_object(Config)
    db.init_app(app)
    return app


@celery.task(bind=True)
def process_csv_import(self, file_path):
    """
    Process CSV file and import products into database.
    
    This task:
    1. Reads CSV in chunks to avoid memory issues
    2. Validates data
    3. Performs upserts (insert or update based on SKU)
    4. Updates progress in real-time
    5. Cleans up temp file
    
    Args:
        file_path: Path to uploaded CSV file
        
    Returns:
        dict: Summary of import (total, created, updated, errors)
    """
    app = create_app()
    
    with app.app_context():
        total_rows = 0
        processed_rows = 0
        created_count = 0
        updated_count = 0
        error_count = 0
        errors = []
        
        try:
            # First pass: count total rows for progress calculation
            with open(file_path, 'r', encoding='utf-8') as f:
                total_rows = sum(1 for _ in csv.DictReader(f))
            
            # Update initial progress
            self.update_state(
                state='PROGRESS',
                meta={
                    'current': 0,
                    'total': total_rows,
                    'status': 'Starting import...'
                }
            )
            
            # Second pass: process in batches
            batch = []
            batch_size = Config.BATCH_SIZE
            
            with open(file_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                
                for row_num, row in enumerate(reader, 1):
                    try:
                        # Validate required fields
                        if not row.get('sku') or not row.get('name'):
                            errors.append(f"Row {row_num}: Missing SKU or name")
                            error_count += 1
                            continue
                        
                        # Normalize SKU (case-insensitive)
                        sku = row['sku'].strip().upper()
                        
                        # Check if product exists
                        existing = Product.query.filter(
                            db.func.upper(Product.sku) == sku
                        ).first()
                        
                        if existing:
                            # Update existing product
                            existing.name = row['name'].strip()
                            existing.description = row.get('description', '').strip()
                            existing.price = float(row['price']) if row.get('price') else None
                            existing.updated_at = datetime.utcnow()
                            updated_count += 1
                        else:
                            # Create new product
                            product = Product(
                                sku=sku,
                                name=row['name'].strip(),
                                description=row.get('description', '').strip(),
                                price=float(row['price']) if row.get('price') else None,
                                active=True
                            )
                            batch.append(product)
                            created_count += 1
                        
                        processed_rows += 1
                        
                        # Commit batch when it reaches batch_size
                        if len(batch) >= batch_size:
                            db.session.bulk_save_objects(batch)
                            db.session.commit()
                            batch = []
                        
                        # Update progress every 100 rows
                        if processed_rows % 100 == 0:
                            self.update_state(
                                state='PROGRESS',
                                meta={
                                    'current': processed_rows,
                                    'total': total_rows,
                                    'status': f'Processing... {processed_rows}/{total_rows}',
                                    'created': created_count,
                                    'updated': updated_count,
                                    'errors': error_count
                                }
                            )
                    
                    except Exception as e:
                        errors.append(f"Row {row_num}: {str(e)}")
                        error_count += 1
                        continue
                
                # Commit remaining batch
                if batch:
                    db.session.bulk_save_objects(batch)
                    db.session.commit()
            
            # Clean up uploaded file
            if os.path.exists(file_path):
                os.remove(file_path)
            
            return {
                'status': 'completed',
                'total': total_rows,
                'processed': processed_rows,
                'created': created_count,
                'updated': updated_count,
                'errors': error_count,
                'error_details': errors[:10]  # Return first 10 errors
            }
        
        except Exception as e:
            # Clean up on error
            if os.path.exists(file_path):
                os.remove(file_path)
            
            return {
                'status': 'failed',
                'error': str(e)
            }
