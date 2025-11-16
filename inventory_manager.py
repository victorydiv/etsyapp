"""Inventory management module for syncing local and Etsy inventory."""
from datetime import datetime
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from database import LocalInventory, get_db
from etsy_api import EtsyAPIClient

class InventoryManager:
    """Manage local and Etsy inventory synchronization."""
    
    def __init__(self):
        """Initialize the inventory manager."""
        self.etsy_client = EtsyAPIClient()
    
    def sync_from_etsy(self, db: Session = None) -> int:
        """Sync inventory from Etsy to local database."""
        if db is None:
            db = get_db()
        
        try:
            listings = self.etsy_client.get_shop_listings()
            count = 0
            
            for listing in listings:
                listing_id = str(listing.get('listing_id'))
                
                # Get inventory details
                inventory_data = self.etsy_client.get_listing_inventory(listing_id)
                products = inventory_data.get('products', [])
                
                # Get or create local inventory record
                local_item = db.query(LocalInventory).filter(
                    LocalInventory.etsy_listing_id == listing_id
                ).first()
                
                if not local_item:
                    local_item = LocalInventory()
                    local_item.etsy_listing_id = listing_id
                    db.add(local_item)
                
                # Update fields
                local_item.title = listing.get('title', '')
                local_item.price = float(listing.get('price', {}).get('amount', 0)) / float(listing.get('price', {}).get('divisor', 100))
                local_item.sku = listing.get('sku', '')
                
                # Sum quantities from all products
                total_quantity = sum(p.get('offerings', [{}])[0].get('quantity', 0) for p in products if p.get('offerings'))
                local_item.quantity = total_quantity
                
                local_item.last_synced = datetime.utcnow()
                count += 1
            
            db.commit()
            return count
        finally:
            if db:
                db.close()
    
    def sync_to_etsy(self, listing_id: str, quantity: int, db: Session = None) -> bool:
        """Sync local inventory changes to Etsy."""
        if db is None:
            db = get_db()
        
        try:
            local_item = db.query(LocalInventory).filter(
                LocalInventory.etsy_listing_id == listing_id
            ).first()
            
            if not local_item:
                raise ValueError(f"Listing {listing_id} not found in local inventory")
            
            # Get current inventory structure
            inventory_data = self.etsy_client.get_listing_inventory(listing_id)
            products = inventory_data.get('products', [])
            
            # Update quantities
            for product in products:
                if product.get('offerings'):
                    product['offerings'][0]['quantity'] = quantity
            
            # Push update to Etsy
            self.etsy_client.update_listing_inventory(listing_id, products)
            
            # Update local record
            local_item.quantity = quantity
            local_item.last_synced = datetime.utcnow()
            db.commit()
            
            return True
        finally:
            if db:
                db.close()
    
    def update_local_inventory(self, listing_id: str, quantity: int, 
                               sync_to_etsy: bool = False, db: Session = None) -> bool:
        """Update local inventory and optionally sync to Etsy."""
        if db is None:
            db = get_db()
        
        try:
            local_item = db.query(LocalInventory).filter(
                LocalInventory.etsy_listing_id == listing_id
            ).first()
            
            if not local_item:
                raise ValueError(f"Listing {listing_id} not found in local inventory")
            
            local_item.quantity = quantity
            local_item.updated_at = datetime.utcnow()
            db.commit()
            
            if sync_to_etsy:
                self.sync_to_etsy(listing_id, quantity, db)
            
            return True
        finally:
            if db:
                db.close()
    
    def get_local_inventory(self, db: Session = None) -> List[Dict]:
        """Get all local inventory items."""
        if db is None:
            db = get_db()
        
        try:
            items = db.query(LocalInventory).all()
            return [{
                'id': item.id,
                'etsy_listing_id': item.etsy_listing_id,
                'sku': item.sku,
                'title': item.title,
                'quantity': item.quantity,
                'price': item.price,
                'cost': item.cost,
                'location': item.location,
                'last_synced': item.last_synced.isoformat() if item.last_synced else None
            } for item in items]
        finally:
            if db:
                db.close()
    
    def get_low_stock_items(self, threshold: int = 5, db: Session = None) -> List[Dict]:
        """Get items with low stock."""
        if db is None:
            db = get_db()
        
        try:
            items = db.query(LocalInventory).filter(
                LocalInventory.quantity <= threshold
            ).all()
            return [{
                'etsy_listing_id': item.etsy_listing_id,
                'sku': item.sku,
                'title': item.title,
                'quantity': item.quantity
            } for item in items]
        finally:
            if db:
                db.close()
