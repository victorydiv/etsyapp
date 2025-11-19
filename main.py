"""Main CLI application for the Etsy management app."""
import sys
from typing import Optional
from datetime import datetime
from config import Config
from database import init_db, get_db, LocalInventory, Order, OrderItem
from document_generator import DocumentGenerator

class EtsyApp:
    """Main application class."""
    
    def __init__(self):
        """Initialize the application."""
        # Always initialize database
        init_db()
        self.doc_generator = DocumentGenerator()
        
        # Check if Etsy API is configured
        self.etsy_enabled = Config.is_etsy_configured()
        
        if self.etsy_enabled:
            try:
                from etsy_api import EtsyAPIClient
                from inventory_manager import InventoryManager
                from order_manager import OrderManager
                
                self.etsy_client = EtsyAPIClient()
                self.inventory_manager = InventoryManager()
                self.order_manager = OrderManager()
                
                print("\n✅ Etsy API integration enabled")
            except Exception as e:
                print(f"\n⚠️  Warning: Etsy API error: {e}")
                print("Running in LOCAL-ONLY mode")
                self.etsy_enabled = False
                self.etsy_client = None
                self.inventory_manager = None
                self.order_manager = None
        else:
            print("\n⚠️  Etsy API not configured - Running in LOCAL-ONLY mode")
            print("💡 To enable Etsy integration, configure your .env file")
            print("   See README.md for instructions\n")
            self.etsy_client = None
            self.inventory_manager = None
            self.order_manager = None
    
    def show_menu(self):
        """Display the main menu."""
        print("\n" + "="*60)
        if self.etsy_enabled:
            print("           ETSY SHOP MANAGEMENT APP")
        else:
            print("     ETSY SHOP MANAGEMENT APP - LOCAL MODE")
        print("="*60)
        
        print("\n📦 INVENTORY MANAGEMENT")
        if self.etsy_enabled:
            print("  1. Sync inventory from Etsy")
        print("  2. View local inventory")
        print("  3. Update inventory quantity")
        if self.etsy_enabled:
            print("     (can sync to Etsy)")
        print("  4. View low stock items")
        print("  5. Add new inventory item")
        
        print("\n📋 ORDER MANAGEMENT")
        if self.etsy_enabled:
            print("  6. Sync orders from Etsy")
        print("  7. View all orders")
        print("  8. View pending orders")
        print("  9. Mark order as packed")
        if self.etsy_enabled:
            print("  10. Update tracking number (syncs to Etsy)")
        else:
            print("  10. Update tracking number")
        
        print("\n📄 DOCUMENT GENERATION")
        print("  11. Generate packing list")
        print("  12. Generate invoice")
        print("  13. Generate shipping label")
        print("  14. Generate all documents for order")
        
        print("\n🏪 LISTING MANAGEMENT")
        if self.etsy_enabled:
            print("  15. View shop listings")
            print("  16. Get listing details")
        
        print("\n⚙️  OTHER")
        if self.etsy_enabled:
            print("  17. View shop information")
        print("  18. Open output folder")
        print("  0. Exit")
        print("="*60)
        
        if not self.etsy_enabled:
            print("\n💡 Etsy features disabled - Configure .env to enable")
    
    def sync_inventory(self):
        """Sync inventory from Etsy."""
        if not self.etsy_enabled:
            print("\n❌ Etsy integration not available")
            print("💡 Configure your .env file to enable Etsy sync")
            return
            
        print("\n🔄 Syncing inventory from Etsy...")
        try:
            count = self.inventory_manager.sync_from_etsy()
            print(f"✅ Successfully synced {count} items from Etsy")
        except Exception as e:
            print(f"❌ Error syncing inventory: {e}")
    
    def view_inventory(self):
        """View local inventory."""
        print("\n📦 Local Inventory:")
        try:
            db = get_db()
            items = db.query(LocalInventory).all()
            
            if not items:
                print("No items in local inventory.")
                if self.etsy_enabled:
                    print("💡 Use option 1 to sync from Etsy")
                else:
                    print("💡 Use option 5 to add items manually")
                db.close()
                return
            
            print(f"\n{'ID':<8} {'SKU':<15} {'Title':<40} {'Qty':<6} {'Price':<10}")
            print("-" * 85)
            for item in items:
                title = item.title[:37] + '...' if len(item.title) > 40 else item.title
                print(f"{item.etsy_listing_id:<8} {item.sku:<15} {title:<40} "
                      f"{item.quantity:<6} ${item.price:<9.2f}" if item.price else "N/A")
            db.close()
        except Exception as e:
            print(f"❌ Error viewing inventory: {e}")
    
    def update_inventory_quantity(self):
        """Update inventory quantity."""
        listing_id = input("\nEnter listing ID: ").strip()
        quantity = input("Enter new quantity: ").strip()
        
        sync = False
        if self.etsy_enabled:
            sync = input("Sync to Etsy? (y/n): ").strip().lower() == 'y'
        
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
            
            if sync and self.etsy_enabled:
                try:
                    self.inventory_manager.sync_to_etsy(listing_id, quantity)
                    print("✅ Synced to Etsy")
                except Exception as e:
                    print(f"⚠️  Local update successful, but Etsy sync failed: {e}")
        except Exception as e:
            print(f"❌ Error updating inventory: {e}")
    
    def view_low_stock(self):
        """View low stock items."""
        threshold = input("\nEnter threshold (default 5): ").strip()
        threshold = int(threshold) if threshold else 5
        
        try:
            db = get_db()
            items = db.query(LocalInventory).filter(
                LocalInventory.quantity <= threshold
            ).all()
            
            if not items:
                print(f"✅ No items with stock below {threshold}")
                db.close()
                return
            
            print(f"\n⚠️  Items with stock <= {threshold}:")
            print(f"\n{'ID':<10} {'SKU':<15} {'Title':<40} {'Qty':<6}")
            print("-" * 75)
            for item in items:
                title = item.title[:37] + '...' if len(item.title) > 40 else item.title
                print(f"{item.etsy_listing_id:<10} {item.sku:<15} {title:<40} {item.quantity:<6}")
            db.close()
        except Exception as e:
            print(f"❌ Error viewing low stock: {e}")
    
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
    
    def sync_orders(self):
        """Sync orders from Etsy."""
        if not self.etsy_enabled:
            print("\n❌ Etsy integration not available")
            print("💡 Configure your .env file to enable Etsy sync")
            return
            
        print("\n🔄 Syncing orders from Etsy...")
        try:
            count = self.order_manager.sync_orders_from_etsy()
            print(f"✅ Successfully synced {count} orders from Etsy")
        except Exception as e:
            print(f"❌ Error syncing orders: {e}")
    
    def view_orders(self, status: Optional[str] = None):
        """View orders."""
        status_text = f" ({status})" if status else ""
        print(f"\n📋 Orders{status_text}:")
        try:
            db = get_db()
            query = db.query(Order)
            if status:
                query = query.filter(Order.status == status)
            
            orders = query.all()
            if not orders:
                print("No orders found.")
                if not self.etsy_enabled:
                    print("💡 Orders can be manually added in the database")
                db.close()
                return
            
            print(f"\n{'ID':<6} {'Order ID':<12} {'Customer':<25} {'Amount':<10} {'Status':<10} {'Packed':<8}")
            print("-" * 85)
            for order in orders:
                print(f"{order.id:<6} {order.etsy_order_id:<12} "
                      f"{order.buyer_name[:23]:<25} ${order.total_amount:<9.2f} "
                      f"{order.status:<10} {'Yes' if order.packed else 'No':<8}")
            db.close()
        except Exception as e:
            print(f"❌ Error viewing orders: {e}")
    
    def mark_packed(self):
        """Mark an order as packed."""
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
            
            print(f"✅ Order {order_id} marked as packed")
        except Exception as e:
            print(f"❌ Error marking order as packed: {e}")
    
    def update_tracking(self):
        """Update tracking number for an order."""
        order_id = input("\nEnter order ID (local database ID): ").strip()
        tracking = input("Enter tracking number: ").strip()
        carrier = input("Enter carrier name (default USPS): ").strip() or "USPS"
        
        try:
            order_id = int(order_id)
            db = get_db()
            order = db.query(Order).filter(Order.id == order_id).first()
            
            if not order:
                print(f"❌ Order {order_id} not found")
                db.close()
                return
            
            # Update local record
            order.tracking_number = tracking
            order.status = 'shipped'
            db.commit()
            db.close()
            
            print(f"✅ Updated tracking for order {order_id}")
            
            # Update Etsy if enabled
            if self.etsy_enabled and self.order_manager:
                try:
                    self.etsy_client.update_receipt_tracking(
                        order.etsy_order_id, 
                        tracking, 
                        carrier
                    )
                    print("✅ Synced to Etsy")
                except Exception as e:
                    print(f"⚠️  Local update successful, but Etsy sync failed: {e}")
        except Exception as e:
            print(f"❌ Error updating tracking: {e}")
    
    def generate_packing_list(self):
        """Generate a packing list."""
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
            items_data = []
            for item in items:
                # Try to get location from inventory
                inv_item = db.query(LocalInventory).filter(
                    LocalInventory.sku == item.sku
                ).first()
                location = inv_item.location if inv_item and inv_item.location else 'N/A'
                
                items_data.append({
                    'sku': item.sku,
                    'title': item.title,
                    'quantity': item.quantity,
                    'location': location
                })
            
            order_data = {
                'order_id': order.etsy_order_id,
                'order_date': order.order_date.strftime('%Y-%m-%d') if order.order_date else 'N/A',
                'buyer_name': order.buyer_name,
                'shipping_address': order.shipping_address
            }
            
            pdf_path = self.doc_generator.generate_packing_list(order_data, items_data)
            print(f"✅ Packing list generated: {pdf_path}")
            db.close()
        except Exception as e:
            print(f"❌ Error generating packing list: {e}")
    
    def generate_invoice(self):
        """Generate an invoice."""
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
                'order_date': order.order_date.strftime('%Y-%m-%d') if order.order_date else 'N/A',
                'buyer_name': order.buyer_name,
                'buyer_email': order.buyer_email,
                'total_amount': order.total_amount,
                'status': order.status
            }
            
            # Get shop info if Etsy is enabled, otherwise use default
            shop_info = None
            if self.etsy_enabled and self.etsy_client:
                try:
                    shop_info = self.etsy_client.get_shop()
                except:
                    pass
            
            if not shop_info:
                shop_info = {
                    'shop_name': Config.ETSY_SHOP_ID or 'Your Shop',
                    'address': 'Your Business Address Here'
                }
            
            pdf_path = self.doc_generator.generate_invoice(order_data, items_data, shop_info)
            print(f"✅ Invoice generated: {pdf_path}")
            
            order.invoice_generated = True
            db.commit()
            db.close()
        except Exception as e:
            print(f"❌ Error generating invoice: {e}")
    
    def generate_label(self):
        """Generate a shipping label."""
        order_id = input("\nEnter order ID (local database ID): ").strip()
        try:
            order_id = int(order_id)
            db = get_db()
            order = db.query(Order).filter(Order.id == order_id).first()
            
            if not order:
                print(f"❌ Order {order_id} not found")
                db.close()
                return
            
            # Get shop info if Etsy is enabled
            shop_name = Config.ETSY_SHOP_ID or 'Your Shop'
            shop_address = 'Your Business Address Here'
            
            if self.etsy_enabled and self.etsy_client:
                try:
                    shop = self.etsy_client.get_shop()
                    shop_name = shop.get('shop_name', shop_name)
                except:
                    pass
            
            order_data = {
                'order_id': order.etsy_order_id,
                'buyer_name': order.buyer_name,
                'shipping_address': order.shipping_address,
                'tracking_number': order.tracking_number,
                'shop_name': shop_name,
                'shop_address': shop_address
            }
            
            pdf_path = self.doc_generator.generate_shipping_label(order_data)
            print(f"✅ Shipping label generated: {pdf_path}")
            
            order.label_generated = True
            db.commit()
            db.close()
        except Exception as e:
            print(f"❌ Error generating shipping label: {e}")
    
    def generate_all_documents(self):
        """Generate all documents for an order."""
        order_id = input("\nEnter order ID (local database ID): ").strip()
        try:
            order_id_int = int(order_id)
            
            print("\n📄 Generating all documents...")
            
            # Store the order ID to reuse
            original_input = input
            def mock_input(prompt):
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
            print(f"❌ Error generating documents: {e}")
    
    def view_listings(self):
        """View shop listings."""
        if not self.etsy_enabled:
            print("\n❌ Etsy integration not available")
            return
            
        print("\n🏪 Shop Listings:")
        try:
            listings = self.etsy_client.get_shop_listings()
            if not listings:
                print("No active listings found.")
                return
            
            print(f"\n{'Listing ID':<12} {'Title':<50} {'Price':<10} {'Quantity':<10}")
            print("-" * 85)
            for listing in listings:
                title = listing['title'][:47] + '...' if len(listing['title']) > 50 else listing['title']
                price = listing.get('price', {})
                price_str = f"${float(price.get('amount', 0)) / float(price.get('divisor', 100)):.2f}"
                print(f"{listing['listing_id']:<12} {title:<50} {price_str:<10} {listing.get('quantity', 'N/A'):<10}")
        except Exception as e:
            print(f"❌ Error viewing listings: {e}")
    
    def get_listing_details(self):
        """Get details for a specific listing."""
        if not self.etsy_enabled:
            print("\n❌ Etsy integration not available")
            return
            
        listing_id = input("\nEnter listing ID: ").strip()
        try:
            listing = self.etsy_client.get_listing(listing_id)
            print("\n📄 Listing Details:")
            print(f"Title: {listing.get('title')}")
            print(f"Description: {listing.get('description', 'N/A')[:200]}...")
            print(f"Price: ${float(listing.get('price', {}).get('amount', 0)) / 100:.2f}")
            print(f"Quantity: {listing.get('quantity')}")
            print(f"SKU: {listing.get('sku', 'N/A')}")
            print(f"State: {listing.get('state')}")
        except Exception as e:
            print(f"❌ Error getting listing details: {e}")
    
    def view_shop_info(self):
        """View shop information."""
        if not self.etsy_enabled:
            print("\n❌ Etsy integration not available")
            return
            
        print("\n🏪 Shop Information:")
        try:
            shop = self.etsy_client.get_shop()
            print(f"Shop Name: {shop.get('shop_name')}")
            print(f"Shop ID: {shop.get('shop_id')}")
            print(f"Title: {shop.get('title', 'N/A')}")
            print(f"Currency: {shop.get('currency_code', 'N/A')}")
            print(f"Is Vacation: {shop.get('is_vacation', False)}")
        except Exception as e:
            print(f"❌ Error getting shop info: {e}")
    
    def open_output_folder(self):
        """Open the output folder."""
        import os
        import subprocess
        
        output_dir = Config.PDF_OUTPUT_DIR
        if output_dir.exists():
            if os.name == 'nt':  # Windows
                os.startfile(str(output_dir))
            else:  # Mac/Linux
                subprocess.Popen(['open' if sys.platform == 'darwin' else 'xdg-open', str(output_dir)])
            print(f"✅ Opening {output_dir}")
        else:
            print(f"❌ Output folder not found. Generate a document first.")
    
    def run(self):
        """Run the main application loop."""
        print("\n🎉 Welcome to the Etsy Shop Management App!")
        
        while True:
            self.show_menu()
            choice = input("\nEnter your choice: ").strip()
            
            if choice == '0':
                print("\n👋 Thank you for using Etsy Shop Management App!")
                break
            elif choice == '1' and self.etsy_enabled:
                self.sync_inventory()
            elif choice == '2':
                self.view_inventory()
            elif choice == '3':
                self.update_inventory_quantity()
            elif choice == '4':
                self.view_low_stock()
            elif choice == '5':
                self.add_inventory_item()
            elif choice == '6' and self.etsy_enabled:
                self.sync_orders()
            elif choice == '7':
                self.view_orders()
            elif choice == '8':
                self.view_orders('pending')
            elif choice == '9':
                self.mark_packed()
            elif choice == '10':
                self.update_tracking()
            elif choice == '11':
                self.generate_packing_list()
            elif choice == '12':
                self.generate_invoice()
            elif choice == '13':
                self.generate_label()
            elif choice == '14':
                self.generate_all_documents()
            elif choice == '15' and self.etsy_enabled:
                self.view_listings()
            elif choice == '16' and self.etsy_enabled:
                self.get_listing_details()
            elif choice == '17' and self.etsy_enabled:
                self.view_shop_info()
            elif choice == '18':
                self.open_output_folder()
            else:
                if not self.etsy_enabled and choice in ['1', '6', '15', '16', '17']:
                    print("\n❌ This feature requires Etsy integration")
                    print("💡 Configure your .env file to enable")
                else:
                    print("\n❌ Invalid choice. Please try again.")
            
            input("\nPress Enter to continue...")

def main():
    """Main entry point."""
    app = EtsyApp()
    app.run()

if __name__ == '__main__':
    main()
