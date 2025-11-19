# Inventory Management System - New Features

## Overview
The inventory system has been completely restructured to provide professional-grade inventory management with:
- **Item Master**: Central catalog of all items
- **Bill of Materials (BOM)**: Create kits from component items
- **Inbound Orders**: Purchase order tracking and receiving
- **Inventory Transactions**: Complete audit trail
- **Automated Cost Calculation**: Kit costs calculated from components

## Database Structure

### ItemMaster
Central catalog defining all items that can be in inventory:
- SKU (unique identifier)
- Category: raw material, component, finished good, kit
- Pricing: base cost, calculated cost (for kits), sell price
- Physical attributes: weight, dimensions
- Supplier information with URLs for easy reordering
- Reorder points and quantities
- Etsy listing integration

### BillOfMaterials (BOM)
Defines what components make up a kit/assembly:
- Parent item (the kit)
- Component items with quantities required
- Automated cost rollup

### Inventory
Current stock levels:
- Quantity on hand
- Quantity reserved (for orders)
- Quantity available (on hand - reserved)

### InboundOrder & InboundOrderItem
Purchase orders for replenishing stock:
- Supplier tracking with reference numbers and URLs
- Expected and received dates
- Shipping, tax, and total costs
- Partial receiving support
- Status tracking: ordered → in_transit → received

### InventoryTransaction
Complete audit trail of all inventory movements:
- Inbound receipts
- Outbound shipments
- Manual adjustments
- Kit assemblies

## Key Features

### 1. Item Master Management
Create and manage all inventory items:
```python
from item_master_manager import ItemMasterManager

manager = ItemMasterManager()

# Create a raw material
item = manager.create_item(
    sku="WOOD-OAK-1X6",
    title="Oak Board 1x6x8",
    category="raw material",
    base_cost=12.50,
    supplier_name="Home Depot",
    supplier_url="https://homedepot.com/...",
    reorder_point=10,
    reorder_quantity=20
)
```

### 2. Kit Assembly with BOM
Build finished goods from components:
```python
# Create a kit with components
kit = manager.create_kit(
    kit_sku="KIT-BIRDHOUSE",
    kit_title="Cedar Birdhouse Kit",
    components=[
        {'sku': 'WOOD-CEDAR-1X6', 'quantity': 2},
        {'sku': 'SCREW-WOOD-1IN', 'quantity': 12},
        {'sku': 'HINGE-SMALL', 'quantity': 1}
    ],
    sell_price=45.00
)
# Calculated cost is automatically summed from components

# Check if you can assemble
can_make, details = manager.can_assemble_kit(kit.id, quantity=5)

# Assemble kits (consumes components, adds to kit inventory)
success = manager.assemble_kit(kit.id, quantity=5, notes="Production run #1")
```

### 3. Inbound Orders (Purchase Orders)
Track purchases and receive into inventory:
```python
from inbound_order_manager import InboundOrderManager

po_manager = InboundOrderManager()

# Create a purchase order
po = po_manager.create_inbound_order(
    supplier_name="Amazon",
    items=[
        {'sku': 'SCREW-WOOD-1IN', 'quantity': 500, 'unit_cost': 0.05},
        {'sku': 'HINGE-SMALL', 'quantity': 100, 'unit_cost': 1.25}
    ],
    supplier_reference="113-9876543-1234567",
    supplier_url="https://amazon.com/gp/your-account/order-details?orderID=...",
    shipping_cost=5.99,
    tax=3.45,
    expected_date=datetime(2025, 11, 20)
)
# PO number auto-generated: PO000001

# Mark as in transit
po_manager.update_inbound_order(po.id, 
    status='in_transit',
    tracking_number='1Z999AA10123456784',
    carrier='UPS'
)

# Receive into inventory
po_manager.receive_order(
    po.id,
    received_date=datetime.now(),
    notes="All items received in good condition"
)
# Inventory automatically updated, transactions logged
```

### 4. Inventory Adjustments
Manual adjustments with audit trail:
```python
# Add inventory (e.g., found extra stock)
manager.adjust_inventory(
    item_id=123,
    quantity=5,
    notes="Found 5 units in back storage",
    performed_by="John"
)

# Remove inventory (e.g., damaged)
manager.adjust_inventory(
    item_id=123,
    quantity=-3,
    notes="3 units damaged during inspection",
    performed_by="Mary"
)
```

### 5. Reorder Management
Get items that need reordering:
```python
reorder_list = manager.get_items_below_reorder_point()
# Returns items with available quantity <= reorder point
# Includes supplier info for easy reordering
```

### 6. Transaction History
Complete audit trail:
```python
history = manager.get_transaction_history(item_id=123, limit=50)
for txn in history:
    print(f"{txn.transaction_date}: {txn.transaction_type} "
          f"{txn.quantity} - {txn.notes}")
```

## GUI Features

### Item Master Tab
- Browse all items with filtering by category
- Add/edit items with full details
- Create kits with visual BOM editor
- View calculated costs for kits
- Assemble kits with component availability checking
- Manual inventory adjustments
- Transaction history viewer

### Inbound Orders Tab
- Create purchase orders with line items
- Track order status from ordered → received
- Add supplier references and URLs for easy access
- Partial receiving support
- Automatic inventory updates on receipt
- Cost tracking with shipping and tax

## Migration

If you have existing data in the old `LocalInventory` table:

```bash
python migrate_inventory.py
```

This will:
1. Create all new tables
2. Migrate existing inventory to ItemMaster and Inventory
3. Preserve your data (old table kept for reference)

## Workflow Examples

### Example 1: Manufacturing Workflow
1. **Set up raw materials** in Item Master with supplier info
2. **Create kit items** with BOMs defining what components are needed
3. **Create purchase orders** when materials run low
4. **Receive orders** into inventory
5. **Assemble kits** as needed for orders
6. **Ship orders** (decrements kit inventory automatically)

### Example 2: Dropshipping/Resale
1. **Create items** for products you sell (category: finished good)
2. **Set reorder points** based on sales velocity
3. **Get reorder list** daily/weekly
4. **Create POs** with Amazon/supplier URLs for one-click reordering
5. **Receive and ship** as orders come in

### Example 3: Hybrid
1. Some items are **raw materials** → assembled into **kits**
2. Other items are **finished goods** purchased directly
3. All tracked in one system with complete visibility

## Benefits

✅ **Cost Accuracy**: Kits automatically calculate cost from components
✅ **Audit Trail**: Every inventory movement is logged
✅ **Supplier Links**: One-click access to reorder from Amazon, etc.
✅ **Reorder Automation**: Know what to order before you run out
✅ **Component Tracking**: See what raw materials you need for production
✅ **Purchase History**: Track all incoming orders and costs
✅ **Professional**: Matches commercial inventory management systems

## Next Steps

1. Run migration if you have existing data
2. Set up your item master catalog
3. Add supplier information and URLs
4. Create any kit items with BOMs
5. Create purchase orders as you order inventory
6. Use the GUI for daily operations
