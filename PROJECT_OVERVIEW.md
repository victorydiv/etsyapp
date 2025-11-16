# Project Structure Overview

## 📁 Complete File Structure

```
etsyapp/
│
├── 📄 main.py                    # Main CLI application entry point
├── 📄 config.py                  # Configuration and environment management
├── 📄 database.py                # SQLAlchemy models and database setup
├── 📄 etsy_api.py                # Etsy API v3 client wrapper
├── 📄 inventory_manager.py       # Inventory sync and management logic
├── 📄 order_manager.py           # Order processing and management
├── 📄 document_generator.py      # PDF generation for all documents
├── 📄 utils.py                   # Helper functions and utilities
├── 📄 demo.py                    # Demo/test script (no API required)
│
├── 📄 requirements.txt           # Python dependencies
├── 📄 .env.example               # Environment variables template
├── 📄 .gitignore                 # Git ignore rules
├── 📄 __init__.py                # Package initialization
│
├── 📖 README.md                  # Complete documentation
├── 📖 QUICKSTART.md              # Quick start guide
└── 📖 PROJECT_OVERVIEW.md        # This file
```

## 🔧 Core Components

### 1. **main.py** - Application Entry Point
- Interactive CLI menu system
- User-friendly interface for all operations
- Coordinates all managers and modules
- Handles user input and error messages

**Key Features:**
- 16 menu options covering all functionality
- Emoji-based visual feedback
- Input validation and error handling

### 2. **config.py** - Configuration Management
- Loads environment variables from .env file
- Validates required credentials
- Provides centralized configuration access
- Creates necessary directories

**Configuration:**
- Etsy API credentials
- Database connection string
- Output directory paths

### 3. **database.py** - Data Models
- SQLAlchemy ORM models
- Three main tables:
  - `local_inventory`: Product inventory tracking
  - `orders`: Order information
  - `order_items`: Line items for orders
- Database initialization
- Session management

### 4. **etsy_api.py** - API Client
- Complete Etsy API v3 wrapper
- All authentication headers managed
- Error handling for API calls

**API Endpoints Covered:**
- Listing management (get, create, update)
- Inventory operations
- Order/receipt retrieval
- Tracking updates
- Shop information

### 5. **inventory_manager.py** - Inventory Operations
- Bidirectional sync (Etsy ↔ Local)
- Quantity updates with optional Etsy sync
- Low stock alerts
- Custom fields (cost, location)

**Key Methods:**
- `sync_from_etsy()`: Download all listings
- `sync_to_etsy()`: Push local changes to Etsy
- `update_local_inventory()`: Update quantities
- `get_low_stock_items()`: Stock alerts

### 6. **order_manager.py** - Order Operations
- Order synchronization from Etsy
- Status tracking and updates
- Document generation coordination
- Tracking number management

**Key Methods:**
- `sync_orders_from_etsy()`: Download orders
- `get_orders()`: Retrieve with filters
- `mark_order_packed()`: Update status
- `update_tracking()`: Sync tracking to Etsy
- `generate_*()`: Create PDFs

### 7. **document_generator.py** - PDF Creation
- Professional PDF documents using ReportLab
- Three document types with custom styling
- Configurable layouts and branding

**Documents Generated:**
- **Packing Lists**: Checklist format with locations
- **Invoices**: Itemized with totals
- **Shipping Labels**: 4x6" format ready to print

### 8. **utils.py** - Helper Functions
- Currency formatting
- Date/time utilities
- Address formatting
- Progress tracking
- Color output for terminal
- Data validation functions

## 🔄 Data Flow

### Order Fulfillment Flow
```
Etsy → sync_orders_from_etsy() → Local Database
         ↓
    Generate Documents (PDFs)
         ↓
    Mark as Packed (Local DB)
         ↓
    Add Tracking → Update Etsy
```

### Inventory Management Flow
```
Etsy → sync_from_etsy() → Local Database
                              ↓
                    Update Quantities
                              ↓
                    sync_to_etsy() → Etsy
```

## 💾 Database Schema

### local_inventory
```sql
- id (Primary Key)
- etsy_listing_id (Unique, Indexed)
- sku (Unique, Indexed)
- title
- quantity
- price
- cost
- location
- last_synced
- created_at
- updated_at
```

### orders
```sql
- id (Primary Key)
- etsy_order_id (Unique, Indexed)
- buyer_name
- buyer_email
- shipping_address
- total_amount
- order_date
- status
- tracking_number
- packed (Boolean)
- invoice_generated (Boolean)
- label_generated (Boolean)
- created_at
- updated_at
```

### order_items
```sql
- id (Primary Key)
- order_id (Foreign Key to orders.id)
- etsy_listing_id
- sku
- title
- quantity
- price
- created_at
```

## 🚀 Usage Patterns

### For Development
```python
# Import and use programmatically
from inventory_manager import InventoryManager
from order_manager import OrderManager

inv_mgr = InventoryManager()
items = inv_mgr.get_local_inventory()

order_mgr = OrderManager()
pdf = order_mgr.generate_invoice(order_id=1)
```

### For End Users
```bash
# Run the interactive CLI
python main.py

# Or run the demo/test
python demo.py
```

## 📦 Dependencies

### Core Libraries
- **requests**: HTTP client for Etsy API
- **python-dotenv**: Environment variable management
- **sqlalchemy**: ORM for database operations
- **reportlab**: PDF generation
- **Pillow**: Image processing (for PDFs)
- **pandas**: Data manipulation (optional features)

## 🔒 Security Features

- Environment variables for credentials
- .gitignore prevents credential commits
- No hardcoded API keys
- Secure token-based authentication
- Input validation throughout

## 🎯 Key Features by Category

### Inventory Management
✅ Sync from Etsy  
✅ Update quantities locally  
✅ Push changes to Etsy  
✅ Low stock alerts  
✅ Custom fields (cost, location)  

### Order Management
✅ Sync orders from Etsy  
✅ Filter by status  
✅ Track packing status  
✅ Update tracking numbers  
✅ Automatic Etsy updates  

### Document Generation
✅ Professional packing lists  
✅ Detailed invoices  
✅ Shipping labels (4x6")  
✅ Batch generation  
✅ Timestamped filenames  

### Listing Management
✅ View all listings  
✅ Get listing details  
✅ Update listings  
✅ Manage inventory  

## 🛠️ Extensibility

### Easy to Add:
- New document types (modify `document_generator.py`)
- Additional API endpoints (extend `etsy_api.py`)
- New database fields (update `database.py` models)
- Custom reports (use `utils.py` helpers)
- Web interface (Flask/Django wrapper around managers)

### Suggested Enhancements:
1. **Web UI**: Flask dashboard for browser access
2. **Automation**: Scheduled syncs with cron/Task Scheduler
3. **Notifications**: Email/SMS alerts for orders
4. **Analytics**: Sales reports and trends
5. **Multi-shop**: Support multiple Etsy shops
6. **Barcode**: Generate/scan barcodes for inventory
7. **Shipping**: Direct carrier API integration
8. **Bulk Operations**: Mass updates for listings

## 📊 Module Relationships

```
main.py
  ├─→ config.py (configuration)
  ├─→ database.py (data models)
  ├─→ etsy_api.py (API calls)
  ├─→ inventory_manager.py
  │     ├─→ database.py
  │     └─→ etsy_api.py
  ├─→ order_manager.py
  │     ├─→ database.py
  │     ├─→ etsy_api.py
  │     └─→ document_generator.py
  └─→ utils.py (helpers)
```

## 🎓 Learning Path

### Beginner → Start Here:
1. Read `QUICKSTART.md`
2. Run `python demo.py` to test without API
3. Configure `.env` with credentials
4. Run `python main.py` and explore menus

### Intermediate → Customize:
1. Read `README.md` for full documentation
2. Modify `document_generator.py` for custom PDFs
3. Add custom fields to database models
4. Extend API client with new endpoints

### Advanced → Extend:
1. Build web interface using Flask
2. Add automated workflows
3. Integrate with shipping carriers
4. Create analytics dashboard
5. Build mobile companion app

## 📈 Performance Considerations

- **API Rate Limits**: Etsy limits ~10,000 requests/day
- **Database**: SQLite suitable for small-medium shops
- **PDF Generation**: Fast, but consider background jobs for bulk
- **Sync Strategy**: Manual sync vs scheduled automation

## 🧪 Testing

### Quick Test (No API Required)
```bash
python demo.py
```

### Full Test (Requires API)
```bash
python main.py
# Choose option 1 (sync inventory)
# Choose option 5 (sync orders)
```

## 📞 Support Resources

- **Etsy API Docs**: https://developers.etsy.com/documentation/
- **ReportLab Docs**: https://www.reportlab.com/docs/
- **SQLAlchemy Docs**: https://docs.sqlalchemy.org/

---

**Created**: November 2025  
**Version**: 1.0.0  
**Python**: 3.8+  
**License**: Open for personal and commercial use
