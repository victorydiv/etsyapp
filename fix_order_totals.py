"""Fix order totals for all inbound orders."""
from database import get_db, InboundOrder, InboundOrderItem

def fix_all_order_totals():
    """Recalculate and fix totals for all inbound orders."""
    db = get_db()
    
    try:
        orders = db.query(InboundOrder).all()
        
        for order in orders:
            # Get all items for this order
            items = db.query(InboundOrderItem).filter(
                InboundOrderItem.inbound_order_id == order.id
            ).all()
            
            # Calculate subtotal from items
            subtotal = sum(item.quantity_ordered * (item.unit_cost or 0) for item in items)
            
            # Calculate total (subtotal + shipping + tax)
            total_cost = subtotal + (order.shipping_cost or 0) + (order.tax or 0)
            
            # Update order
            old_subtotal = order.subtotal
            old_total = order.total_cost
            order.subtotal = subtotal
            order.total_cost = total_cost
            
            print(f"PO {order.po_number}:")
            print(f"  Subtotal: ${old_subtotal:.2f} -> ${subtotal:.2f}")
            print(f"  Total:    ${old_total:.2f} -> ${total_cost:.2f}")
            print(f"  (Shipping: ${order.shipping_cost or 0:.2f}, Tax: ${order.tax or 0:.2f})")
            print()
        
        db.commit()
        print(f"Fixed totals for {len(orders)} orders.")
        
    except Exception as e:
        db.rollback()
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    fix_all_order_totals()
