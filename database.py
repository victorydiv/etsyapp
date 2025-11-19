"""Database models and session management."""
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean, Text, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
from config import Config

Base = declarative_base()

def get_database_url():
    """Get database URL from configuration."""
    db_type = Config._get_value('DB_TYPE', 'sqlite')
    
    if db_type == 'mysql':
        host = Config._get_value('MYSQL_HOST', 'localhost')
        port = Config._get_value('MYSQL_PORT', '3306')
        database = Config._get_value('MYSQL_DATABASE', 'etsy_inventory')
        user = Config._get_value('MYSQL_USER', 'root')
        password = Config._get_value('MYSQL_PASSWORD', '')
        return f'mysql+pymysql://{user}:{password}@{host}:{port}/{database}'
    else:
        # Default to SQLite
        db_path = Config._get_value('SQLITE_PATH', 'etsy_inventory.db')
        return f'sqlite:///{db_path}'

# Create engine with dynamic configuration
engine = create_engine(get_database_url())
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class ItemMaster(Base):
    """Master item catalog - defines all items that can be in inventory."""
    __tablename__ = 'item_master'
    
    id = Column(Integer, primary_key=True)
    sku = Column(String(100), unique=True, index=True, nullable=False)
    etsy_listing_id = Column(String(50), unique=True, index=True)
    
    # Item Details
    title = Column(String(500), nullable=False)
    description = Column(Text)
    category = Column(String(100))  # raw material, component, finished good, kit
    
    # Pricing
    sell_price = Column(Float)
    base_cost = Column(Float)  # Direct cost (for raw materials/purchased items)
    calculated_cost = Column(Float)  # For kits - sum of component costs
    
    # Physical attributes
    weight = Column(Float)  # in ounces
    dimensions = Column(String(100))  # LxWxH
    
    # Inventory tracking
    track_inventory = Column(Boolean, default=True)
    reorder_point = Column(Integer, default=5)
    reorder_quantity = Column(Integer, default=10)
    
    # Kit/BOM flag
    is_kit = Column(Boolean, default=False)
    
    # Storage
    storage_location = Column(String(200))
    
    # Supplier info
    supplier_name = Column(String(200))
    supplier_sku = Column(String(100))
    supplier_url = Column(String(2000))
    lead_time_days = Column(Integer)
    
    # Image
    image_path = Column(String(500))  # Path to item image file
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_synced = Column(DateTime)
    
    # Active/Inactive
    is_active = Column(Boolean, default=True)
    
    # Relationships
    bom_components = relationship("BillOfMaterials", 
                                 foreign_keys="BillOfMaterials.parent_item_id",
                                 back_populates="parent_item")

class BillOfMaterials(Base):
    """Bill of Materials - defines what components make up a kit/assembly."""
    __tablename__ = 'bill_of_materials'
    
    id = Column(Integer, primary_key=True)
    parent_item_id = Column(Integer, ForeignKey('item_master.id'), nullable=False)
    component_item_id = Column(Integer, ForeignKey('item_master.id'), nullable=False)
    quantity_required = Column(Float, nullable=False)  # How many of component needed
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    parent_item = relationship("ItemMaster", 
                              foreign_keys=[parent_item_id],
                              back_populates="bom_components")
    component_item = relationship("ItemMaster", foreign_keys=[component_item_id])

class Customer(Base):
    """Customer master table for storing customer information."""
    __tablename__ = 'customers'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False, index=True)
    email = Column(String(200), index=True)
    phone = Column(String(50))
    
    # Address fields
    address_line1 = Column(String(200))
    address_line2 = Column(String(200))
    city = Column(String(100))
    state = Column(String(50))
    postal_code = Column(String(20))
    country = Column(String(50), default='US')
    
    # Notes
    notes = Column(Text)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_order_date = Column(DateTime)
    
    # Stats
    total_orders = Column(Integer, default=0)
    total_spent = Column(Float, default=0.0)
    
    # Active/Inactive
    is_active = Column(Boolean, default=True)

class Inventory(Base):
    """Current inventory levels - actual stock on hand."""
    __tablename__ = 'inventory'
    
    id = Column(Integer, primary_key=True)
    item_id = Column(Integer, ForeignKey('item_master.id'), nullable=False)
    
    quantity_on_hand = Column(Integer, default=0)
    quantity_reserved = Column(Integer, default=0)  # Reserved for orders
    quantity_available = Column(Integer, default=0)  # on_hand - reserved
    
    last_counted = Column(DateTime)
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship
    item = relationship("ItemMaster")

class InboundOrder(Base):
    """Purchase orders / receipts - items coming into inventory."""
    __tablename__ = 'inbound_orders'
    
    id = Column(Integer, primary_key=True)
    po_number = Column(String(50), unique=True, index=True)
    
    # Supplier info
    supplier_name = Column(String(200), nullable=False)
    supplier_reference = Column(String(100))  # Their order/invoice number
    supplier_url = Column(String(2000))  # Link to order on supplier site (Amazon, etc.)
    
    # Order details
    order_date = Column(DateTime, nullable=False)
    expected_date = Column(DateTime)
    received_date = Column(DateTime)
    
    # Status
    status = Column(String(50), default='ordered')  # ordered, in_transit, received, cancelled
    
    # Financial
    subtotal = Column(Float)
    shipping_cost = Column(Float)
    tax = Column(Float)
    total_cost = Column(Float)
    
    # Notes
    notes = Column(Text)
    
    # Tracking
    tracking_number = Column(String(100))
    carrier = Column(String(100))
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class InboundOrderItem(Base):
    """Line items for inbound orders."""
    __tablename__ = 'inbound_order_items'
    
    id = Column(Integer, primary_key=True)
    inbound_order_id = Column(Integer, ForeignKey('inbound_orders.id'), nullable=False)
    item_id = Column(Integer, ForeignKey('item_master.id'), nullable=False)
    
    quantity_ordered = Column(Integer, nullable=False)
    quantity_received = Column(Integer, default=0)
    unit_cost = Column(Float)
    
    # Relationship
    inbound_order = relationship("InboundOrder")
    item = relationship("ItemMaster")

class InventoryTransaction(Base):
    """All inventory movements - audit trail."""
    __tablename__ = 'inventory_transactions'
    
    id = Column(Integer, primary_key=True)
    item_id = Column(Integer, ForeignKey('item_master.id'), nullable=False)
    
    transaction_type = Column(String(50), nullable=False)  # inbound, outbound, adjustment, kit_assembly
    quantity = Column(Integer, nullable=False)  # Positive for additions, negative for removals
    
    # Reference to source
    reference_type = Column(String(50))  # inbound_order, outbound_order, adjustment, kit
    reference_id = Column(Integer)
    
    notes = Column(Text)
    performed_by = Column(String(100))
    
    transaction_date = Column(DateTime, default=datetime.utcnow)
    
    # Relationship
    item = relationship("ItemMaster")

class LocalInventory(Base):
    """DEPRECATED - kept for backwards compatibility during migration."""
    __tablename__ = 'local_inventory'
    
    id = Column(Integer, primary_key=True)
    etsy_listing_id = Column(String(50), unique=True, index=True)
    sku = Column(String(100), unique=True, index=True)
    title = Column(String(500), nullable=False)
    quantity = Column(Integer, default=0)
    price = Column(Float)
    cost = Column(Float)
    location = Column(String(200))  # Storage location
    last_synced = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Order(Base):
    """Model for order tracking."""
    __tablename__ = 'orders'
    
    id = Column(Integer, primary_key=True)
    customer_id = Column(Integer, ForeignKey('customers.id'), index=True)
    etsy_order_id = Column(String(50), unique=True, index=True)
    buyer_name = Column(String(200))
    buyer_email = Column(String(200))
    shipping_address = Column(String(500))
    total_amount = Column(Float)
    order_date = Column(DateTime)
    status = Column(String(50))  # pending, packed, shipped, delivered
    tracking_number = Column(String(100))
    packed = Column(Boolean, default=False)
    invoice_generated = Column(Boolean, default=False)
    label_generated = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship
    customer = relationship("Customer", backref="orders")

class OrderItem(Base):
    """Model for individual items in an order."""
    __tablename__ = 'order_items'
    
    id = Column(Integer, primary_key=True)
    order_id = Column(Integer, index=True)  # References Order.id
    etsy_listing_id = Column(String(50))
    sku = Column(String(100))
    title = Column(String(500))
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
