"""Main CLI application for the Etsy management app."""
import sys
from typing import Optional
from config import Config
from database import init_db, get_db
from etsy_api import EtsyAPIClient
from inventory_manager import InventoryManager
from order_manager import OrderManager

class EtsyApp:
    """Main application class."""
    
    def __init__(self):
        """Initialize the application."""
        try:
            Config.validate()
        except ValueError as e:
            print(f"Configuration Error: {e}")
            print("Please copy .env.example to .env and fill in your Etsy API credentials.")
            sys.exit(1)
        
        # Initialize database
        init_db()
        
        # Initialize managers
        self.etsy_client = EtsyAPIClient()
        self.inventory_manager = InventoryManager()
        self.order_manager = OrderManager()
    
    def show_menu(self):
        """Display the main menu."""
        print("\n" + "="*60)
        print("           ETSY SHOP MANAGEMENT APP")
        print("="*60)
        print("\n📦 INVENTORY MANAGEMENT")
        print("  1. Sync inventory from Etsy")
        print("  2. View local inventory")
        print("  3. Update inventory quantity")
        print("  4. View low stock items")
        
        print("\n📋 ORDER MANAGEMENT")
        print("  5. Sync orders from Etsy")
        print("  6. View all orders")
        print("  7. View pending orders")
        print("  8. Mark order as packed")
        print("  9. Update tracking number")
        
        print("\n📄 DOCUMENT GENERATION")
        print("  10. Generate packing list")
        print("  11. Generate invoice")
        print("  12. Generate shipping label")
        print("  13. Generate all documents for order")
        
        print("\n🏪 LISTING MANAGEMENT")
        print("  14. View shop listings")
        print("  15. Get listing details")
        
        print("\n⚙️  OTHER")
        print("  16. View shop information")
        print("  0. Exit")
        print("="*60)
    
    def sync_inventory(self):
        """Sync inventory from Etsy."""
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
            items = self.inventory_manager.get_local_inventory()
            if not items:
                print("No items in local inventory. Sync from Etsy first.")
                return
            
            print(f"\n{'ID':<8} {'SKU':<15} {'Title':<40} {'Qty':<6} {'Price':<10}")
            print("-" * 85)
            for item in items:
                title = item['title'][:37] + '...' if len(item['title']) > 40 else item['title']
                print(f"{item['etsy_listing_id']:<8} {item['sku']:<15} {title:<40} "
                      f"{item['quantity']:<6} ${item['price']:<9.2f}" if item['price'] else "N/A")
        except Exception as e:
            print(f"❌ Error viewing inventory: {e}")
    
    def update_inventory_quantity(self):
        """Update inventory quantity."""
        listing_id = input("\nEnter listing ID: ").strip()
        quantity = input("Enter new quantity: ").strip()
        sync = input("Sync to Etsy? (y/n): ").strip().lower() == 'y'
        
        try:
            quantity = int(quantity)
            self.inventory_manager.update_local_inventory(
                listing_id, quantity, sync_to_etsy=sync
            )
            print(f"✅ Updated inventory for listing {listing_id}")
        except Exception as e:
            print(f"❌ Error updating inventory: {e}")
    
    def view_low_stock(self):
        """View low stock items."""
        threshold = input("\nEnter threshold (default 5): ").strip()
        threshold = int(threshold) if threshold else 5
        
        try:
            items = self.inventory_manager.get_low_stock_items(threshold)
            if not items:
                print(f"✅ No items with stock below {threshold}")
                return
            
            print(f"\n⚠️  Items with stock <= {threshold}:")
            print(f"\n{'ID':<10} {'SKU':<15} {'Title':<40} {'Qty':<6}")
            print("-" * 75)
            for item in items:
                title = item['title'][:37] + '...' if len(item['title']) > 40 else item['title']
                print(f"{item['etsy_listing_id']:<10} {item['sku']:<15} {title:<40} {item['quantity']:<6}")
        except Exception as e:
            print(f"❌ Error viewing low stock: {e}")
    
    def sync_orders(self):
        """Sync orders from Etsy."""
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
            orders = self.order_manager.get_orders(status)
            if not orders:
                print("No orders found.")
                return
            
            print(f"\n{'ID':<6} {'Order ID':<12} {'Customer':<25} {'Amount':<10} {'Status':<10} {'Packed':<8}")
            print("-" * 85)
            for order in orders:
                print(f"{order['id']:<6} {order['etsy_order_id']:<12} "
                      f"{order['buyer_name'][:23]:<25} ${order['total_amount']:<9.2f} "
                      f"{order['status']:<10} {'Yes' if order['packed'] else 'No':<8}")
        except Exception as e:
            print(f"❌ Error viewing orders: {e}")
    
    def mark_packed(self):
        """Mark an order as packed."""
        order_id = input("\nEnter order ID (local database ID): ").strip()
        try:
            order_id = int(order_id)
            if self.order_manager.mark_order_packed(order_id):
                print(f"✅ Order {order_id} marked as packed")
            else:
                print(f"❌ Order {order_id} not found")
        except Exception as e:
            print(f"❌ Error marking order as packed: {e}")
    
    def update_tracking(self):
        """Update tracking number for an order."""
        order_id = input("\nEnter order ID (local database ID): ").strip()
        tracking = input("Enter tracking number: ").strip()
        carrier = input("Enter carrier name (default USPS): ").strip() or "USPS"
        
        try:
            order_id = int(order_id)
            if self.order_manager.update_tracking(order_id, tracking, carrier):
                print(f"✅ Updated tracking for order {order_id}")
            else:
                print(f"❌ Order {order_id} not found")
        except Exception as e:
            print(f"❌ Error updating tracking: {e}")
    
    def generate_packing_list(self):
        """Generate a packing list."""
        order_id = input("\nEnter order ID (local database ID): ").strip()
        try:
            order_id = int(order_id)
            pdf_path = self.order_manager.generate_packing_list(order_id)
            print(f"✅ Packing list generated: {pdf_path}")
        except Exception as e:
            print(f"❌ Error generating packing list: {e}")
    
    def generate_invoice(self):
        """Generate an invoice."""
        order_id = input("\nEnter order ID (local database ID): ").strip()
        try:
            order_id = int(order_id)
            shop_info = self.etsy_client.get_shop()
            pdf_path = self.order_manager.generate_invoice(order_id, shop_info)
            print(f"✅ Invoice generated: {pdf_path}")
        except Exception as e:
            print(f"❌ Error generating invoice: {e}")
    
    def generate_label(self):
        """Generate a shipping label."""
        order_id = input("\nEnter order ID (local database ID): ").strip()
        try:
            order_id = int(order_id)
            shop_info = self.etsy_client.get_shop()
            pdf_path = self.order_manager.generate_shipping_label(order_id, shop_info)
            print(f"✅ Shipping label generated: {pdf_path}")
        except Exception as e:
            print(f"❌ Error generating shipping label: {e}")
    
    def generate_all_documents(self):
        """Generate all documents for an order."""
        order_id = input("\nEnter order ID (local database ID): ").strip()
        try:
            order_id = int(order_id)
            shop_info = self.etsy_client.get_shop()
            
            packing_list = self.order_manager.generate_packing_list(order_id)
            print(f"✅ Packing list: {packing_list}")
            
            invoice = self.order_manager.generate_invoice(order_id, shop_info)
            print(f"✅ Invoice: {invoice}")
            
            label = self.order_manager.generate_shipping_label(order_id, shop_info)
            print(f"✅ Shipping label: {label}")
            
            print("\n✅ All documents generated successfully!")
        except Exception as e:
            print(f"❌ Error generating documents: {e}")
    
    def view_listings(self):
        """View shop listings."""
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
    
    def run(self):
        """Run the main application loop."""
        print("\n🎉 Welcome to the Etsy Shop Management App!")
        
        while True:
            self.show_menu()
            choice = input("\nEnter your choice: ").strip()
            
            if choice == '0':
                print("\n👋 Thank you for using Etsy Shop Management App!")
                break
            elif choice == '1':
                self.sync_inventory()
            elif choice == '2':
                self.view_inventory()
            elif choice == '3':
                self.update_inventory_quantity()
            elif choice == '4':
                self.view_low_stock()
            elif choice == '5':
                self.sync_orders()
            elif choice == '6':
                self.view_orders()
            elif choice == '7':
                self.view_orders('pending')
            elif choice == '8':
                self.mark_packed()
            elif choice == '9':
                self.update_tracking()
            elif choice == '10':
                self.generate_packing_list()
            elif choice == '11':
                self.generate_invoice()
            elif choice == '12':
                self.generate_label()
            elif choice == '13':
                self.generate_all_documents()
            elif choice == '14':
                self.view_listings()
            elif choice == '15':
                self.get_listing_details()
            elif choice == '16':
                self.view_shop_info()
            else:
                print("\n❌ Invalid choice. Please try again.")
            
            input("\nPress Enter to continue...")

def main():
    """Main entry point."""
    app = EtsyApp()
    app.run()

if __name__ == '__main__':
    main()
