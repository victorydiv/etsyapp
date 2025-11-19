"""Migration script to add image_path column to item_master."""
import sqlite3
from pathlib import Path

def migrate():
    """Add image_path column to item_master."""
    db_path = Path(__file__).parent / "etsy_inventory.db"
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check if image_path column exists in item_master
        cursor.execute("PRAGMA table_info(item_master)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'image_path' not in columns:
            print("Adding image_path column to item_master...")
            cursor.execute("ALTER TABLE item_master ADD COLUMN image_path VARCHAR")
            print("✓ Added image_path column to item_master")
        else:
            print("✓ image_path column already exists in item_master")
        
        conn.commit()
        print("\n✓ Migration completed successfully!")
        
    except Exception as e:
        conn.rollback()
        print(f"\n✗ Migration failed: {e}")
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    print("Starting item image migration...\n")
    migrate()
