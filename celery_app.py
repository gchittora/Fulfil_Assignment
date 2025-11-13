"""
Celery application configuration.
This is separate from Flask to allow running workers independently.
"""
import ssl
from celery import Celery
from config import Config

def make_celery():
    """Create and configure Celery instance"""
    celery = Celery(
        'product_importer',
        broker=Config.CELERY_BROKER_URL,
        backend=Config.CELERY_RESULT_BACKEND,
        include=['tasks']  # Import tasks module
    )
    
    # Configure SSL for Redis if using rediss://
    broker_use_ssl = None
    redis_backend_use_ssl = None
    
    if Config.REDIS_URL.startswith('rediss://'):
        broker_use_ssl = {
            'ssl_cert_reqs': ssl.CERT_NONE
        }
        redis_backend_use_ssl = {
            'ssl_cert_reqs': ssl.CERT_NONE
        }
    
    celery.conf.update(
        task_serializer='json',
        accept_content=['json'],
        result_serializer='json',
        timezone='UTC',
        enable_utc=True,
        task_track_started=True,  # Important for progress tracking
        broker_use_ssl=broker_use_ssl,
        redis_backend_use_ssl=redis_backend_use_ssl,
        broker_connection_retry_on_startup=True,
        broker_connection_timeout=3,
        broker_connection_max_retries=1,
        task_ignore_result=False,
        task_store_errors_even_if_ignored=True,
        result_backend_transport_options={
            'socket_connect_timeout': 2,
            'socket_timeout': 2,
            'socket_keepalive': True,
            'health_check_interval': 10,
        },
        broker_transport_options={
            'socket_connect_timeout': 2,
            'socket_timeout': 2,
            'socket_keepalive': True,
            'health_check_interval': 10,
            'visibility_timeout': 3600,
            'max_connections': 10,
        },
        broker_pool_limit=1,  # Limit connection pool
        result_expires=3600,
    )
    
    return celery

celery = make_celery()
