"""Item Master and Bill of Materials management."""
from sqlalchemy.orm import Session
from database import (
    ItemMaster, BillOfMaterials, Inventory, 
    InventoryTransaction, SessionLocal
)
from datetime import datetime
from typing import List, Dict, Optional

class ItemMasterManager:
    """Manages item master records and bill of materials."""
    
    def __init__(self, db_session: Session = None):
        self.db = db_session or SessionLocal()
    
    def create_item(self, **kwargs) -> ItemMaster:
        """Create a new item master record."""
        item = ItemMaster(**kwargs)
        self.db.add(item)
        self.db.commit()
        self.db.refresh(item)
        
        # Initialize inventory record
        inventory = Inventory(item_id=item.id)
        self.db.add(inventory)
        self.db.commit()
        
        return item
    
    def update_item(self, item_id: int, **kwargs) -> ItemMaster:
        """Update an item master record."""
        item = self.db.query(ItemMaster).filter(ItemMaster.id == item_id).first()
        if not item:
            raise ValueError(f"Item {item_id} not found")
        
        for key, value in kwargs.items():
            if hasattr(item, key):
                setattr(item, key, value)
        
        item.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(item)
        return item
    
    def get_item_by_sku(self, sku: str) -> Optional[ItemMaster]:
        """Get item by SKU."""
        return self.db.query(ItemMaster).filter(ItemMaster.sku == sku).first()
    
    def get_item_by_id(self, item_id: int) -> Optional[ItemMaster]:
        """Get item by ID."""
        return self.db.query(ItemMaster).filter(ItemMaster.id == item_id).first()
    
    def list_items(self, category: str = None, active_only: bool = True) -> List[ItemMaster]:
        """List all items, optionally filtered by category."""
        query = self.db.query(ItemMaster)
        
        if active_only:
            query = query.filter(ItemMaster.is_active == True)
        
        if category:
            query = query.filter(ItemMaster.category == category)
        
        return query.order_by(ItemMaster.sku).all()
    
    def create_kit(self, kit_sku: str, kit_title: str, components: List[Dict], **kwargs) -> ItemMaster:
        """
        Create a kit/assembly item with bill of materials.
        
        Args:
            kit_sku: SKU for the new kit
            kit_title: Title/name of the kit
            components: List of dicts with 'sku' and 'quantity' keys
            **kwargs: Additional ItemMaster fields
        """
        # Create the kit item
        kit_item = self.create_item(
            sku=kit_sku,
            title=kit_title,
            category='kit',
            is_kit=True,
            **kwargs
        )
        
        # Add BOM components
        total_cost = 0.0
        for comp in components:
            component_item = self.get_item_by_sku(comp['sku'])
            if not component_item:
                raise ValueError(f"Component SKU {comp['sku']} not found")
            
            bom = BillOfMaterials(
                parent_item_id=kit_item.id,
                component_item_id=component_item.id,
                quantity_required=comp['quantity']
            )
            self.db.add(bom)
            
            # Calculate cost
            component_cost = component_item.base_cost or component_item.calculated_cost or 0
            total_cost += component_cost * comp['quantity']
        
        # Update kit with calculated cost
        kit_item.calculated_cost = total_cost
        self.db.commit()
        self.db.refresh(kit_item)
        
        return kit_item
    
    def update_kit_bom(self, kit_id: int, components: List[Dict]):
        """Update the bill of materials for a kit."""
        # Remove existing BOM entries
        self.db.query(BillOfMaterials).filter(
            BillOfMaterials.parent_item_id == kit_id
        ).delete()
        
        # Add new components
        kit_item = self.get_item_by_id(kit_id)
        total_cost = 0.0
        
        for comp in components:
            component_item = self.get_item_by_sku(comp['sku'])
            if not component_item:
                raise ValueError(f"Component SKU {comp['sku']} not found")
            
            bom = BillOfMaterials(
                parent_item_id=kit_id,
                component_item_id=component_item.id,
                quantity_required=comp['quantity']
            )
            self.db.add(bom)
            
            component_cost = component_item.base_cost or component_item.calculated_cost or 0
            total_cost += component_cost * comp['quantity']
        
        # Update calculated cost
        kit_item.calculated_cost = total_cost
        kit_item.updated_at = datetime.utcnow()
        self.db.commit()
    
    def get_kit_bom(self, kit_id: int) -> List[Dict]:
        """Get bill of materials for a kit."""
        bom_entries = self.db.query(BillOfMaterials).filter(
            BillOfMaterials.parent_item_id == kit_id
        ).all()
        
        result = []
        for entry in bom_entries:
            component = entry.component_item
            result.append({
                'component_id': component.id,
                'sku': component.sku,
                'title': component.title,
                'quantity_required': entry.quantity_required,
                'unit_cost': component.base_cost or component.calculated_cost,
                'extended_cost': (component.base_cost or component.calculated_cost or 0) * entry.quantity_required
            })
        
        return result
    
    def can_assemble_kit(self, kit_id: int, quantity: int = 1) -> tuple[bool, Dict]:
        """
        Check if we have enough components to assemble a kit.
        
        Returns:
            (can_assemble, details_dict)
        """
        bom_entries = self.db.query(BillOfMaterials).filter(
            BillOfMaterials.parent_item_id == kit_id
        ).all()
        
        can_assemble = True
        details = {}
        
        for entry in bom_entries:
            component_inventory = self.db.query(Inventory).filter(
                Inventory.item_id == entry.component_item_id
            ).first()
            
            required = entry.quantity_required * quantity
            available = component_inventory.quantity_available if component_inventory else 0
            
            details[entry.component_item.sku] = {
                'required': required,
                'available': available,
                'sufficient': available >= required
            }
            
            if available < required:
                can_assemble = False
        
        return can_assemble, details
    
    def assemble_kit(self, kit_id: int, quantity: int = 1, notes: str = None) -> bool:
        """
        Assemble a kit by consuming components and adding to kit inventory.
        
        Returns:
            True if successful, False if insufficient components
        """
        can_assemble, details = self.can_assemble_kit(kit_id, quantity)
        
        if not can_assemble:
            return False
        
        # Get BOM
        bom_entries = self.db.query(BillOfMaterials).filter(
            BillOfMaterials.parent_item_id == kit_id
        ).all()
        
        # Consume components
        for entry in bom_entries:
            qty_needed = entry.quantity_required * quantity
            
            # Update component inventory
            component_inv = self.db.query(Inventory).filter(
                Inventory.item_id == entry.component_item_id
            ).first()
            
            component_inv.quantity_on_hand -= qty_needed
            component_inv.quantity_available = component_inv.quantity_on_hand - component_inv.quantity_reserved
            component_inv.last_updated = datetime.utcnow()
            
            # Log transaction
            transaction = InventoryTransaction(
                item_id=entry.component_item_id,
                transaction_type='kit_assembly',
                quantity=-qty_needed,
                reference_type='kit',
                reference_id=kit_id,
                notes=f"Used in assembly of {quantity} unit(s) of kit ID {kit_id}. {notes or ''}".strip()
            )
            self.db.add(transaction)
        
        # Add to kit inventory
        kit_inv = self.db.query(Inventory).filter(
            Inventory.item_id == kit_id
        ).first()
        
        kit_inv.quantity_on_hand += quantity
        kit_inv.quantity_available = kit_inv.quantity_on_hand - kit_inv.quantity_reserved
        kit_inv.last_updated = datetime.utcnow()
        
        # Log kit addition
        transaction = InventoryTransaction(
            item_id=kit_id,
            transaction_type='kit_assembly',
            quantity=quantity,
            reference_type='kit',
            reference_id=kit_id,
            notes=f"Assembled from components. {notes or ''}".strip()
        )
        self.db.add(transaction)
        
        self.db.commit()
        return True
    
    def get_item_inventory(self, item_id: int) -> Optional[Inventory]:
        """Get current inventory for an item."""
        return self.db.query(Inventory).filter(Inventory.item_id == item_id).first()
    
    def get_inventory_by_sku(self, sku: str) -> Optional[Inventory]:
        """Get current inventory for an item by SKU."""
        item = self.get_item_by_sku(sku)
        if item:
            return self.get_item_inventory(item.id)
        return None
    
    def adjust_inventory(self, item_id: int, quantity: int, notes: str = None, performed_by: str = None):
        """
        Manual inventory adjustment (positive or negative).
        
        Args:
            item_id: Item to adjust
            quantity: Quantity to add (positive) or remove (negative)
            notes: Reason for adjustment
            performed_by: Who performed the adjustment
        """
        inventory = self.db.query(Inventory).filter(
            Inventory.item_id == item_id
        ).first()
        
        if not inventory:
            raise ValueError(f"No inventory record for item {item_id}")
        
        inventory.quantity_on_hand += quantity
        inventory.quantity_available = inventory.quantity_on_hand - inventory.quantity_reserved
        inventory.last_updated = datetime.utcnow()
        
        # Log transaction
        transaction = InventoryTransaction(
            item_id=item_id,
            transaction_type='adjustment',
            quantity=quantity,
            reference_type='adjustment',
            notes=notes,
            performed_by=performed_by
        )
        self.db.add(transaction)
        self.db.commit()
    
    def get_transaction_history(self, item_id: int, limit: int = 50) -> List[InventoryTransaction]:
        """Get inventory transaction history for an item."""
        return self.db.query(InventoryTransaction).filter(
            InventoryTransaction.item_id == item_id
        ).order_by(InventoryTransaction.transaction_date.desc()).limit(limit).all()
    
    def get_items_below_reorder_point(self) -> List[Dict]:
        """Get items that need reordering."""
        items_query = self.db.query(ItemMaster, Inventory).join(
            Inventory, ItemMaster.id == Inventory.item_id
        ).filter(
            ItemMaster.is_active == True,
            ItemMaster.track_inventory == True
        ).all()
        
        reorder_list = []
        for item, inventory in items_query:
            if inventory.quantity_available <= item.reorder_point:
                reorder_list.append({
                    'id': item.id,
                    'sku': item.sku,
                    'title': item.title,
                    'quantity_available': inventory.quantity_available,
                    'reorder_point': item.reorder_point,
                    'reorder_quantity': item.reorder_quantity,
                    'supplier': item.supplier_name,
                    'supplier_url': item.supplier_url
                })
        
        return reorder_list
    
    def close(self):
        """Close database session."""
        self.db.close()
