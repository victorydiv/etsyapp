# Inventory System Upgrade - Quick Start

## What Changed?

The inventory system has been completely restructured from a simple list to a professional inventory management system with:

1. **Item Master** - Central catalog of all items
2. **Bill of Materials** - Build kits from components  
3. **Inbound Orders** - Track purchase orders and receiving
4. **Inventory Transactions** - Complete audit trail
5. **Automated Cost Calculations** - Kit costs calculated from components

## Getting Started

### Step 1: Run Migration (If you have existing data)
```bash
python migrate_inventory.py
```

This will convert your existing LocalInventory data to the new ItemMaster/Inventory structure.

### Step 2: Launch the App
```bash
python gui_app.py
```

You'll see two new tabs:
- **🏭 Item Master** - Manage all your items here
- **📥 Inbound Orders** - Track purchase orders

The old "📦 Legacy Inventory" tab still exists for reference.

## New Workflows

### Workflow 1: Add a Simple Item
1. Go to **Item Master** tab
2. Click **➕ Add Item**
3. Fill in: SKU, Title, Category, Cost, Price
4. Save

### Workflow 2: Create a Kit
1. First, create component items (the parts that make up your kit)
2. Click **📦 Add Kit**
3. Enter kit SKU and title
4. Click **➕ Add Component** for each part
5. Cost is automatically calculated

### Workflow 3: Order Supplies
1. Go to **Inbound Orders** tab
2. Click **➕ New PO**
3. Enter supplier name
4. Add items you're ordering with quantities
5. Add supplier reference number (e.g., Amazon order #)
6. Paste supplier URL for easy reordering
7. Save

### Workflow 4: Receive Order
1. When your order arrives, find it in **Inbound Orders**
2. Click **📦 Receive**
3. Confirm quantities received
4. Inventory automatically updates!

### Workflow 5: Assemble Kits
1. Go to **Item Master**
2. Select a kit item
3. Click **Assemble Kit**
4. Enter quantity
5. System checks if you have enough components
6. If yes, components are consumed and kit inventory increases

### Workflow 6: Check What to Reorder
1. Set reorder points when creating items
2. Items below reorder point are highlighted
3. Use supplier URLs to quickly reorder

## Key Features

### Item Master
- **Categories**: Organize items as raw material, component, finished good, or kit
- **Supplier Info**: Store supplier name, SKU, and URL for easy reordering
- **Reorder Points**: Set min/max levels
- **Bill of Materials**: Define what components make up a kit
- **Cost Tracking**: Base cost for purchased items, calculated cost for kits

### Inbound Orders
- **PO Numbers**: Auto-generated (PO000001, PO000002, etc.)
- **Supplier References**: Store order numbers from Amazon, etc.
- **URLs**: Direct links to orders on supplier sites
- **Status Tracking**: ordered → in_transit → received
- **Partial Receiving**: Receive items as they arrive
- **Cost Tracking**: Track shipping, tax, and total costs

### Inventory
- **On Hand**: Physical quantity you have
- **Reserved**: Quantity allocated to orders (future feature)
- **Available**: On hand - reserved
- **Transaction History**: See every movement with dates and notes

### Adjustments
- Add or remove inventory with notes
- Complete audit trail
- Track who made changes

## Data Structure

### Before (Simple)
```
LocalInventory:
  - SKU
  - Title  
  - Quantity
  - Price/Cost
```

### After (Professional)
```
ItemMaster:
  - SKU, Title, Description
  - Category (raw material, component, finished good, kit)
  - Pricing (base cost, calculated cost, sell price)
  - Physical (weight, dimensions, storage location)
  - Supplier (name, SKU, URL, lead time)
  - Reorder (point, quantity)
  - Etsy integration

BillOfMaterials:
  - Parent item (the kit)
  - Component items + quantities
  - Automated cost rollup

Inventory:
  - Item reference
  - Quantity on hand
  - Quantity reserved
  - Quantity available

InboundOrder:
  - PO number
  - Supplier info + reference + URL
  - Dates, status, tracking
  - Costs (subtotal, shipping, tax, total)

InboundOrderItem:
  - Line items for PO
  - Quantities ordered vs received

InventoryTransaction:
  - Complete audit trail
  - All movements logged
```

## Benefits

✅ **Know Your True Costs** - Kit costs automatically calculated  
✅ **Never Lose Track** - Every movement is logged  
✅ **Easy Reordering** - One click to supplier URLs  
✅ **Production Ready** - Build kits from components  
✅ **Professional** - Matches commercial systems  
✅ **Audit Trail** - Know who changed what and when  

## Tips

1. **Start with Raw Materials**: Add your basic components first
2. **Then Build Up**: Create kits from those components
3. **Use Categories**: Helps organize your catalog
4. **Add Supplier URLs**: Makes reordering quick
5. **Set Reorder Points**: Based on your sales velocity
6. **Use Notes**: Document adjustments and assemblies

## Migration Notes

- Old LocalInventory table is preserved (not deleted)
- New system references it as "Legacy Inventory" tab
- All old data is migrated to new structure
- You can still see old data but work in new system
- Eventually phase out legacy tab once comfortable

## Need Help?

See `INVENTORY_SYSTEM.md` for detailed documentation and code examples.
