"""
Demo script to test document generation without needing real Etsy data.
This creates sample documents to verify PDF generation works correctly.
"""

from document_generator import DocumentGenerator
from datetime import datetime

def demo_documents():
    """Generate sample documents for testing."""
    print("🎨 Generating sample documents for testing...\n")
    
    doc_gen = DocumentGenerator()
    
    # Sample order data
    sample_order = {
        'order_id': 'DEMO-12345',
        'order_date': datetime.now().strftime('%Y-%m-%d'),
        'buyer_name': 'Jane Smith',
        'buyer_email': 'jane.smith@example.com',
        'shipping_address': '123 Main Street\nApt 4B\nNew York, NY 10001\nUnited States',
        'total_amount': 89.97,
        'status': 'pending',
        'tracking_number': 'DEMO-TRACKING-123456',
        'shop_name': 'Your Awesome Shop',
        'shop_address': '456 Business Blvd\nYour City, ST 12345'
    }
    
    # Sample items
    sample_items = [
        {
            'sku': 'WIDGET-001',
            'title': 'Handmade Ceramic Mug - Blue',
            'quantity': 2,
            'price': 24.99,
            'location': 'Shelf A-3'
        },
        {
            'sku': 'WIDGET-002',
            'title': 'Artisan Wooden Coaster Set (4 pieces)',
            'quantity': 1,
            'price': 19.99,
            'location': 'Shelf B-1'
        },
        {
            'sku': 'WIDGET-003',
            'title': 'Hand-painted Canvas Tote Bag',
            'quantity': 1,
            'price': 20.00,
            'location': 'Shelf C-2'
        }
    ]
    
    # Generate packing list
    print("📦 Generating packing list...")
    packing_list = doc_gen.generate_packing_list(sample_order, sample_items)
    print(f"   ✅ Created: {packing_list}")
    
    # Generate invoice
    print("\n💰 Generating invoice...")
    shop_info = {
        'shop_name': 'Your Awesome Shop',
        'address': '456 Business Blvd, Your City, ST 12345'
    }
    invoice = doc_gen.generate_invoice(sample_order, sample_items, shop_info)
    print(f"   ✅ Created: {invoice}")
    
    # Generate shipping label
    print("\n📮 Generating shipping label...")
    label = doc_gen.generate_shipping_label(sample_order)
    print(f"   ✅ Created: {label}")
    
    print("\n" + "="*60)
    print("✨ All sample documents generated successfully!")
    print("="*60)
    print(f"\nCheck the 'output' folder to view your PDFs:")
    print(f"  - Packing List: Professional checklist for order fulfillment")
    print(f"  - Invoice: Detailed invoice with itemized pricing")
    print(f"  - Shipping Label: 4x6\" label ready to print")
    print("\n💡 Tip: These documents work without Etsy API credentials.")
    print("   Once you configure your .env file, they'll use real data!\n")

def test_configuration():
    """Test if configuration is set up."""
    print("🔧 Testing configuration...\n")
    
    try:
        from config import Config
        
        has_key = bool(Config.ETSY_API_KEY and Config.ETSY_API_KEY != 'your_api_key_here')
        has_token = bool(Config.ETSY_ACCESS_TOKEN and Config.ETSY_ACCESS_TOKEN != 'your_access_token_here')
        has_shop = bool(Config.ETSY_SHOP_ID and Config.ETSY_SHOP_ID != 'your_shop_id_here')
        
        if has_key and has_token and has_shop:
            print("✅ Configuration looks good!")
            print("   All required Etsy credentials are set.")
            return True
        else:
            print("⚠️  Configuration incomplete:")
            if not has_key:
                print("   ❌ ETSY_API_KEY not set")
            if not has_token:
                print("   ❌ ETSY_ACCESS_TOKEN not set")
            if not has_shop:
                print("   ❌ ETSY_SHOP_ID not set")
            print("\n   📝 Copy .env.example to .env and add your credentials")
            print("   💡 You can still generate demo documents without credentials!\n")
            return False
    except Exception as e:
        print(f"❌ Error checking configuration: {e}\n")
        return False

def test_database():
    """Test database initialization."""
    print("🗄️  Testing database...\n")
    
    try:
        from database import init_db, get_db
        init_db()
        db = get_db()
        db.close()
        print("✅ Database initialized successfully!")
        print("   SQLite database created: etsy_inventory.db\n")
        return True
    except Exception as e:
        print(f"❌ Database error: {e}\n")
        return False

def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("     ETSY APP DEMO & TESTING SCRIPT")
    print("="*60 + "\n")
    
    # Test configuration
    config_ok = test_configuration()
    
    # Test database
    db_ok = test_database()
    
    # Generate demo documents
    if db_ok:
        demo_documents()
    
    print("\n" + "="*60)
    print("Next Steps:")
    print("="*60)
    
    if not config_ok:
        print("1. Set up your .env file with Etsy API credentials")
        print("2. See QUICKSTART.md for instructions")
    
    print("3. Run 'python main.py' to start the full application")
    print("4. Check out README.md for complete documentation")
    print("\n")

if __name__ == '__main__':
    main()
