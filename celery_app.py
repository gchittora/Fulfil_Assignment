"""
Celery application configuration.
This is separate from Flask to allow running workers independently.
"""
from celery import Celery
from config import Config

def make_celery():
    """Create and configure Celery instance"""
    celery = Celery(
        'product_importer',
        broker=Config.CELERY_BROKER_URL,
        backend=Config.CELERY_RESULT_BACKEND
    )
    
    celery.conf.update(
        task_serializer='json',
        accept_content=['json'],
        result_serializer='json',
        timezone='UTC',
        enable_utc=True,
        task_track_started=True,  # Important for progress tracking
    )
    
    return celery

celery = make_celery()
