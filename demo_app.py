"""Demo version of the main app that works without Etsy API credentials."""
import sys
from datetime import datetime, timedelta
from database import init_db, get_db, LocalInventory, Order, OrderItem
from document_generator import DocumentGenerator
from sqlalchemy.orm import Session

class EtsyAppDemo:
    """Demo application class with sample data."""
    
    def __init__(self):
        """Initialize the demo application."""
        # Initialize database
        init_db()
        self.doc_generator = DocumentGenerator()
        self.setup_sample_data()
    
    def setup_sample_data(self):
        """Create sample inventory and order data."""
        db = get_db()
        
        # Check if we already have sample data
        existing = db.query(LocalInventory).first()
        if existing:
            db.close()
            return
        
        print("\n🎨 Creating sample data...")
        
        # Sample inventory items
        sample_items = [
            {
                'etsy_listing_id': '1001',
                'sku': 'MUG-BLUE-001',
                'title': 'Handmade Ceramic Mug - Ocean Blue',
                'quantity': 15,
                'price': 24.99,
                'cost': 12.50,
                'location': 'Shelf A-3'
            },
            {
                'etsy_listing_id': '1002',
                'sku': 'COASTER-WOOD-SET',
                'title': 'Artisan Wooden Coaster Set (4 pieces)',
                'quantity': 8,
                'price': 19.99,
                'cost': 8.00,
                'location': 'Shelf B-1'
            },
            {
                'etsy_listing_id': '1003',
                'sku': 'TOTE-CANVAS-001',
                'title': 'Hand-painted Canvas Tote Bag',
                'quantity': 3,
                'price': 29.99,
                'cost': 15.00,
                'location': 'Shelf C-2'
            },
            {
                'etsy_listing_id': '1004',
                'sku': 'BOWL-CERAMIC-LARGE',
                'title': 'Large Ceramic Serving Bowl - Rustic',
                'quantity': 12,
                'price': 45.00,
                'cost': 22.00,
                'location': 'Shelf A-1'
            },
            {
                'etsy_listing_id': '1005',
                'sku': 'CANDLE-SOY-LAVENDER',
                'title': 'Natural Soy Candle - Lavender Dreams',
                'quantity': 25,
                'price': 16.99,
                'cost': 6.50,
                'location': 'Shelf D-4'
            },
            {
                'etsy_listing_id': '1006',
                'sku': 'PLATE-CERAMIC-SET',
                'title': 'Ceramic Dinner Plate Set (4 plates)',
                'quantity': 2,
                'price': 89.99,
                'cost': 40.00,
                'location': 'Shelf A-2'
            },
            {
                'etsy_listing_id': '1007',
                'sku': 'SCARF-WOOL-WINTER',
                'title': 'Hand-knitted Wool Winter Scarf',
                'quantity': 6,
                'price': 38.00,
                'cost': 18.00,
                'location': 'Shelf E-1'
            }
        ]
        
        for item_data in sample_items:
            item = LocalInventory(**item_data)
            item.last_synced = datetime.utcnow()
            db.add(item)
        
        db.commit()
        
        # Sample orders
        sample_order = Order(
            etsy_order_id='ORDER-2024-001',
            buyer_name='Sarah Johnson',
            buyer_email='sarah.j@example.com',
            shipping_address='123 Maple Street\nApt 4B\nPortland, OR 97201\nUnited States',
            total_amount=69.97,
            order_date=datetime.utcnow() - timedelta(days=1),
            status='pending',
            packed=False,
            invoice_generated=False,
            label_generated=False
        )
        db.add(sample_order)
        db.commit()
        
        # Sample order items
        order_items = [
            OrderItem(
                order_id=sample_order.id,
                etsy_listing_id='1001',
                sku='MUG-BLUE-001',
                title='Handmade Ceramic Mug - Ocean Blue',
                quantity=2,
                price=24.99
            ),
            OrderItem(
                order_id=sample_order.id,
                etsy_listing_id='1002',
                sku='COASTER-WOOD-SET',
                title='Artisan Wooden Coaster Set (4 pieces)',
                quantity=1,
                price=19.99
            )
        ]
        
        for item in order_items:
            db.add(item)
        
        db.commit()
        db.close()
        print("✅ Sample data created!\n")
    
    def show_menu(self):
        """Display the main menu."""
        print("\n" + "="*60)
        print("           ETSY SHOP MANAGEMENT APP - DEMO MODE")
        print("="*60)
        print("\n📦 INVENTORY MANAGEMENT (Works in Demo)")
        print("  1. View local inventory")
        print("  2. Update inventory quantity")
        print("  3. View low stock items")
        print("  4. Add new inventory item")
        
        print("\n📋 ORDER MANAGEMENT (Demo Data)")
        print("  5. View all orders")
        print("  6. View order details")
        print("  7. Mark order as packed")
        
        print("\n📄 DOCUMENT GENERATION (Fully Functional)")
        print("  8. Generate packing list")
        print("  9. Generate invoice")
        print("  10. Generate shipping label")
        print("  11. Generate all documents for order")
        
        print("\n⚙️  OTHER")
        print("  12. Open output folder")
        print("  0. Exit")
        print("="*60)
        print("\n💡 Note: This is DEMO mode with sample data.")
        print("   Configure .env with Etsy API to sync real data.")
    
    def view_inventory(self):
        """View local inventory."""
        print("\n📦 Local Inventory:")
        db = get_db()
        items = db.query(LocalInventory).all()
        
        if not items:
            print("No items in local inventory.")
            db.close()
            return
        
        print(f"\n{'ID':<8} {'SKU':<20} {'Title':<40} {'Qty':<6} {'Price':<10} {'Location':<12}")
        print("-" * 105)
        for item in items:
            title = item.title[:37] + '...' if len(item.title) > 40 else item.title
            price_str = f"${item.price:.2f}" if item.price else "N/A"
            print(f"{item.etsy_listing_id:<8} {item.sku:<20} {title:<40} "
                  f"{item.quantity:<6} {price_str:<10} {item.location or 'N/A':<12}")
        
        db.close()
    
    def update_inventory_quantity(self):
        """Update inventory quantity."""
        listing_id = input("\nEnter listing ID: ").strip()
        quantity = input("Enter new quantity: ").strip()
        
        try:
            quantity = int(quantity)
            db = get_db()
            item = db.query(LocalInventory).filter(
                LocalInventory.etsy_listing_id == listing_id
            ).first()
            
            if not item:
                print(f"❌ Listing {listing_id} not found")
                db.close()
                return
            
            old_qty = item.quantity
            item.quantity = quantity
            item.updated_at = datetime.utcnow()
            db.commit()
            db.close()
            
            print(f"✅ Updated {item.title}")
            print(f"   Quantity: {old_qty} → {quantity}")
            print("\n💡 In full mode, you can sync this to Etsy automatically")
        except Exception as e:
            print(f"❌ Error updating inventory: {e}")
    
    def view_low_stock(self):
        """View low stock items."""
        threshold = input("\nEnter threshold (default 5): ").strip()
        threshold = int(threshold) if threshold else 5
        
        db = get_db()
        items = db.query(LocalInventory).filter(
            LocalInventory.quantity <= threshold
        ).all()
        
        if not items:
            print(f"✅ No items with stock below {threshold}")
            db.close()
            return
        
        print(f"\n⚠️  Items with stock <= {threshold}:")
        print(f"\n{'ID':<10} {'SKU':<20} {'Title':<40} {'Qty':<6}")
        print("-" * 80)
        for item in items:
            title = item.title[:37] + '...' if len(item.title) > 40 else item.title
            print(f"{item.etsy_listing_id:<10} {item.sku:<20} {title:<40} {item.quantity:<6}")
        
        db.close()
    
    def add_inventory_item(self):
        """Add a new inventory item."""
        print("\n➕ Add New Inventory Item")
        
        listing_id = input("Listing ID: ").strip()
        sku = input("SKU: ").strip()
        title = input("Title: ").strip()
        quantity = input("Quantity: ").strip()
        price = input("Price: ").strip()
        cost = input("Cost (optional): ").strip()
        location = input("Storage location (optional): ").strip()
        
        try:
            db = get_db()
            item = LocalInventory(
                etsy_listing_id=listing_id,
                sku=sku,
                title=title,
                quantity=int(quantity),
                price=float(price) if price else None,
                cost=float(cost) if cost else None,
                location=location if location else None,
                last_synced=datetime.utcnow()
            )
            db.add(item)
            db.commit()
            db.close()
            
            print(f"\n✅ Added {title} to inventory!")
        except Exception as e:
            print(f"❌ Error adding item: {e}")
    
    def view_orders(self):
        """View orders."""
        print("\n📋 Orders:")
        db = get_db()
        orders = db.query(Order).all()
        
        if not orders:
            print("No orders found.")
            db.close()
            return
        
        print(f"\n{'ID':<6} {'Order ID':<18} {'Customer':<25} {'Amount':<10} {'Status':<10} {'Packed':<8}")
        print("-" * 85)
        for order in orders:
            print(f"{order.id:<6} {order.etsy_order_id:<18} "
                  f"{order.buyer_name[:23]:<25} ${order.total_amount:<9.2f} "
                  f"{order.status:<10} {'Yes' if order.packed else 'No':<8}")
        
        db.close()
    
    def view_order_details(self):
        """View order details."""
        order_id = input("\nEnter order ID (local database ID): ").strip()
        
        try:
            order_id = int(order_id)
            db = get_db()
            order = db.query(Order).filter(Order.id == order_id).first()
            
            if not order:
                print(f"❌ Order {order_id} not found")
                db.close()
                return
            
            print("\n" + "="*60)
            print(f"Order Details - {order.etsy_order_id}")
            print("="*60)
            print(f"Customer: {order.buyer_name}")
            print(f"Email: {order.buyer_email}")
            print(f"Status: {order.status}")
            print(f"Total: ${order.total_amount:.2f}")
            print(f"Order Date: {order.order_date.strftime('%Y-%m-%d %H:%M')}")
            print(f"\nShipping Address:")
            print(order.shipping_address)
            
            # Get items
            items = db.query(OrderItem).filter(OrderItem.order_id == order_id).all()
            print(f"\n{'SKU':<20} {'Title':<40} {'Qty':<6} {'Price':<10}")
            print("-" * 80)
            for item in items:
                title = item.title[:37] + '...' if len(item.title) > 40 else item.title
                print(f"{item.sku:<20} {title:<40} {item.quantity:<6} ${item.price:<9.2f}")
            
            db.close()
        except Exception as e:
            print(f"❌ Error: {e}")
    
    def mark_packed(self):
        """Mark order as packed."""
        order_id = input("\nEnter order ID (local database ID): ").strip()
        
        try:
            order_id = int(order_id)
            db = get_db()
            order = db.query(Order).filter(Order.id == order_id).first()
            
            if not order:
                print(f"❌ Order {order_id} not found")
                db.close()
                return
            
            order.packed = True
            order.status = 'packed'
            db.commit()
            db.close()
            
            print(f"✅ Order {order.etsy_order_id} marked as packed!")
        except Exception as e:
            print(f"❌ Error: {e}")
    
    def generate_packing_list(self):
        """Generate packing list."""
        order_id = input("\nEnter order ID (local database ID): ").strip()
        
        try:
            order_id = int(order_id)
            db = get_db()
            order = db.query(Order).filter(Order.id == order_id).first()
            
            if not order:
                print(f"❌ Order {order_id} not found")
                db.close()
                return
            
            items = db.query(OrderItem).all()
            items_data = [{
                'sku': item.sku,
                'title': item.title,
                'quantity': item.quantity,
                'location': 'N/A'
            } for item in items]
            
            # Get inventory locations
            for item_data in items_data:
                inv_item = db.query(LocalInventory).filter(
                    LocalInventory.sku == item_data['sku']
                ).first()
                if inv_item and inv_item.location:
                    item_data['location'] = inv_item.location
            
            order_data = {
                'order_id': order.etsy_order_id,
                'order_date': order.order_date.strftime('%Y-%m-%d'),
                'buyer_name': order.buyer_name,
                'shipping_address': order.shipping_address
            }
            
            pdf_path = self.doc_generator.generate_packing_list(order_data, items_data)
            print(f"✅ Packing list generated: {pdf_path}")
            
            db.close()
        except Exception as e:
            print(f"❌ Error: {e}")
    
    def generate_invoice(self):
        """Generate invoice."""
        order_id = input("\nEnter order ID (local database ID): ").strip()
        
        try:
            order_id = int(order_id)
            db = get_db()
            order = db.query(Order).filter(Order.id == order_id).first()
            
            if not order:
                print(f"❌ Order {order_id} not found")
                db.close()
                return
            
            items = db.query(OrderItem).filter(OrderItem.order_id == order_id).all()
            items_data = [{
                'sku': item.sku,
                'title': item.title,
                'quantity': item.quantity,
                'price': item.price
            } for item in items]
            
            order_data = {
                'order_id': order.etsy_order_id,
                'order_date': order.order_date.strftime('%Y-%m-%d'),
                'buyer_name': order.buyer_name,
                'buyer_email': order.buyer_email,
                'total_amount': order.total_amount,
                'status': order.status
            }
            
            shop_info = {
                'shop_name': 'Your Awesome Shop',
                'address': '456 Business Blvd, Your City, ST 12345'
            }
            
            pdf_path = self.doc_generator.generate_invoice(order_data, items_data, shop_info)
            print(f"✅ Invoice generated: {pdf_path}")
            
            order.invoice_generated = True
            db.commit()
            db.close()
        except Exception as e:
            print(f"❌ Error: {e}")
    
    def generate_label(self):
        """Generate shipping label."""
        order_id = input("\nEnter order ID (local database ID): ").strip()
        
        try:
            order_id = int(order_id)
            db = get_db()
            order = db.query(Order).filter(Order.id == order_id).first()
            
            if not order:
                print(f"❌ Order {order_id} not found")
                db.close()
                return
            
            order_data = {
                'order_id': order.etsy_order_id,
                'buyer_name': order.buyer_name,
                'shipping_address': order.shipping_address,
                'tracking_number': order.tracking_number or 'N/A',
                'shop_name': 'Your Awesome Shop',
                'shop_address': '456 Business Blvd\nYour City, ST 12345'
            }
            
            pdf_path = self.doc_generator.generate_shipping_label(order_data)
            print(f"✅ Shipping label generated: {pdf_path}")
            
            order.label_generated = True
            db.commit()
            db.close()
        except Exception as e:
            print(f"❌ Error: {e}")
    
    def generate_all_documents(self):
        """Generate all documents."""
        order_id = input("\nEnter order ID (local database ID): ").strip()
        
        try:
            print("\n📄 Generating all documents...")
            
            # Temporarily store order_id for reuse
            original_input = input
            call_count = [0]
            
            def mock_input(prompt):
                call_count[0] += 1
                if "order ID" in prompt:
                    return order_id
                return original_input(prompt)
            
            import builtins
            builtins.input = mock_input
            
            self.generate_packing_list()
            self.generate_invoice()
            self.generate_label()
            
            builtins.input = original_input
            
            print("\n✅ All documents generated successfully!")
        except Exception as e:
            print(f"❌ Error: {e}")
    
    def open_output_folder(self):
        """Open the output folder."""
        import os
        import subprocess
        
        output_dir = "output"
        if os.path.exists(output_dir):
            subprocess.Popen(f'explorer "{os.path.abspath(output_dir)}"')
            print(f"✅ Opening {os.path.abspath(output_dir)}")
        else:
            print(f"❌ Output folder not found. Generate a document first.")
    
    def run(self):
        """Run the demo application."""
        print("\n🎉 Welcome to the Etsy Shop Management App - DEMO MODE!")
        print("📝 This demo uses sample data so you can explore the features.")
        
        while True:
            self.show_menu()
            choice = input("\nEnter your choice: ").strip()
            
            if choice == '0':
                print("\n👋 Thank you for trying the Etsy Shop Management App!")
                break
            elif choice == '1':
                self.view_inventory()
            elif choice == '2':
                self.update_inventory_quantity()
            elif choice == '3':
                self.view_low_stock()
            elif choice == '4':
                self.add_inventory_item()
            elif choice == '5':
                self.view_orders()
            elif choice == '6':
                self.view_order_details()
            elif choice == '7':
                self.mark_packed()
            elif choice == '8':
                self.generate_packing_list()
            elif choice == '9':
                self.generate_invoice()
            elif choice == '10':
                self.generate_label()
            elif choice == '11':
                self.generate_all_documents()
            elif choice == '12':
                self.open_output_folder()
            else:
                print("\n❌ Invalid choice. Please try again.")
            
            input("\nPress Enter to continue...")

def main():
    """Main entry point for demo."""
    app = EtsyAppDemo()
    app.run()

if __name__ == '__main__':
    main()
