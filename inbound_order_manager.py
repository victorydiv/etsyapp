"""Inbound Order (Purchase Order) management."""
from sqlalchemy.orm import Session
from database import (
    InboundOrder, InboundOrderItem, ItemMaster, 
    Inventory, InventoryTransaction, SessionLocal
)
from datetime import datetime
from typing import List, Dict, Optional

class InboundOrderManager:
    """Manages purchase orders and receiving inventory."""
    
    def __init__(self, db_session: Session = None):
        self.db = db_session or SessionLocal()
    
    def create_inbound_order(self, 
                            supplier_name: str,
                            order_date: datetime = None,
                            items: List[Dict] = None,
                            **kwargs) -> InboundOrder:
        """
        Create a new inbound order (purchase order).
        
        Args:
            supplier_name: Name of supplier
            order_date: Date order was placed
            items: List of dicts with 'sku', 'quantity', and optionally 'unit_cost'
            **kwargs: Additional InboundOrder fields
        """
        # Generate PO number if not provided
        if 'po_number' not in kwargs:
            kwargs['po_number'] = self._generate_po_number()
        
        order = InboundOrder(
            supplier_name=supplier_name,
            order_date=order_date or datetime.utcnow(),
            **kwargs
        )
        self.db.add(order)
        self.db.flush()  # Get the order ID
        
        # Add line items
        total = 0.0
        if items:
            for item_data in items:
                item_master = self.db.query(ItemMaster).filter(
                    ItemMaster.sku == item_data['sku']
                ).first()
                
                if not item_master:
                    raise ValueError(f"Item with SKU {item_data['sku']} not found")
                
                unit_cost = item_data.get('unit_cost', item_master.base_cost or 0)
                quantity = item_data['quantity']
                
                order_item = InboundOrderItem(
                    inbound_order_id=order.id,
                    item_id=item_master.id,
                    quantity_ordered=quantity,
                    unit_cost=unit_cost
                )
                self.db.add(order_item)
                total += unit_cost * quantity
        
        # Update order totals
        order.subtotal = total
        order.total_cost = total + (order.shipping_cost or 0) + (order.tax or 0)
        
        self.db.commit()
        self.db.refresh(order)
        return order
    
    def _generate_po_number(self) -> str:
        """Generate next PO number."""
        last_order = self.db.query(InboundOrder).order_by(
            InboundOrder.id.desc()
        ).first()
        
        if last_order and last_order.po_number.startswith('PO'):
            try:
                last_num = int(last_order.po_number[2:])
                return f"PO{last_num + 1:06d}"
            except:
                pass
        
        return f"PO{1:06d}"
    
    def update_inbound_order(self, order_id: int, **kwargs) -> InboundOrder:
        """Update an inbound order."""
        order = self.db.query(InboundOrder).filter(
            InboundOrder.id == order_id
        ).first()
        
        if not order:
            raise ValueError(f"Order {order_id} not found")
        
        for key, value in kwargs.items():
            if hasattr(order, key):
                setattr(order, key, value)
        
        order.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(order)
        return order
    
    def add_order_item(self, order_id: int, sku: str, quantity: int, unit_cost: float = None):
        """Add a line item to an existing order."""
        order = self.db.query(InboundOrder).filter(
            InboundOrder.id == order_id
        ).first()
        
        if not order:
            raise ValueError(f"Order {order_id} not found")
        
        if order.status == 'received':
            raise ValueError("Cannot add items to a received order")
        
        item_master = self.db.query(ItemMaster).filter(
            ItemMaster.sku == sku
        ).first()
        
        if not item_master:
            raise ValueError(f"Item with SKU {sku} not found")
        
        unit_cost = unit_cost or item_master.base_cost or 0
        
        order_item = InboundOrderItem(
            inbound_order_id=order_id,
            item_id=item_master.id,
            quantity_ordered=quantity,
            unit_cost=unit_cost
        )
        self.db.add(order_item)
        
        # Recalculate totals
        self._recalculate_order_totals(order_id)
        
        self.db.commit()
    
    def remove_order_item(self, order_id: int, item_id: int):
        """Remove a line item from an order."""
        order = self.db.query(InboundOrder).filter(
            InboundOrder.id == order_id
        ).first()
        
        if not order:
            raise ValueError(f"Order {order_id} not found")
        
        if order.status == 'received':
            raise ValueError("Cannot remove items from a received order")
        
        # Find and delete the order item
        order_item = self.db.query(InboundOrderItem).filter(
            InboundOrderItem.inbound_order_id == order_id,
            InboundOrderItem.item_id == item_id
        ).first()
        
        if order_item:
            self.db.delete(order_item)
            self._recalculate_order_totals(order_id)
            self.db.commit()
    
    def update_order_items(self, order_id: int, items: List[Dict]):
        """Update all line items for an order (replaces existing items).
        
        Args:
            order_id: The order ID
            items: List of dicts with 'sku', 'quantity', and 'unit_cost'
        """
        order = self.db.query(InboundOrder).filter(
            InboundOrder.id == order_id
        ).first()
        
        if not order:
            raise ValueError(f"Order {order_id} not found")
        
        if order.status == 'received':
            raise ValueError("Cannot modify items on a received order")
        
        # Delete existing items
        self.db.query(InboundOrderItem).filter(
            InboundOrderItem.inbound_order_id == order_id
        ).delete()
        
        # Add new items
        for item_data in items:
            item_master = self.db.query(ItemMaster).filter(
                ItemMaster.sku == item_data['sku']
            ).first()
            
            if not item_master:
                raise ValueError(f"Item with SKU {item_data['sku']} not found")
            
            order_item = InboundOrderItem(
                inbound_order_id=order_id,
                item_id=item_master.id,
                quantity_ordered=item_data['quantity'],
                unit_cost=item_data.get('unit_cost', item_master.base_cost or 0)
            )
            self.db.add(order_item)
        
        # Flush to make sure items are in the session before recalculating
        self.db.flush()
        
        # Recalculate totals
        self._recalculate_order_totals(order_id)
        self.db.commit()
    
    def _recalculate_order_totals(self, order_id: int):
        """Recalculate order totals based on line items."""
        # Refresh order from database to get latest shipping/tax values
        order = self.db.query(InboundOrder).filter(
            InboundOrder.id == order_id
        ).first()
        
        self.db.refresh(order)
        
        items = self.db.query(InboundOrderItem).filter(
            InboundOrderItem.inbound_order_id == order_id
        ).all()
        
        subtotal = sum(item.quantity_ordered * (item.unit_cost or 0) for item in items)
        order.subtotal = subtotal
        order.total_cost = subtotal + (order.shipping_cost or 0) + (order.tax or 0)
    
    def receive_order(self, order_id: int, 
                     received_items: Dict[int, int] = None,
                     received_date: datetime = None,
                     notes: str = None) -> InboundOrder:
        """
        Receive an inbound order into inventory.
        
        Args:
            order_id: Order to receive
            received_items: Dict of {item_id: quantity_received}. If None, receive all as ordered.
            received_date: Date received. Defaults to now.
            notes: Receiving notes
        """
        order = self.db.query(InboundOrder).filter(
            InboundOrder.id == order_id
        ).first()
        
        if not order:
            raise ValueError(f"Order {order_id} not found")
        
        if order.status == 'received':
            raise ValueError("Order already received")
        
        order_items = self.db.query(InboundOrderItem).filter(
            InboundOrderItem.inbound_order_id == order_id
        ).all()
        
        # Process each line item
        for order_item in order_items:
            # Determine quantity to receive
            if received_items and order_item.item_id in received_items:
                qty_received = received_items[order_item.item_id]
            else:
                qty_received = order_item.quantity_ordered
            
            if qty_received > 0:
                # Update order item
                order_item.quantity_received += qty_received
                
                # Update inventory
                inventory = self.db.query(Inventory).filter(
                    Inventory.item_id == order_item.item_id
                ).first()
                
                if inventory:
                    inventory.quantity_on_hand += qty_received
                    inventory.quantity_available = inventory.quantity_on_hand - inventory.quantity_reserved
                    inventory.last_updated = datetime.utcnow()
                
                # Log transaction
                transaction = InventoryTransaction(
                    item_id=order_item.item_id,
                    transaction_type='inbound',
                    quantity=qty_received,
                    reference_type='inbound_order',
                    reference_id=order_id,
                    notes=f"Received from PO {order.po_number}. {notes or ''}".strip()
                )
                self.db.add(transaction)
        
        # Check if all items fully received
        all_received = all(
            item.quantity_received >= item.quantity_ordered 
            for item in order_items
        )
        
        if all_received:
            order.status = 'received'
            order.received_date = received_date or datetime.utcnow()
        
        order.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(order)
        return order
    
    def get_inbound_order(self, order_id: int) -> Optional[InboundOrder]:
        """Get an inbound order by ID."""
        return self.db.query(InboundOrder).filter(
            InboundOrder.id == order_id
        ).first()
    
    def get_inbound_order_by_po(self, po_number: str) -> Optional[InboundOrder]:
        """Get an inbound order by PO number."""
        return self.db.query(InboundOrder).filter(
            InboundOrder.po_number == po_number
        ).first()
    
    def list_inbound_orders(self, status: str = None) -> List[InboundOrder]:
        """List inbound orders, optionally filtered by status."""
        query = self.db.query(InboundOrder)
        
        if status:
            query = query.filter(InboundOrder.status == status)
        
        return query.order_by(InboundOrder.order_date.desc()).all()
    
    def get_order_items(self, order_id: int) -> List[Dict]:
        """Get line items for an inbound order with item details."""
        items = self.db.query(InboundOrderItem, ItemMaster).join(
            ItemMaster, InboundOrderItem.item_id == ItemMaster.id
        ).filter(
            InboundOrderItem.inbound_order_id == order_id
        ).all()
        
        result = []
        for order_item, item_master in items:
            result.append({
                'order_item_id': order_item.id,
                'item_id': item_master.id,
                'sku': item_master.sku,
                'title': item_master.title,
                'quantity_ordered': order_item.quantity_ordered,
                'quantity_received': order_item.quantity_received,
                'quantity_remaining': order_item.quantity_ordered - order_item.quantity_received,
                'unit_cost': order_item.unit_cost,
                'extended_cost': order_item.quantity_ordered * (order_item.unit_cost or 0)
            })
        
        return result
    
    def cancel_order(self, order_id: int, notes: str = None):
        """Cancel an inbound order."""
        order = self.db.query(InboundOrder).filter(
            InboundOrder.id == order_id
        ).first()
        
        if not order:
            raise ValueError(f"Order {order_id} not found")
        
        if order.status == 'received':
            raise ValueError("Cannot cancel a received order")
        
        order.status = 'cancelled'
        if notes:
            order.notes = f"{order.notes or ''}\nCancelled: {notes}".strip()
        order.updated_at = datetime.utcnow()
        
        self.db.commit()
    
    def get_pending_orders(self) -> List[InboundOrder]:
        """Get orders that are not yet fully received."""
        return self.db.query(InboundOrder).filter(
            InboundOrder.status.in_(['ordered', 'in_transit'])
        ).order_by(InboundOrder.expected_date).all()
    
    def close(self):
        """Close database session."""
        self.db.close()
