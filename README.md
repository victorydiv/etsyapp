# Etsy Shop Management App

A comprehensive Python application for managing your Etsy shop, including inventory synchronization, order management, and automated document generation (packing lists, invoices, and shipping labels).

## Features

### 📦 Inventory Management
- Sync inventory from Etsy to local database
- Track local inventory with custom fields (cost, location)
- Update inventory quantities locally and sync to Etsy
- View low stock alerts
- Bidirectional sync between local and Etsy inventory

### 📋 Order Management
- Sync orders from Etsy
- View and filter orders by status
- Mark orders as packed
- Update tracking numbers
- Automatic status updates to Etsy

### 📄 Document Generation
- **Packing Lists**: Professional packing lists with checkboxes for order fulfillment
- **Invoices**: Detailed invoices with itemized pricing
- **Shipping Labels**: 4x6" shipping labels with tracking information
- Batch generate all documents for an order

### 🏪 Listing Management
- View all shop listings
- Get detailed listing information
- Update listing details

## Prerequisites

- Python 3.8 or higher
- Etsy Developer Account with API access
- Etsy Shop ID and API credentials

## Installation

1. **Clone or download this repository**

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Set up environment variables**
   - Copy `.env.example` to `.env`
   - Fill in your Etsy API credentials:
   ```
   ETSY_API_KEY=your_api_key_here
   ETSY_API_SECRET=your_api_secret_here
   ETSY_ACCESS_TOKEN=your_access_token_here
   ETSY_SHOP_ID=your_shop_id_here
   ```

## Getting Etsy API Credentials

1. Go to [Etsy Developers](https://www.etsy.com/developers/)
2. Create a new app
3. Note your API Key (Keystring)
4. Set up OAuth 2.0 to get an access token
5. Find your Shop ID in your shop's URL or via API

For detailed instructions, see [Etsy's API Documentation](https://developers.etsy.com/documentation/)

## Usage

### Starting the Application

Run the main application:
```bash
python main.py
```

### Menu Options

The application provides an interactive menu with the following options:

#### Inventory Management
1. **Sync inventory from Etsy** - Download all listings from Etsy to local database
2. **View local inventory** - Display all items with quantities and prices
3. **Update inventory quantity** - Modify quantities locally and optionally sync to Etsy
4. **View low stock items** - Get alerts for items below a threshold

#### Order Management
5. **Sync orders from Etsy** - Download recent orders
6. **View all orders** - Display all orders with status
7. **View pending orders** - Filter for orders awaiting fulfillment
8. **Mark order as packed** - Update order status
9. **Update tracking number** - Add tracking and sync to Etsy

#### Document Generation
10. **Generate packing list** - Create PDF packing list for an order
11. **Generate invoice** - Create PDF invoice for an order
12. **Generate shipping label** - Create 4x6" shipping label
13. **Generate all documents** - Create all three documents at once

#### Listing Management
14. **View shop listings** - Display all active listings
15. **Get listing details** - View detailed information for a specific listing

#### Other
16. **View shop information** - Display shop details
0. **Exit** - Close the application

## Project Structure

```
etsyapp/
├── main.py                  # Main CLI application
├── config.py               # Configuration management
├── database.py             # Database models and session management
├── etsy_api.py            # Etsy API client
├── inventory_manager.py    # Inventory management logic
├── order_manager.py        # Order management logic
├── document_generator.py   # PDF document generation
├── requirements.txt        # Python dependencies
├── .env.example           # Environment variables template
├── .env                   # Your credentials (create this)
├── .gitignore            # Git ignore rules
└── output/               # Generated PDF documents (auto-created)
```

## Database Schema

The application uses SQLite with three main tables:

### local_inventory
- Tracks inventory items with Etsy listing IDs
- Fields: SKU, title, quantity, price, cost, location, sync timestamps

### orders
- Stores order information from Etsy
- Fields: buyer info, shipping address, status, tracking, document flags

### order_items
- Individual line items for each order
- Links to orders and listings

## Document Output

All generated PDFs are saved to the `output/` directory with timestamps:
- `packing_list_[order_id]_[timestamp].pdf`
- `invoice_[order_id]_[timestamp].pdf`
- `shipping_label_[order_id]_[timestamp].pdf`

## API Usage

You can also use the modules programmatically:

```python
from config import Config
from database import init_db
from inventory_manager import InventoryManager
from order_manager import OrderManager

# Initialize
init_db()
inventory_mgr = InventoryManager()
order_mgr = OrderManager()

# Sync inventory
count = inventory_mgr.sync_from_etsy()
print(f"Synced {count} items")

# Get low stock items
low_stock = inventory_mgr.get_low_stock_items(threshold=5)

# Generate documents
pdf_path = order_mgr.generate_packing_list(order_id=1)
```

## Configuration Options

Edit `config.py` to customize:
- Database location
- PDF output directory
- API endpoints
- Timeout settings

## Troubleshooting

### Authentication Errors
- Verify your API credentials in `.env`
- Check that your access token hasn't expired
- Ensure your app has proper OAuth scopes

### API Rate Limits
- Etsy has rate limits (typically 10,000 requests/day)
- The app includes error handling for rate limits
- Consider adding delays for bulk operations

### PDF Generation Issues
- Ensure the `output/` directory is writable
- Check that ReportLab is properly installed
- Verify font availability on your system

### Database Errors
- Delete `etsy_inventory.db` to reset the database
- Run `init_db()` to recreate tables

## Security Notes

- Never commit your `.env` file
- Keep your API credentials secure
- Regularly rotate access tokens
- Use environment variables in production

## Development

To extend the application:

1. **Add new API endpoints**: Edit `etsy_api.py`
2. **Modify database schema**: Update `database.py` and run migrations
3. **Add document templates**: Extend `document_generator.py`
4. **Create new features**: Add methods to manager classes

## License

This project is provided as-is for personal or commercial use.

## Support

For Etsy API issues, consult the [Etsy Developer Documentation](https://developers.etsy.com/documentation/)

## Future Enhancements

Potential features to add:
- Web interface with Flask/Django
- Automated order fulfillment workflows
- Integration with shipping carriers (USPS, UPS, FedEx)
- Analytics and reporting dashboard
- Multi-shop support
- Barcode generation for inventory
- Email notifications
- Bulk operations (listing updates, price changes)

## Contributing

Feel free to submit issues, fork the repository, and create pull requests for any improvements.

---

**Note**: This application uses Etsy's v3 API. Make sure your Etsy app is configured for API v3 and has the necessary OAuth scopes for read and write operations on listings, inventory, and orders.
