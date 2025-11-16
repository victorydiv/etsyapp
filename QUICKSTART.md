# Quick Start Guide

## Setup (5 minutes)

### 1. Install Python Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure Etsy API Credentials
Copy the example environment file:
```bash
copy .env.example .env
```

Edit `.env` and add your credentials:
```
ETSY_API_KEY=your_keystring_from_etsy
ETSY_API_SECRET=your_shared_secret
ETSY_ACCESS_TOKEN=your_oauth_token
ETSY_SHOP_ID=your_shop_id
```

### 3. Run the Application
```bash
python main.py
```

## First Time Usage

### Step 1: Sync Your Data
1. Choose option **1** to sync inventory from Etsy
2. Choose option **5** to sync orders from Etsy

### Step 2: View Your Data
- Option **2**: View all inventory items
- Option **6**: View all orders
- Option **4**: Check for low stock items

### Step 3: Process an Order
1. Choose option **7** to view pending orders
2. Note the order ID (first column)
3. Choose option **13** to generate all documents for that order
4. Find your PDFs in the `output/` folder!

## Common Workflows

### Order Fulfillment Workflow
1. **Sync orders** (option 5)
2. **View pending orders** (option 7)
3. **Generate packing list** (option 10) - print and use to pack
4. **Mark as packed** (option 8)
5. **Generate shipping label** (option 12)
6. **Update tracking** (option 9) - automatically updates Etsy!
7. **Generate invoice** (option 11) - include in package

### Inventory Management Workflow
1. **Sync from Etsy** (option 1) - gets current quantities
2. **View low stock** (option 4) - see what needs restocking
3. **Update quantity** (option 3) - adjust after restocking
   - Choose 'y' when asked to sync to push changes to Etsy

### Daily Operations
- Morning: Sync orders (option 5) to get overnight sales
- Process: Generate documents (option 13) for all new orders
- Afternoon: Update tracking numbers (option 9) for shipped orders
- Evening: Check low stock (option 4) for restock planning

## Tips & Tricks

- **Batch Processing**: Generate all documents at once (option 13) saves time
- **Local Database**: Your local database persists data, no need to sync every time
- **PDF Organization**: All PDFs include timestamps, organized in `output/` folder
- **Tracking Updates**: Option 9 updates both local database AND Etsy automatically
- **Low Stock Alerts**: Run option 4 regularly to avoid stockouts

## Troubleshooting

**"Configuration Error"** → Check your `.env` file has all required fields

**"Authentication failed"** → Verify your access token is valid and not expired

**No orders/inventory showing** → Run sync options (1 and 5) first

**PDF not generating** → Check that `output/` folder exists and is writable

## Getting Etsy Credentials - Quick Guide

1. Go to https://www.etsy.com/developers/
2. Click "Register as a Developer" if you haven't
3. Create a new app
4. Copy your "Keystring" (this is ETSY_API_KEY)
5. Click "Request Access Token" to get OAuth token
6. Your Shop ID is in your shop URL: etsy.com/shop/YourShopName

Need more help? See the full README.md

## Need Help?

- Read the full **README.md** for detailed documentation
- Check **config.py** to customize settings
- Review Etsy API docs: https://developers.etsy.com/documentation/

---

**Ready to go?** Run `python main.py` and start managing your shop! 🎉
