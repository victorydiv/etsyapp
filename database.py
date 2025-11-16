"""Database models and session management."""
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from config import Config

Base = declarative_base()
engine = create_engine(Config.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class LocalInventory(Base):
    """Model for local inventory tracking."""
    __tablename__ = 'local_inventory'
    
    id = Column(Integer, primary_key=True)
    etsy_listing_id = Column(String, unique=True, index=True)
    sku = Column(String, unique=True, index=True)
    title = Column(String, nullable=False)
    quantity = Column(Integer, default=0)
    price = Column(Float)
    cost = Column(Float)
    location = Column(String)  # Storage location
    last_synced = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Order(Base):
    """Model for order tracking."""
    __tablename__ = 'orders'
    
    id = Column(Integer, primary_key=True)
    etsy_order_id = Column(String, unique=True, index=True)
    buyer_name = Column(String)
    buyer_email = Column(String)
    shipping_address = Column(String)
    total_amount = Column(Float)
    order_date = Column(DateTime)
    status = Column(String)  # pending, packed, shipped, delivered
    tracking_number = Column(String)
    packed = Column(Boolean, default=False)
    invoice_generated = Column(Boolean, default=False)
    label_generated = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class OrderItem(Base):
    """Model for individual items in an order."""
    __tablename__ = 'order_items'
    
    id = Column(Integer, primary_key=True)
    order_id = Column(Integer, index=True)  # References Order.id
    etsy_listing_id = Column(String)
    sku = Column(String)
    title = Column(String)
    quantity = Column(Integer)
    price = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)

def init_db():
    """Initialize the database."""
    Base.metadata.create_all(bind=engine)

def get_db():
    """Get database session."""
    db = SessionLocal()
    try:
        return db
    finally:
        db.close()
