"""
Database models for the application.
"""
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class Product(db.Model):
    """
    Product model - stores product information from CSV imports.
    SKU is case-insensitive unique identifier.
    """
    __tablename__ = 'products'
    
    id = db.Column(db.Integer, primary_key=True)
    sku = db.Column(db.String(100), unique=True, nullable=False, index=True)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    price = db.Column(db.Numeric(10, 2))
    active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    def to_dict(self):
        """Convert product to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'sku': self.sku,
            'name': self.name,
            'description': self.description,
            'price': float(self.price) if self.price else None,
            'active': self.active,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }


class Webhook(db.Model):
    """
    Webhook model - stores webhook configurations.
    Webhooks are triggered on product events (create, update, delete).
    """
    __tablename__ = 'webhooks'
    
    id = db.Column(db.Integer, primary_key=True)
    url = db.Column(db.String(500), nullable=False)
    event_type = db.Column(db.String(50), nullable=False)  # 'create', 'update', 'delete', 'all'
    enabled = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    def to_dict(self):
        """Convert webhook to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'url': self.url,
            'event_type': self.event_type,
            'enabled': self.enabled,
            'created_at': self.created_at.isoformat()
        }
