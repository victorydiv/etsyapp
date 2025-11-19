# Quick Reference - New Inventory Features

## New GUI Tabs

### 🏭 Item Master
**Purpose**: Central catalog of all items - raw materials, components, finished goods, and kits

**Key Actions**:
- **➕ Add Item**: Create new inventory item
- **📦 Add Kit**: Create kit/assembly with BOM (Bill of Materials)
- **✏️ Edit**: Modify item details
- **🔧 Adjust Inventory**: Add or remove stock with notes
- **🔄 Refresh**: Reload item list

**Features**:
- Filter by category (all, raw material, component, finished good, kit)
- View item details including BOM for kits
- See on-hand, reserved, and available quantities
- View calculated costs for kits
- Track supplier information with URLs
- View complete transaction history

**Kit Assembly**:
1. Select a kit item
2. Click "Assemble Kit"
3. Enter quantity to build
4. System checks component availability
5. If sufficient, components are consumed and kit inventory increases

### 📥 Inbound Orders  
**Purpose**: Purchase order tracking and inventory receiving

**Key Actions**:
- **➕ New PO**: Create purchase order
- **📦 Receive**: Receive order into inventory
- **✏️ Edit**: Modify order details
- **❌ Cancel PO**: Cancel an order
- **🔄 Refresh**: Reload order list

**Features**:
- Filter by status (all, ordered, in_transit, received, cancelled)
- Auto-generated PO numbers (PO000001, PO000002, etc.)
- Track supplier reference numbers (Amazon order #, etc.)
- Store supplier URLs for easy reordering
- Track shipping, tax, and total costs
- Partial receiving support
- Automatic inventory updates on receipt

## Data Fields

### Item Master Fields
| Field | Required | Description |
|-------|----------|-------------|
| SKU | ✓ | Unique identifier |
| Title | ✓ | Item name |
| Category | | raw material, component, finished good, kit |
| Description | | Detailed description |
| Base Cost | | Direct cost (for purchased items) |
| Sell Price | | Selling price |
| Weight | | Weight in ounces |
| Dimensions | | LxWxH format |
| Storage Location | | Where item is stored |
| Supplier Name | | Vendor name |
| Supplier SKU | | Vendor's part number |
| Supplier URL | | Direct link to product page |
| Reorder Point | | Min qty before reorder alert |
| Reorder Quantity | | How many to order |
| Track Inventory | | Enable/disable tracking |
| Etsy Listing ID | | Link to Etsy listing |

### Kit (BOM) Fields
| Field | Required | Description |
|-------|----------|-------------|
| Kit SKU | ✓ | Unique identifier for kit |
| Kit Title | ✓ | Kit name |
| Sell Price | | Selling price |
| Components | ✓ | List of component SKUs + quantities |

**Note**: Kit cost is automatically calculated from component costs.

### Inbound Order Fields
| Field | Required | Description |
|-------|----------|-------------|
| Supplier | ✓ | Vendor name |
| Order Date | ✓ | When order was placed |
| Supplier Reference | | Their order/invoice number |
| Supplier URL | | Link to order on their site |
| Expected Date | | When you expect to receive |
| Status | | ordered, in_transit, received, cancelled |
| Tracking Number | | Shipment tracking |
| Carrier | | Shipping company |
| Line Items | ✓ | Items being ordered |
| Shipping Cost | | Shipping charges |
| Tax | | Tax charges |
| Notes | | Additional information |

## Keyboard Shortcuts

- **Double-click item** = Edit item
- **Enter** = Save dialog
- **Escape** = Cancel dialog

## Status Icons

### Item Master
- 🏭 = Item Master tab
- ➕ = Add new
- ✏️ = Edit
- 📦 = Kit/Assembly
- 🔧 = Adjust inventory
- 🔄 = Refresh

### Inbound Orders
- 📥 = Inbound Orders tab
- ○ = Items not yet received
- ✓ = Items fully received

## Common Workflows

### Add Raw Material
1. Item Master → Add Item
2. SKU: "WOOD-OAK-1X6"
3. Category: "raw material"
4. Add supplier info with URL
5. Set reorder point
6. Save

### Create Kit from Components
1. Item Master → Add Kit
2. Kit SKU: "KIT-BIRDHOUSE"
3. Add Component → Select each part
4. System calculates total cost
5. Save

### Order Supplies
1. Inbound Orders → New PO
2. Enter supplier: "Amazon"
3. Add line items
4. Paste Amazon order URL
5. Add shipping/tax
6. Save

### Receive Shipment
1. Find PO in Inbound Orders
2. Click Receive
3. Confirm quantities
4. Inventory updates automatically

### Assemble Products
1. Item Master → Select kit
2. Click "Assemble Kit"
3. Enter quantity
4. Components consumed, kit inventory increased

### Adjust Inventory
1. Item Master → Select item
2. Click "Adjust Inventory"
3. Enter +/- quantity
4. Add notes explaining why
5. Save

## Tips & Tricks

1. **Use SKU Prefixes**: 
   - RAW-xxx for raw materials
   - COMP-xxx for components
   - KIT-xxx for kits
   - PROD-xxx for finished goods

2. **Always Add Supplier URLs**: Makes reordering one-click

3. **Set Reorder Points**: Based on lead time + safety stock

4. **Use Notes Field**: Document adjustments, assemblies, and special situations

5. **Check Transaction History**: View complete audit trail for any item

6. **Partial Receiving**: Can receive orders in multiple shipments

7. **Kit Cost Updates**: When component costs change, kit costs update automatically

8. **Categories Help**: Use categories to organize and filter items

## Troubleshooting

**Q: Can't find my old inventory items?**
A: Check the "Legacy Inventory" tab or run the migration again.

**Q: Kit shows wrong cost?**
A: Edit the kit's BOM - cost recalculates from current component costs.

**Q: Can't assemble kit?**
A: Check component availability. System prevents assembly if insufficient components.

**Q: How do I delete an item?**
A: Edit the item and set it to inactive (or use database tools to delete).

**Q: Received wrong quantity?**
A: Receive what you got, then use Adjust Inventory to correct.

**Q: Need to track who made changes?**
A: Use the "performed_by" field in adjustments (set in code, future GUI feature).

## Database Tables

- `item_master` - All items catalog
- `bill_of_materials` - Kit components
- `inventory` - Current stock levels
- `inbound_orders` - Purchase orders
- `inbound_order_items` - PO line items
- `inventory_transactions` - Complete audit trail
- `local_inventory` - Legacy (deprecated)

## Future Enhancements

- [ ] User authentication for "performed_by" tracking
- [ ] Barcode scanning for receiving
- [ ] Low stock alerts/notifications
- [ ] Automatic PO generation from reorder points
- [ ] Supplier performance tracking
- [ ] Cost history and trends
- [ ] Inventory valuation reports
- [ ] Integration with pricing system
