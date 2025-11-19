"""Migrate from old LocalInventory to new ItemMaster/Inventory structure."""
from database import (
    Base, engine, SessionLocal, 
    LocalInventory, ItemMaster, Inventory
)
from datetime import datetime

def migrate_inventory():
    """Migrate existing LocalInventory records to new structure."""
    # Create all new tables
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    
    try:
        # Get all existing local inventory items
        old_items = db.query(LocalInventory).all()
        
        print(f"Found {len(old_items)} items to migrate...")
        
        for old_item in old_items:
            # Check if already migrated
            existing = db.query(ItemMaster).filter(
                ItemMaster.sku == old_item.sku
            ).first()
            
            if existing:
                print(f"  Skipping {old_item.sku} - already exists")
                continue
            
            # Create new ItemMaster record
            new_item = ItemMaster(
                sku=old_item.sku,
                etsy_listing_id=old_item.etsy_listing_id,
                title=old_item.title,
                sell_price=old_item.price,
                base_cost=old_item.cost,
                storage_location=old_item.location,
                category='finished good',
                last_synced=old_item.last_synced,
                created_at=old_item.created_at,
                updated_at=old_item.updated_at,
                is_active=True,
                track_inventory=True
            )
            db.add(new_item)
            db.flush()
            
            # Create Inventory record
            inventory = Inventory(
                item_id=new_item.id,
                quantity_on_hand=old_item.quantity,
                quantity_available=old_item.quantity,
                last_updated=old_item.updated_at
            )
            db.add(inventory)
            
            print(f"  Migrated {old_item.sku} - {old_item.title}")
        
        db.commit()
        print("Migration complete!")
        
    except Exception as e:
        db.rollback()
        print(f"Migration failed: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    print("Starting inventory migration...")
    print("This will migrate LocalInventory to ItemMaster/Inventory structure")
    response = input("Continue? (yes/no): ")
    
    if response.lower() == 'yes':
        migrate_inventory()
    else:
        print("Migration cancelled")
