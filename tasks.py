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
def process_csv_import(self, csv_content, filename):
    """
    Process CSV content and import products into database.
    
    This task:
    1. Reads CSV from string content (not file)
    2. Validates data
    3. Performs upserts (insert or update based on SKU)
    4. Updates progress in real-time
    
    Args:
        csv_content: CSV file content as string
        filename: Original filename (for logging)
        
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
            # Parse CSV from string content
            import io
            csv_file = io.StringIO(csv_content)
            
            # First pass: count total rows for progress calculation
            reader = csv.DictReader(csv_file)
            rows = list(reader)  # Read all rows into memory
            total_rows = len(rows)
            
            # Update initial progress
            self.update_state(
                state='PROGRESS',
                meta={
                    'current': 0,
                    'total': total_rows,
                    'status': 'Starting import...'
                }
            )
            
            # Process in batches
            batch = []
            batch_skus = set()  # Track SKUs in current batch to avoid duplicates
            batch_size = Config.BATCH_SIZE
            
            for row_num, row in enumerate(rows, 1):
                try:
                        # Validate required fields
                        if not row.get('sku') or not row.get('name'):
                            errors.append(f"Row {row_num}: Missing SKU or name")
                            error_count += 1
                            continue
                        
                        # Normalize SKU (case-insensitive)
                        sku = row['sku'].strip().upper()
                        
                        # Check if product exists in database
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
                            # Check if SKU is already in current batch
                            if sku in batch_skus:
                                # Skip duplicate within batch
                                errors.append(f"Row {row_num}: Duplicate SKU {sku} in file")
                                error_count += 1
                                continue
                            
                            # Create new product
                            product = Product(
                                sku=sku,
                                name=row['name'].strip(),
                                description=row.get('description', '').strip(),
                                price=float(row['price']) if row.get('price') else None,
                                active=True
                            )
                            batch.append(product)
                            batch_skus.add(sku)  # Track this SKU
                            created_count += 1
                        
                        processed_rows += 1
                        
                    # Commit batch when it reaches batch_size
                    if len(batch) >= batch_size:
                        db.session.bulk_save_objects(batch)
                        db.session.commit()
                        batch = []
                        batch_skus = set()  # Clear batch SKU tracker
                    
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
            return {
                'status': 'failed',
                'error': str(e)
            }
