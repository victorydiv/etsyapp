"""Migration script to add customers table and customer_id to orders."""
import sqlite3
from pathlib import Path

def migrate():
    """Add customers table and customer_id column to orders."""
    db_path = Path(__file__).parent / "etsy_inventory.db"
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check if customers table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='customers'")
        if not cursor.fetchone():
            print("Creating customers table...")
            cursor.execute("""
                CREATE TABLE customers (
                    id INTEGER PRIMARY KEY,
                    name VARCHAR NOT NULL,
                    email VARCHAR,
                    phone VARCHAR,
                    address_line1 VARCHAR,
                    address_line2 VARCHAR,
                    city VARCHAR,
                    state VARCHAR,
                    postal_code VARCHAR,
                    country VARCHAR DEFAULT 'US',
                    notes TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    last_order_date DATETIME,
                    total_orders INTEGER DEFAULT 0,
                    total_spent FLOAT DEFAULT 0.0,
                    is_active BOOLEAN DEFAULT 1
                )
            """)
            print("✓ Created customers table")
        else:
            print("✓ Customers table already exists")
        
        # Check if customer_id column exists in orders
        cursor.execute("PRAGMA table_info(orders)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'customer_id' not in columns:
            print("Adding customer_id column to orders...")
            cursor.execute("ALTER TABLE orders ADD COLUMN customer_id INTEGER")
            print("✓ Added customer_id column to orders")
        else:
            print("✓ customer_id column already exists in orders")
        
        conn.commit()
        print("\n✓ Migration completed successfully!")
        
    except Exception as e:
        conn.rollback()
        print(f"\n✗ Migration failed: {e}")
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    print("Starting customer migration...\n")
    migrate()
