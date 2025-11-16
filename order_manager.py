"""Order management module for tracking and processing orders."""
from datetime import datetime
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from database import Order, OrderItem, get_db
from etsy_api import EtsyAPIClient
from document_generator import DocumentGenerator

class OrderManager:
    """Manage orders and related operations."""
    
    def __init__(self):
        """Initialize the order manager."""
        self.etsy_client = EtsyAPIClient()
        self.doc_generator = DocumentGenerator()
    
    def sync_orders_from_etsy(self, limit: int = 100, db: Session = None) -> int:
        """Sync orders from Etsy to local database."""
        if db is None:
            db = get_db()
        
        try:
            receipts = self.etsy_client.get_shop_receipts(limit=limit)
            count = 0
            
            for receipt in receipts:
                receipt_id = str(receipt.get('receipt_id'))
                
                # Check if order already exists
                existing_order = db.query(Order).filter(
                    Order.etsy_order_id == receipt_id
                ).first()
                
                if not existing_order:
                    order = Order()
                    order.etsy_order_id = receipt_id
                    db.add(order)
                else:
                    order = existing_order
                
                # Update order fields
                order.buyer_name = receipt.get('name', '')
                order.buyer_email = receipt.get('buyer_email', '')
                
                # Format shipping address
                ship_addr = receipt.get('formatted_address', '')
                order.shipping_address = ship_addr
                
                order.total_amount = float(receipt.get('grandtotal', {}).get('amount', 0)) / 100
                order.order_date = datetime.fromtimestamp(receipt.get('create_timestamp', 0))
                
                # Map Etsy status to our status
                etsy_status = receipt.get('status', 'unknown')
                if etsy_status in ['paid', 'completed']:
                    order.status = 'pending'
                elif etsy_status == 'shipped':
                    order.status = 'shipped'
                else:
                    order.status = etsy_status
                
                db.commit()
                
                # Sync order items
                transactions = self.etsy_client.get_receipt_transactions(receipt_id)
                for transaction in transactions:
                    existing_item = db.query(OrderItem).filter(
                        OrderItem.order_id == order.id,
                        OrderItem.etsy_listing_id == str(transaction.get('listing_id'))
                    ).first()
                    
                    if not existing_item:
                        item = OrderItem()
                        item.order_id = order.id
                        db.add(item)
                    else:
                        item = existing_item
                    
                    item.etsy_listing_id = str(transaction.get('listing_id'))
                    item.sku = transaction.get('sku', '')
                    item.title = transaction.get('title', '')
                    item.quantity = transaction.get('quantity', 0)
                    item.price = float(transaction.get('price', {}).get('amount', 0)) / 100
                
                db.commit()
                count += 1
            
            return count
        finally:
            if db:
                db.close()
    
    def get_orders(self, status: Optional[str] = None, db: Session = None) -> List[Dict]:
        """Get orders, optionally filtered by status."""
        if db is None:
            db = get_db()
        
        try:
            query = db.query(Order)
            if status:
                query = query.filter(Order.status == status)
            
            orders = query.all()
            return [{
                'id': order.id,
                'etsy_order_id': order.etsy_order_id,
                'buyer_name': order.buyer_name,
                'buyer_email': order.buyer_email,
                'shipping_address': order.shipping_address,
                'total_amount': order.total_amount,
                'order_date': order.order_date.isoformat() if order.order_date else None,
                'status': order.status,
                'tracking_number': order.tracking_number,
                'packed': order.packed,
                'invoice_generated': order.invoice_generated,
                'label_generated': order.label_generated
            } for order in orders]
        finally:
            if db:
                db.close()
    
    def get_order_items(self, order_id: int, db: Session = None) -> List[Dict]:
        """Get items for a specific order."""
        if db is None:
            db = get_db()
        
        try:
            items = db.query(OrderItem).filter(OrderItem.order_id == order_id).all()
            return [{
                'etsy_listing_id': item.etsy_listing_id,
                'sku': item.sku,
                'title': item.title,
                'quantity': item.quantity,
                'price': item.price
            } for item in items]
        finally:
            if db:
                db.close()
    
    def mark_order_packed(self, order_id: int, db: Session = None) -> bool:
        """Mark an order as packed."""
        if db is None:
            db = get_db()
        
        try:
            order = db.query(Order).filter(Order.id == order_id).first()
            if not order:
                return False
            
            order.packed = True
            order.status = 'packed'
            db.commit()
            return True
        finally:
            if db:
                db.close()
    
    def update_tracking(self, order_id: int, tracking_number: str, 
                       carrier: str = 'USPS', db: Session = None) -> bool:
        """Update tracking information for an order."""
        if db is None:
            db = get_db()
        
        try:
            order = db.query(Order).filter(Order.id == order_id).first()
            if not order:
                return False
            
            # Update local record
            order.tracking_number = tracking_number
            order.status = 'shipped'
            db.commit()
            
            # Update Etsy
            try:
                self.etsy_client.update_receipt_tracking(
                    order.etsy_order_id, 
                    tracking_number, 
                    carrier
                )
            except Exception as e:
                print(f"Warning: Failed to update Etsy tracking: {e}")
            
            return True
        finally:
            if db:
                db.close()
    
    def generate_packing_list(self, order_id: int, db: Session = None) -> str:
        """Generate a packing list for an order."""
        if db is None:
            db = get_db()
        
        try:
            order = db.query(Order).filter(Order.id == order_id).first()
            if not order:
                raise ValueError(f"Order {order_id} not found")
            
            items = self.get_order_items(order_id, db)
            
            order_data = {
                'order_id': order.etsy_order_id,
                'order_date': order.order_date.strftime('%Y-%m-%d') if order.order_date else 'N/A',
                'buyer_name': order.buyer_name,
                'shipping_address': order.shipping_address
            }
            
            pdf_path = self.doc_generator.generate_packing_list(order_data, items)
            return pdf_path
        finally:
            if db:
                db.close()
    
    def generate_invoice(self, order_id: int, shop_info: Dict = None, db: Session = None) -> str:
        """Generate an invoice for an order."""
        if db is None:
            db = get_db()
        
        try:
            order = db.query(Order).filter(Order.id == order_id).first()
            if not order:
                raise ValueError(f"Order {order_id} not found")
            
            items = self.get_order_items(order_id, db)
            
            order_data = {
                'order_id': order.etsy_order_id,
                'order_date': order.order_date.strftime('%Y-%m-%d') if order.order_date else 'N/A',
                'buyer_name': order.buyer_name,
                'buyer_email': order.buyer_email,
                'total_amount': order.total_amount,
                'status': order.status
            }
            
            pdf_path = self.doc_generator.generate_invoice(order_data, items, shop_info)
            
            # Mark invoice as generated
            order.invoice_generated = True
            db.commit()
            
            return pdf_path
        finally:
            if db:
                db.close()
    
    def generate_shipping_label(self, order_id: int, shop_info: Dict = None, db: Session = None) -> str:
        """Generate a shipping label for an order."""
        if db is None:
            db = get_db()
        
        try:
            order = db.query(Order).filter(Order.id == order_id).first()
            if not order:
                raise ValueError(f"Order {order_id} not found")
            
            order_data = {
                'order_id': order.etsy_order_id,
                'buyer_name': order.buyer_name,
                'shipping_address': order.shipping_address,
                'tracking_number': order.tracking_number,
                'shop_name': shop_info.get('shop_name', '') if shop_info else '',
                'shop_address': shop_info.get('address', '') if shop_info else ''
            }
            
            pdf_path = self.doc_generator.generate_shipping_label(order_data)
            
            # Mark label as generated
            order.label_generated = True
            db.commit()
            
            return pdf_path
        finally:
            if db:
                db.close()
