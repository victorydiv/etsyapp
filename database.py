"""Database models and session management."""
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean, Text, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
from config import Config

Base = declarative_base()
engine = create_engine(Config.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class ItemMaster(Base):
    """Master item catalog - defines all items that can be in inventory."""
    __tablename__ = 'item_master'
    
    id = Column(Integer, primary_key=True)
    sku = Column(String, unique=True, index=True, nullable=False)
    etsy_listing_id = Column(String, unique=True, index=True)
    
    # Item Details
    title = Column(String, nullable=False)
    description = Column(Text)
    category = Column(String)  # raw material, component, finished good, kit
    
    # Pricing
    sell_price = Column(Float)
    base_cost = Column(Float)  # Direct cost (for raw materials/purchased items)
    calculated_cost = Column(Float)  # For kits - sum of component costs
    
    # Physical attributes
    weight = Column(Float)  # in ounces
    dimensions = Column(String)  # LxWxH
    
    # Inventory tracking
    track_inventory = Column(Boolean, default=True)
    reorder_point = Column(Integer, default=5)
    reorder_quantity = Column(Integer, default=10)
    
    # Kit/BOM flag
    is_kit = Column(Boolean, default=False)
    
    # Storage
    storage_location = Column(String)
    
    # Supplier info
    supplier_name = Column(String)
    supplier_sku = Column(String)
    supplier_url = Column(String)
    lead_time_days = Column(Integer)
    
    # Image
    image_path = Column(String)  # Path to item image file
    
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
    name = Column(String, nullable=False, index=True)
    email = Column(String, index=True)
    phone = Column(String)
    
    # Address fields
    address_line1 = Column(String)
    address_line2 = Column(String)
    city = Column(String)
    state = Column(String)
    postal_code = Column(String)
    country = Column(String, default='US')
    
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
    po_number = Column(String, unique=True, index=True)
    
    # Supplier info
    supplier_name = Column(String, nullable=False)
    supplier_reference = Column(String)  # Their order/invoice number
    supplier_url = Column(String)  # Link to order on supplier site (Amazon, etc.)
    
    # Order details
    order_date = Column(DateTime, nullable=False)
    expected_date = Column(DateTime)
    received_date = Column(DateTime)
    
    # Status
    status = Column(String, default='ordered')  # ordered, in_transit, received, cancelled
    
    # Financial
    subtotal = Column(Float)
    shipping_cost = Column(Float)
    tax = Column(Float)
    total_cost = Column(Float)
    
    # Notes
    notes = Column(Text)
    
    # Tracking
    tracking_number = Column(String)
    carrier = Column(String)
    
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
    
    transaction_type = Column(String, nullable=False)  # inbound, outbound, adjustment, kit_assembly
    quantity = Column(Integer, nullable=False)  # Positive for additions, negative for removals
    
    # Reference to source
    reference_type = Column(String)  # inbound_order, outbound_order, adjustment, kit
    reference_id = Column(Integer)
    
    notes = Column(Text)
    performed_by = Column(String)
    
    transaction_date = Column(DateTime, default=datetime.utcnow)
    
    # Relationship
    item = relationship("ItemMaster")

class LocalInventory(Base):
    """DEPRECATED - kept for backwards compatibility during migration."""
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
    customer_id = Column(Integer, ForeignKey('customers.id'), index=True)
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
    
    # Relationship
    customer = relationship("Customer", backref="orders")

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
