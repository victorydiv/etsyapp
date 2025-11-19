"""
GUI Application for Etsy Shop Management
Modern interface with tabs for different functions
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog
from datetime import datetime
import threading
import os
import subprocess
from pathlib import Path

from config import Config
from database import init_db, get_db, LocalInventory, Order, OrderItem
from inventory_manager import InventoryManager
from order_manager import OrderManager
from document_generator import DocumentGenerator
from settings_dialog import show_settings_dialog
from item_master_tab import ItemMasterTab
from inbound_orders_tab import InboundOrdersTab

class EtsyAppGUI:
    """Main GUI Application."""
    
    def __init__(self, root):
        """Initialize the GUI."""
        self.root = root
        self.root.title("EMS - Etsy Management System")
        self.root.geometry("1200x700")
        
        # Initialize database
        init_db()
        
        # Check Etsy connection
        self.etsy_available = False
        self.etsy_status = self.check_etsy_connection()
        
        # Always initialize order manager (needed for manual orders)
        self.order_manager = OrderManager()
        
        if self.etsy_status['available']:
            self.inventory_manager = InventoryManager()
            self.etsy_available = True
            self.status_text = f"✅ {self.etsy_status['message']}"
        else:
            self.inventory_manager = None
            self.status_text = f"⚠️ {self.etsy_status['message']}"
        
        self.doc_generator = DocumentGenerator()
        
        # Set up the GUI
        self.setup_styles()
        self.create_widgets()
        self.load_inventory()
        self.load_orders()
    
    def check_etsy_connection(self):
        """Check if Etsy API is actually accessible."""
        try:
            # First check if credentials are configured
            Config.validate()
        except ValueError as e:
            return {
                'available': False,
                'message': 'Local Mode - Etsy credentials not configured',
                'error': str(e)
            }
        
        # Credentials exist, now test actual API connection
        try:
            import requests
            
            headers = {
                'x-api-key': Config.ETSY_API_KEY,
                'Authorization': f'Bearer {Config.ETSY_ACCESS_TOKEN}'
            }
            
            # Try a simple API call with short timeout
            response = requests.get(
                f'https://openapi.etsy.com/v3/application/shops/{Config.ETSY_SHOP_ID}',
                headers=headers,
                timeout=5
            )
            
            if response.status_code == 200:
                shop_data = response.json()
                return {
                    'available': True,
                    'message': f"Connected to Etsy - Shop: {shop_data.get('shop_name', 'Unknown')}",
                    'shop_data': shop_data
                }
            elif response.status_code == 401:
                return {
                    'available': False,
                    'message': 'Local Mode - Invalid Etsy credentials (check access token)',
                    'error': 'Authentication failed'
                }
            elif response.status_code == 403:
                return {
                    'available': False,
                    'message': 'Local Mode - API key not approved yet',
                    'error': 'API key pending approval'
                }
            else:
                return {
                    'available': False,
                    'message': f'Local Mode - Etsy API error (status {response.status_code})',
                    'error': response.text
                }
                
        except requests.exceptions.Timeout:
            return {
                'available': False,
                'message': 'Local Mode - Connection timeout (check internet)',
                'error': 'Timeout'
            }
        except requests.exceptions.ConnectionError:
            return {
                'available': False,
                'message': 'Local Mode - No internet connection',
                'error': 'Connection error'
            }
        except Exception as e:
            return {
                'available': False,
                'message': 'Local Mode - Unable to connect to Etsy',
                'error': str(e)
            }
    
    def setup_styles(self):
        """Configure ttk styles."""
        style = ttk.Style()
        style.theme_use('clam')
        
        # Configure colors
        style.configure('TNotebook', background='#f0f0f0')
        style.configure('TFrame', background='#f0f0f0')
        style.configure('TLabel', background='#f0f0f0', font=('Segoe UI', 10))
        style.configure('Title.TLabel', font=('Segoe UI', 16, 'bold'))
        style.configure('Header.TLabel', font=('Segoe UI', 12, 'bold'))
        style.configure('TButton', font=('Segoe UI', 10))
        style.configure('Action.TButton', font=('Segoe UI', 10, 'bold'))
        
        # Treeview styles
        style.configure('Treeview', font=('Segoe UI', 9), rowheight=25)
        style.configure('Treeview.Heading', font=('Segoe UI', 10, 'bold'))
    
    def create_widgets(self):
        """Create all GUI widgets."""
        # Top status bar
        status_frame = ttk.Frame(self.root)
        status_frame.pack(fill='x', padx=10, pady=5)
        
        ttk.Label(status_frame, text="Etsy Shop Manager", 
                 style='Title.TLabel').pack(side='left')
        ttk.Label(status_frame, text=self.status_text).pack(side='right')
        
        # Create notebook (tabs)
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill='both', expand=True, padx=10, pady=5)
        
        # Create tabs
        self.create_item_master_tab()
        self.create_inbound_orders_tab()
        self.create_inventory_tab()
        self.create_orders_tab()
        self.create_documents_tab()
        self.create_settings_tab()
        
        # Bottom button bar
        button_frame = ttk.Frame(self.root)
        button_frame.pack(fill='x', padx=10, pady=5)
        
        if self.etsy_available:
            ttk.Button(button_frame, text="🔄 Sync from Etsy", 
                      command=self.sync_all, style='Action.TButton').pack(side='left', padx=5)
        
        ttk.Button(button_frame, text="📂 Open Output Folder", 
                  command=self.open_output_folder).pack(side='left', padx=5)
        ttk.Button(button_frame, text="ℹ️ Help", 
                  command=self.show_help).pack(side='right', padx=5)
    
    def create_item_master_tab(self):
        """Create the item master tab."""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text='🏭 Item Master')
        self.item_master_tab = ItemMasterTab(tab, self)
    
    def create_inbound_orders_tab(self):
        """Create the inbound orders tab."""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text='📥 Inbound Orders')
        self.inbound_orders_tab = InboundOrdersTab(tab, self)
    
    def create_inventory_tab(self):
        """Create the inventory overview tab - shows current stock levels."""
        from item_master_manager import ItemMasterManager
        
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text='� Inventory Levels')
        
        # Store manager reference
        self.inv_manager = ItemMasterManager()
        
        # Top controls
        control_frame = ttk.Frame(tab)
        control_frame.pack(fill='x', padx=10, pady=10)
        
        ttk.Label(control_frame, text="Current Inventory Levels", 
                 style='Header.TLabel').pack(side='left')
        
        # Stats labels
        self.inv_stats_frame = ttk.Frame(control_frame)
        self.inv_stats_frame.pack(side='left', padx=20)
        self.inv_total_items_label = ttk.Label(self.inv_stats_frame, text="Items: 0")
        self.inv_total_items_label.pack(side='left', padx=10)
        self.inv_low_stock_label = ttk.Label(self.inv_stats_frame, text="Low Stock: 0", foreground='red')
        self.inv_low_stock_label.pack(side='left', padx=10)
        
        btn_frame = ttk.Frame(control_frame)
        btn_frame.pack(side='right')
        
        ttk.Button(btn_frame, text="⚠️ Low Stock Only", 
                  command=self.show_low_stock_inventory).pack(side='left', padx=2)
        ttk.Button(btn_frame, text="🔄 Refresh", 
                  command=self.load_inventory_levels).pack(side='left', padx=2)
        ttk.Button(btn_frame, text="📥 Export", 
                  command=self.export_inventory).pack(side='left', padx=2)
        
        # Filter frame
        filter_frame = ttk.Frame(tab)
        filter_frame.pack(fill='x', padx=10, pady=5)
        
        ttk.Label(filter_frame, text="Category:").pack(side='left', padx=5)
        self.inv_category_var = tk.StringVar(value="all")
        category_combo = ttk.Combobox(
            filter_frame,
            textvariable=self.inv_category_var,
            values=['all', 'raw material', 'component', 'finished good', 'kit'],
            state='readonly',
            width=15
        )
        category_combo.pack(side='left', padx=5)
        category_combo.bind('<<ComboboxSelected>>', lambda e: self.load_inventory_levels())
        
        ttk.Label(filter_frame, text="Search:").pack(side='left', padx=(20, 5))
        self.inv_search_var = tk.StringVar()
        self.inv_search_var.trace('w', lambda *args: self.filter_inventory_levels())
        search_entry = ttk.Entry(filter_frame, textvariable=self.inv_search_var, width=30)
        search_entry.pack(side='left', padx=5)
        
        # Inventory treeview
        tree_frame = ttk.Frame(tab)
        tree_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        # Scrollbars
        v_scroll = ttk.Scrollbar(tree_frame, orient='vertical')
        h_scroll = ttk.Scrollbar(tree_frame, orient='horizontal')
        
        self.inventory_tree = ttk.Treeview(
            tree_frame,
            columns=('sku', 'title', 'category', 'on_hand', 'on_order', 'reserved', 'available', 
                    'reorder_point', 'cost', 'value', 'location'),
            show='headings',
            yscrollcommand=v_scroll.set,
            xscrollcommand=h_scroll.set
        )
        
        v_scroll.config(command=self.inventory_tree.yview)
        h_scroll.config(command=self.inventory_tree.xview)
        
        # Configure columns
        self.inventory_tree.heading('sku', text='SKU')
        self.inventory_tree.heading('title', text='Title')
        self.inventory_tree.heading('category', text='Category')
        self.inventory_tree.heading('on_hand', text='On Hand')
        self.inventory_tree.heading('on_order', text='On Order')
        self.inventory_tree.heading('reserved', text='Reserved')
        self.inventory_tree.heading('available', text='Available')
        self.inventory_tree.heading('reorder_point', text='Reorder Pt')
        self.inventory_tree.heading('cost', text='Unit Cost')
        self.inventory_tree.heading('value', text='Total Value')
        self.inventory_tree.heading('location', text='Location')
        
        self.inventory_tree.column('sku', width=120)
        self.inventory_tree.column('title', width=250)
        self.inventory_tree.column('category', width=100)
        self.inventory_tree.column('on_hand', width=80)
        self.inventory_tree.column('on_order', width=80)
        self.inventory_tree.column('reserved', width=80)
        self.inventory_tree.column('available', width=80)
        self.inventory_tree.column('reorder_point', width=80)
        self.inventory_tree.column('cost', width=80)
        self.inventory_tree.column('value', width=100)
        self.inventory_tree.column('location', width=120)
        
        # Pack treeview and scrollbars
        self.inventory_tree.grid(row=0, column=0, sticky='nsew')
        v_scroll.grid(row=0, column=1, sticky='ns')
        h_scroll.grid(row=1, column=0, sticky='ew')
        
        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)
        
        # Tag for low stock highlighting
        self.inventory_tree.tag_configure('low_stock', background='#ffcccc')
        self.inventory_tree.tag_configure('out_of_stock', background='#ff9999', foreground='white')
    
    def create_orders_tab(self):
        """Create the orders management tab."""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text='📋 Orders')
        
        # Top controls
        control_frame = ttk.Frame(tab)
        control_frame.pack(fill='x', padx=10, pady=10)
        
        ttk.Label(control_frame, text="Order Management", 
                 style='Header.TLabel').pack(side='left')
        
        btn_frame = ttk.Frame(control_frame)
        btn_frame.pack(side='right')
        
        ttk.Button(btn_frame, text="➕ Add Order", 
                  command=self.add_order).pack(side='left', padx=2)
        ttk.Button(btn_frame, text="🔄 Refresh", 
                  command=self.load_orders).pack(side='left', padx=2)
        
        if self.etsy_available:
            ttk.Button(btn_frame, text="☁️ Sync from Etsy", 
                      command=self.sync_orders).pack(side='left', padx=2)
        
        # Filter frame
        filter_frame = ttk.Frame(tab)
        filter_frame.pack(fill='x', padx=10, pady=5)
        
        ttk.Label(filter_frame, text="Status Filter:").pack(side='left', padx=5)
        self.order_filter_var = tk.StringVar(value="All")
        filter_combo = ttk.Combobox(
            filter_frame, 
            textvariable=self.order_filter_var,
            values=['All', 'pending', 'packed', 'shipped', 'delivered'],
            state='readonly',
            width=15
        )
        filter_combo.pack(side='left', padx=5)
        filter_combo.bind('<<ComboboxSelected>>', lambda e: self.load_orders())
        
        ttk.Label(filter_frame, text="Search:").pack(side='left', padx=(20, 5))
        self.order_search_var = tk.StringVar()
        self.order_search_var.trace('w', lambda *args: self.filter_orders())
        ttk.Entry(filter_frame, textvariable=self.order_search_var, width=30).pack(side='left')
        
        # Orders treeview
        tree_frame = ttk.Frame(tab)
        tree_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        v_scroll = ttk.Scrollbar(tree_frame, orient='vertical')
        h_scroll = ttk.Scrollbar(tree_frame, orient='horizontal')
        
        self.orders_tree = ttk.Treeview(
            tree_frame,
            columns=('id', 'order_id', 'customer', 'email', 'amount', 'date', 'status', 'packed'),
            show='headings',
            yscrollcommand=v_scroll.set,
            xscrollcommand=h_scroll.set
        )
        
        v_scroll.config(command=self.orders_tree.yview)
        h_scroll.config(command=self.orders_tree.xview)
        
        # Configure columns
        self.orders_tree.heading('id', text='ID')
        self.orders_tree.heading('order_id', text='Order #')
        self.orders_tree.heading('customer', text='Customer')
        self.orders_tree.heading('email', text='Email')
        self.orders_tree.heading('amount', text='Amount')
        self.orders_tree.heading('date', text='Order Date')
        self.orders_tree.heading('status', text='Status')
        self.orders_tree.heading('packed', text='Packed')
        
        self.orders_tree.column('id', width=50)
        self.orders_tree.column('order_id', width=120)
        self.orders_tree.column('customer', width=180)
        self.orders_tree.column('email', width=200)
        self.orders_tree.column('amount', width=80)
        self.orders_tree.column('date', width=120)
        self.orders_tree.column('status', width=80)
        self.orders_tree.column('packed', width=60)
        
        self.orders_tree.grid(row=0, column=0, sticky='nsew')
        v_scroll.grid(row=0, column=1, sticky='ns')
        h_scroll.grid(row=1, column=0, sticky='ew')
        
        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)
        
        # Action buttons frame
        action_frame = ttk.Frame(tab)
        action_frame.pack(fill='x', padx=10, pady=5)
        
        ttk.Button(action_frame, text="📦 Mark as Packed", 
                  command=self.mark_order_packed).pack(side='left', padx=5)
        ttk.Button(action_frame, text="📭 Unpack Order", 
                  command=self.unpack_order).pack(side='left', padx=5)
        ttk.Button(action_frame, text="🏷️ Add Tracking", 
                  command=self.add_tracking).pack(side='left', padx=5)
        ttk.Button(action_frame, text="❌ Cancel Order", 
                  command=self.cancel_order).pack(side='left', padx=5)
        ttk.Button(action_frame, text="📄 View Details", 
                  command=self.view_order_details).pack(side='left', padx=5)
        
        # Bind double-click
        self.orders_tree.bind('<Double-1>', lambda e: self.view_order_details())
    
    def create_documents_tab(self):
        """Create the document generation tab."""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text='📄 Documents')
        
        # Header
        ttk.Label(tab, text="Document Generation", 
                 style='Header.TLabel').pack(pady=20)
        
        # Main frame
        main_frame = ttk.Frame(tab)
        main_frame.pack(expand=True)
        
        # Order selection
        select_frame = ttk.Frame(main_frame)
        select_frame.pack(pady=20)
        
        ttk.Label(select_frame, text="Select Order:").pack(side='left', padx=5)
        self.doc_order_var = tk.StringVar()
        self.doc_order_combo = ttk.Combobox(
            select_frame,
            textvariable=self.doc_order_var,
            width=30,
            state='readonly'
        )
        self.doc_order_combo.pack(side='left', padx=5)
        
        ttk.Button(select_frame, text="🔄 Refresh Orders", 
                  command=self.refresh_order_list).pack(side='left', padx=5)
        
        # Document buttons
        doc_frame = ttk.Frame(main_frame)
        doc_frame.pack(pady=20)
        
        ttk.Button(doc_frame, text="📋 Generate Packing List", 
                  command=lambda: self.generate_document('packing'),
                  width=30).pack(pady=5)
        
        ttk.Button(doc_frame, text="💰 Generate Invoice", 
                  command=lambda: self.generate_document('invoice'),
                  width=30).pack(pady=5)
        
        ttk.Button(doc_frame, text="📮 Generate Shipping Label", 
                  command=lambda: self.generate_document('label'),
                  width=30).pack(pady=5)
        
        ttk.Button(doc_frame, text="📦 Generate All Documents", 
                  command=lambda: self.generate_document('all'),
                  width=30, style='Action.TButton').pack(pady=15)
        
        # Recent documents
        recent_frame = ttk.LabelFrame(main_frame, text="Recent Documents", padding=10)
        recent_frame.pack(fill='both', expand=True, pady=20, padx=20)
        
        self.recent_docs_list = tk.Listbox(recent_frame, height=8)
        self.recent_docs_list.pack(fill='both', expand=True)
        self.recent_docs_list.bind('<Double-1>', self.open_selected_document)
        
        ttk.Button(recent_frame, text="📂 Open Selected", 
                  command=self.open_selected_document).pack(pady=5)
        
        self.refresh_order_list()
        self.refresh_recent_docs()
    
    def create_settings_tab(self):
        """Create the settings tab."""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text='⚙️ Settings')
        
        # Settings content
        ttk.Label(tab, text="Application Settings", 
                 style='Header.TLabel').pack(pady=20)
        
        settings_frame = ttk.Frame(tab)
        settings_frame.pack(padx=40, pady=20, fill='both', expand=True)
        
        # Etsy API Status
        api_frame = ttk.LabelFrame(settings_frame, text="Etsy API Connection", padding=15)
        api_frame.pack(fill='x', pady=10)
        
        status_text = "✅ Connected" if self.etsy_available else "❌ Not Connected"
        ttk.Label(api_frame, text=f"Status: {status_text}", 
                 font=('Segoe UI', 10, 'bold')).pack(anchor='w')
        
        # Show detailed status message
        ttk.Label(api_frame, text=self.etsy_status['message'],
                 foreground='gray' if not self.etsy_available else 'green').pack(anchor='w', pady=5)
        
        if not self.etsy_available and 'error' in self.etsy_status:
            error_msg = self.etsy_status['error']
            if 'pending approval' in error_msg.lower():
                ttk.Label(api_frame, 
                         text="⏳ Your API key is awaiting approval from Etsy",
                         foreground='orange').pack(anchor='w', pady=2)
            elif 'authentication failed' in error_msg.lower():
                ttk.Label(api_frame, 
                         text="🔑 Check your access token in configuration",
                         foreground='orange').pack(anchor='w', pady=2)
        
        btn_frame = ttk.Frame(api_frame)
        btn_frame.pack(anchor='w', pady=5)
        
        ttk.Button(btn_frame, text="📝 Edit Configuration", 
                  command=self.edit_config).pack(side='left', padx=(0, 5))
        ttk.Button(btn_frame, text="🔄 Test Connection", 
                  command=self.test_etsy_connection).pack(side='left')
        
        # Database info
        db_frame = ttk.LabelFrame(settings_frame, text="Database", padding=15)
        db_frame.pack(fill='x', pady=10)
        
        db = get_db()
        inv_count = db.query(LocalInventory).count()
        order_count = db.query(Order).count()
        db.close()
        
        ttk.Label(db_frame, text=f"Inventory Items: {inv_count}").pack(anchor='w')
        ttk.Label(db_frame, text=f"Orders: {order_count}").pack(anchor='w')
        ttk.Label(db_frame, text=f"Database: etsy_inventory.db").pack(anchor='w')
        
        # Output folder
        output_frame = ttk.LabelFrame(settings_frame, text="Output Folder", padding=15)
        output_frame.pack(fill='x', pady=10)
        
        ttk.Label(output_frame, text=f"Location: {Config.PDF_OUTPUT_DIR}").pack(anchor='w')
        ttk.Button(output_frame, text="📂 Open Output Folder", 
                  command=self.open_output_folder).pack(anchor='w', pady=5)
        
        # About
        about_frame = ttk.LabelFrame(settings_frame, text="About", padding=15)
        about_frame.pack(fill='x', pady=10)
        
        ttk.Label(about_frame, text="Etsy Shop Manager v1.0.0").pack(anchor='w')
        ttk.Label(about_frame, text="Manage inventory, orders, and generate documents").pack(anchor='w')
        ttk.Button(about_frame, text="📖 View Documentation", 
                  command=self.view_docs).pack(anchor='w', pady=5)
    
    # Data loading methods
    def load_inventory(self):
        """Deprecated - redirects to new inventory levels loader."""
        self.load_inventory_levels()
    
    def load_inventory_levels(self):
        """Load current inventory levels from new ItemMaster/Inventory system."""
        # Clear existing items
        for item in self.inventory_tree.get_children():
            self.inventory_tree.delete(item)
        
        # Get category filter
        category = None if self.inv_category_var.get() == "all" else self.inv_category_var.get()
        
        # Load items with inventory
        items = self.inv_manager.list_items(category=category, active_only=True)
        
        # Get quantities on order from pending inbound orders
        from inbound_order_manager import InboundOrderManager
        inbound_mgr = InboundOrderManager()
        pending_orders = inbound_mgr.list_inbound_orders(status='ordered') + \
                        inbound_mgr.list_inbound_orders(status='in_transit')
        
        # Build map of item_id to quantity on order
        qty_on_order_map = {}
        for order in pending_orders:
            order_items = inbound_mgr.get_order_items(order.id)
            for order_item in order_items:
                item_id = order_item['item_id']
                qty_remaining = order_item['quantity_remaining']
                if item_id not in qty_on_order_map:
                    qty_on_order_map[item_id] = 0
                qty_on_order_map[item_id] += qty_remaining
        
        total_value = 0.0
        low_stock_count = 0
        
        for item in items:
            inventory = self.inv_manager.get_item_inventory(item.id)
            
            if not inventory:
                continue
            
            # Get quantity on order for this item
            qty_on_order = qty_on_order_map.get(item.id, 0)
            
            # Determine cost (calculated for kits, base for others)
            unit_cost = item.calculated_cost if item.is_kit else item.base_cost
            unit_cost = unit_cost or 0.0
            
            # Calculate total value
            total_value_item = inventory.quantity_on_hand * unit_cost
            total_value += total_value_item
            
            # Check if low stock
            is_low = inventory.quantity_available <= item.reorder_point
            is_out = inventory.quantity_available <= 0
            
            if is_low:
                low_stock_count += 1
            
            # Determine tags
            tags = ()
            if is_out:
                tags = ('out_of_stock',)
            elif is_low:
                tags = ('low_stock',)
            
            self.inventory_tree.insert('', 'end', iid=str(item.id), values=(
                item.sku,
                item.title,
                item.category or 'N/A',
                inventory.quantity_on_hand,
                qty_on_order,  # NEW: Show quantity on order
                inventory.quantity_reserved,
                inventory.quantity_available,
                item.reorder_point,
                f"${unit_cost:.2f}",
                f"${total_value_item:.2f}",
                item.storage_location or 'N/A'
            ), tags=tags)
        
        inbound_mgr.close()
        
        # Update stats
        self.inv_total_items_label.config(text=f"Items: {len(items)} | Total Value: ${total_value:.2f}")
        self.inv_low_stock_label.config(text=f"Low Stock: {low_stock_count}")
    
    def filter_inventory_levels(self):
        """Filter inventory based on search."""
        search_term = self.inv_search_var.get().lower()
        
        if not search_term:
            # Show all items
            for item in self.inventory_tree.get_children():
                self.inventory_tree.reattach(item, '', 'end')
            return
        
        for item in self.inventory_tree.get_children():
            values = self.inventory_tree.item(item)['values']
            # Search in SKU and title
            if search_term in str(values[0]).lower() or search_term in str(values[1]).lower():
                self.inventory_tree.reattach(item, '', 'end')
            else:
                self.inventory_tree.detach(item)
    
    def show_low_stock_inventory(self):
        """Show only items below reorder point."""
        # Clear existing items
        for item in self.inventory_tree.get_children():
            self.inventory_tree.delete(item)
        
        # Get quantities on order from pending inbound orders
        from inbound_order_manager import InboundOrderManager
        inbound_mgr = InboundOrderManager()
        pending_orders = inbound_mgr.list_inbound_orders(status='ordered') + \
                        inbound_mgr.list_inbound_orders(status='in_transit')
        
        # Build map of item_id to quantity on order
        qty_on_order_map = {}
        for order in pending_orders:
            order_items = inbound_mgr.get_order_items(order.id)
            for order_item in order_items:
                item_id = order_item['item_id']
                qty_remaining = order_item['quantity_remaining']
                if item_id not in qty_on_order_map:
                    qty_on_order_map[item_id] = 0
                qty_on_order_map[item_id] += qty_remaining
        
        # Get items below reorder point
        reorder_list = self.inv_manager.get_items_below_reorder_point()
        
        for item_data in reorder_list:
            item = self.inv_manager.get_item_by_sku(item_data['sku'])
            inventory = self.inv_manager.get_item_inventory(item.id)
            
            # Get quantity on order for this item
            qty_on_order = qty_on_order_map.get(item.id, 0)
            
            unit_cost = item.calculated_cost if item.is_kit else item.base_cost
            unit_cost = unit_cost or 0.0
            total_value_item = inventory.quantity_on_hand * unit_cost
            
            is_out = inventory.quantity_available <= 0
            tags = ('out_of_stock',) if is_out else ('low_stock',)
            
            self.inventory_tree.insert('', 'end', iid=str(item.id), values=(
                item.sku,
                item.title,
                item.category or 'N/A',
                inventory.quantity_on_hand,
                qty_on_order,  # NEW: Show quantity on order
                inventory.quantity_reserved,
                inventory.quantity_available,
                item.reorder_point,
                f"${unit_cost:.2f}",
                f"${total_value_item:.2f}",
                item.storage_location or 'N/A'
            ), tags=tags)
        
        inbound_mgr.close()
        
        # Update stats
        self.inv_total_items_label.config(text=f"Low Stock Items: {len(reorder_list)}")
        self.inv_low_stock_label.config(text=f"Showing: {len(reorder_list)}")
    
    def export_inventory(self):
        """Export current inventory to CSV."""
        from datetime import datetime
        import csv
        
        filename = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            initialfile=f"inventory_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        )
        
        if not filename:
            return
        
        try:
            with open(filename, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                
                # Write header
                writer.writerow(['SKU', 'Title', 'Category', 'On Hand', 'On Order', 'Reserved', 
                               'Available', 'Reorder Point', 'Unit Cost', 'Total Value', 
                               'Location'])
                
                # Write data
                for item in self.inventory_tree.get_children():
                    values = self.inventory_tree.item(item)['values']
                    writer.writerow(values)
            
            messagebox.showinfo("Export Complete", f"Inventory exported to:\n{filename}")
        except Exception as e:
            messagebox.showerror("Export Failed", f"Failed to export inventory:\n{e}")
    
    def load_orders(self):
        """Load orders into treeview."""
        # Clear existing
        for item in self.orders_tree.get_children():
            self.orders_tree.delete(item)
        
        db = get_db()
        query = db.query(Order)
        
        # Apply filter
        if self.order_filter_var.get() != 'All':
            query = query.filter(Order.status == self.order_filter_var.get())
        
        orders = query.all()
        
        for order in orders:
            date_str = order.order_date.strftime('%Y-%m-%d') if order.order_date else 'N/A'
            packed_str = '✅' if order.packed else '❌'
            
            self.orders_tree.insert('', 'end', values=(
                order.id,
                order.etsy_order_id,
                order.buyer_name,
                order.buyer_email,
                f"${order.total_amount:.2f}",
                date_str,
                order.status,
                packed_str
            ))
        
        db.close()
    
    def filter_orders(self):
        """Filter orders based on search."""
        search_term = self.order_search_var.get().lower()
        
        for item in self.orders_tree.get_children():
            values = self.orders_tree.item(item)['values']
            # Search in order ID and customer name
            if search_term in str(values[1]).lower() or search_term in str(values[2]).lower():
                self.orders_tree.reattach(item, '', 'end')
            else:
                self.orders_tree.detach(item)
    
    # Action methods
    def sync_all(self):
        """Sync both inventory and orders from Etsy."""
        if not self.etsy_available:
            messagebox.showwarning("Not Available", "Etsy API not configured")
            return
        
        self.sync_inventory()
        self.sync_orders()
    
    def sync_inventory(self):
        """Sync inventory from Etsy."""
        if not self.etsy_available:
            messagebox.showwarning("Not Available", "Etsy API not configured")
            return
        
        def sync():
            try:
                count = self.inventory_manager.sync_from_etsy()
                self.root.after(0, lambda: messagebox.showinfo("Success", 
                    f"Synced {count} items from Etsy"))
                self.root.after(0, self.load_inventory)
            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror("Error", 
                    f"Failed to sync: {str(e)}"))
        
        threading.Thread(target=sync, daemon=True).start()
        messagebox.showinfo("Syncing", "Syncing inventory from Etsy...")
    
    def sync_orders(self):
        """Sync orders from Etsy."""
        if not self.etsy_available:
            messagebox.showwarning("Not Available", "Etsy API not configured")
            return
        
        def sync():
            try:
                count = self.order_manager.sync_orders_from_etsy()
                self.root.after(0, lambda: messagebox.showinfo("Success", 
                    f"Synced {count} orders from Etsy"))
                self.root.after(0, self.load_orders)
                self.root.after(0, self.refresh_order_list)
            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror("Error", 
                    f"Failed to sync: {str(e)}"))
        
        threading.Thread(target=sync, daemon=True).start()
        messagebox.showinfo("Syncing", "Syncing orders from Etsy...")
    
    def add_order(self):
        """Add a new order manually."""
        dialog = ManualOrderDialog(self.root, self.order_manager, self.inv_manager)
        if dialog.result:
            self.load_orders()
            messagebox.showinfo("Success", f"Order {dialog.result.etsy_order_id} created!")
    
    def mark_order_packed(self):
        """Mark selected order as packed."""
        selection = self.orders_tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select an order")
            return
        
        values = self.orders_tree.item(selection[0])['values']
        order_id = values[0]
        
        try:
            # Use order_manager method which checks inventory
            self.order_manager.mark_order_packed(order_id)
            
            db = get_db()
            order = db.query(Order).filter(Order.id == order_id).first()
            db.close()
            
            messagebox.showinfo("Success", f"Order {order.etsy_order_id} marked as packed!\n\nInventory has been deducted.")
            self.load_orders()
            
        except ValueError as e:
            # Insufficient inventory error
            messagebox.showerror("Insufficient Inventory", str(e))
        except Exception as e:
            messagebox.showerror("Error", f"Failed to mark order as packed:\n{str(e)}")
    
    def unpack_order(self):
        """Unpack an order and restore inventory."""
        selection = self.orders_tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select an order")
            return
        
        values = self.orders_tree.item(selection[0])['values']
        order_id = values[0]
        
        db = get_db()
        order = db.query(Order).filter(Order.id == order_id).first()
        
        if not order:
            db.close()
            messagebox.showerror("Error", "Order not found")
            return
        
        if not order.packed:
            db.close()
            messagebox.showwarning("Not Packed", "This order is not marked as packed")
            return
        
        if order.status == 'shipped':
            db.close()
            messagebox.showwarning("Already Shipped", "Cannot unpack an order that has been shipped")
            return
        
        # Confirm unpacking
        if not messagebox.askyesno("Confirm Unpack", 
                                   f"Unpack order {order.etsy_order_id}?\n\n"
                                   "This will restore the inventory that was deducted."):
            db.close()
            return
        
        try:
            from database import ItemMaster, Inventory, InventoryTransaction, OrderItem
            
            # Get order items
            order_items = db.query(OrderItem).filter(OrderItem.order_id == order_id).all()
            
            # Restore inventory for each item
            for order_item in order_items:
                if not order_item.sku:
                    continue
                
                # Find the item in ItemMaster
                item = db.query(ItemMaster).filter(ItemMaster.sku == order_item.sku).first()
                if not item:
                    continue
                
                # Restore inventory
                inventory = db.query(Inventory).filter(Inventory.item_id == item.id).first()
                if inventory:
                    inventory.quantity_on_hand += order_item.quantity
                    inventory.quantity_available = inventory.quantity_on_hand - (inventory.quantity_reserved or 0)
                    
                    # Create inventory transaction
                    transaction = InventoryTransaction(
                        item_id=item.id,
                        transaction_type='adjustment',
                        quantity=order_item.quantity,
                        reference_type='order_unpack',
                        reference_id=str(order.etsy_order_id),
                        notes=f"Order unpacked: {order.etsy_order_id}"
                    )
                    db.add(transaction)
            
            # Mark order as unpacked
            order.packed = False
            order.status = 'pending'
            db.commit()
            
            messagebox.showinfo("Success", f"Order {order.etsy_order_id} has been unpacked!\n\nInventory has been restored.")
            self.load_orders()
            
        except Exception as e:
            db.rollback()
            messagebox.showerror("Error", f"Failed to unpack order:\n{str(e)}")
        finally:
            db.close()
    
    def add_tracking(self):
        """Add tracking number to selected order."""
        selection = self.orders_tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select an order")
            return
        
        values = self.orders_tree.item(selection[0])['values']
        order_id = values[0]
        
        # Check if order is packed first
        db = get_db()
        order = db.query(Order).filter(Order.id == order_id).first()
        
        if not order:
            db.close()
            messagebox.showerror("Error", "Order not found")
            return
        
        if not order.packed:
            db.close()
            messagebox.showwarning("Order Not Packed", 
                                 "Please mark the order as packed before adding tracking information.")
            return
        
        db.close()
        
        # Create dialog
        dialog = tk.Toplevel(self.root)
        dialog.title("Add Tracking Number")
        dialog.geometry("400x150")
        dialog.transient(self.root)
        dialog.grab_set()
        
        ttk.Label(dialog, text="Tracking Number:").pack(pady=10)
        tracking_entry = ttk.Entry(dialog, width=40)
        tracking_entry.pack(pady=5)
        
        ttk.Label(dialog, text="Carrier:").pack(pady=5)
        carrier_var = tk.StringVar(value="USPS")
        carrier_combo = ttk.Combobox(dialog, textvariable=carrier_var, 
                                    values=['USPS', 'UPS', 'FedEx', 'DHL'],
                                    width=37, state='readonly')
        carrier_combo.pack(pady=5)
        
        def save():
            tracking = tracking_entry.get()
            if not tracking:
                messagebox.showwarning("Missing Data", "Please enter a tracking number")
                return
            
            db = get_db()
            order = db.query(Order).filter(Order.id == order_id).first()
            
            if order:
                order.tracking_number = tracking
                order.status = 'shipped'
                db.commit()
                
                # Try to update Etsy if available
                if self.etsy_available and self.order_manager:
                    try:
                        self.order_manager.update_tracking(order_id, tracking, carrier_var.get())
                    except:
                        pass
                
                messagebox.showinfo("Success", "Tracking number added!")
                dialog.destroy()
                self.load_orders()
            
            db.close()
        
        ttk.Button(dialog, text="Save", command=save).pack(pady=10)
    
    def cancel_order(self):
        """Cancel an order and restore inventory if it was packed."""
        selection = self.orders_tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select an order")
            return
        
        values = self.orders_tree.item(selection[0])['values']
        order_id = values[0]
        
        db = get_db()
        order = db.query(Order).filter(Order.id == order_id).first()
        
        if not order:
            db.close()
            messagebox.showerror("Error", "Order not found")
            return
        
        if order.status == 'shipped':
            db.close()
            messagebox.showwarning("Already Shipped", "Cannot cancel an order that has been shipped")
            return
        
        if order.status == 'cancelled':
            db.close()
            messagebox.showinfo("Already Cancelled", "This order is already cancelled")
            return
        
        # Confirm cancellation
        cancel_msg = f"Cancel order {order.etsy_order_id}?"
        if order.packed:
            cancel_msg += "\n\nThis order is packed. Inventory will be restored."
        
        if not messagebox.askyesno("Confirm Cancellation", cancel_msg):
            db.close()
            return
        
        try:
            from database import ItemMaster, Inventory, InventoryTransaction, OrderItem
            
            # If order was packed, restore inventory
            if order.packed:
                order_items = db.query(OrderItem).filter(OrderItem.order_id == order_id).all()
                
                for order_item in order_items:
                    if not order_item.sku:
                        continue
                    
                    # Find the item in ItemMaster
                    item = db.query(ItemMaster).filter(ItemMaster.sku == order_item.sku).first()
                    if not item:
                        continue
                    
                    # Restore inventory
                    inventory = db.query(Inventory).filter(Inventory.item_id == item.id).first()
                    if inventory:
                        inventory.quantity_on_hand += order_item.quantity
                        inventory.quantity_available = inventory.quantity_on_hand - (inventory.quantity_reserved or 0)
                        
                        # Create inventory transaction
                        transaction = InventoryTransaction(
                            item_id=item.id,
                            transaction_type='adjustment',
                            quantity=order_item.quantity,
                            reference_type='order_cancel',
                            reference_id=str(order.etsy_order_id),
                            notes=f"Order cancelled: {order.etsy_order_id}"
                        )
                        db.add(transaction)
            
            # Mark order as cancelled
            order.status = 'cancelled'
            order.packed = False
            db.commit()
            
            success_msg = f"Order {order.etsy_order_id} has been cancelled"
            if order.packed:
                success_msg += " and inventory has been restored"
            success_msg += "."
            
            messagebox.showinfo("Success", success_msg)
            self.load_orders()
            
        except Exception as e:
            db.rollback()
            messagebox.showerror("Error", f"Failed to cancel order:\n{str(e)}")
        finally:
            db.close()
    
    def view_order_details(self):
        """View detailed order information."""
        selection = self.orders_tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select an order")
            return
        
        values = self.orders_tree.item(selection[0])['values']
        order_id = values[0]
        
        db = get_db()
        order = db.query(Order).filter(Order.id == order_id).first()
        
        if not order:
            messagebox.showerror("Error", "Order not found")
            db.close()
            return
        
        # Create details window
        dialog = tk.Toplevel(self.root)
        dialog.title(f"Order Details - {order.etsy_order_id}")
        dialog.geometry("600x500")
        dialog.transient(self.root)
        
        # Order info
        info_frame = ttk.LabelFrame(dialog, text="Order Information", padding=15)
        info_frame.pack(fill='x', padx=10, pady=10)
        
        ttk.Label(info_frame, text=f"Order ID: {order.etsy_order_id}").pack(anchor='w')
        ttk.Label(info_frame, text=f"Customer: {order.buyer_name}").pack(anchor='w')
        ttk.Label(info_frame, text=f"Email: {order.buyer_email}").pack(anchor='w')
        ttk.Label(info_frame, text=f"Status: {order.status}").pack(anchor='w')
        ttk.Label(info_frame, text=f"Amount: ${order.total_amount:.2f}").pack(anchor='w')
        ttk.Label(info_frame, text=f"Tracking: {order.tracking_number or 'N/A'}").pack(anchor='w')
        
        # Address
        addr_frame = ttk.LabelFrame(dialog, text="Shipping Address", padding=15)
        addr_frame.pack(fill='x', padx=10, pady=10)
        
        addr_text = tk.Text(addr_frame, height=4, width=60)
        addr_text.insert('1.0', order.shipping_address)
        addr_text.config(state='disabled')
        addr_text.pack()
        
        # Items
        items_frame = ttk.LabelFrame(dialog, text="Order Items", padding=15)
        items_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        items = db.query(OrderItem).filter(OrderItem.order_id == order_id).all()
        
        for item in items:
            item_text = f"• {item.title} (SKU: {item.sku}) - Qty: {item.quantity} @ ${item.price:.2f}"
            ttk.Label(items_frame, text=item_text).pack(anchor='w', pady=2)
        
        db.close()
    
    def refresh_order_list(self):
        """Refresh the order list in document tab."""
        db = get_db()
        # Exclude cancelled orders from the dropdown
        orders = db.query(Order).filter(Order.status != 'cancelled').all()
        
        order_list = [f"{o.id} - {o.etsy_order_id} - {o.buyer_name}" for o in orders]
        self.doc_order_combo['values'] = order_list
        
        if order_list:
            self.doc_order_combo.current(0)
        
        db.close()
    
    def generate_document(self, doc_type):
        """Generate document for selected order."""
        if not self.doc_order_var.get():
            messagebox.showwarning("No Selection", "Please select an order")
            return
        
        # Extract order ID from combo value
        order_id = int(self.doc_order_var.get().split(' - ')[0])
        
        db = get_db()
        order = db.query(Order).filter(Order.id == order_id).first()
        
        if not order:
            messagebox.showerror("Error", "Order not found")
            db.close()
            return
        
        # Check if order is cancelled
        if order.status == 'cancelled':
            messagebox.showwarning("Cancelled Order", 
                                 "Cannot generate documents for cancelled orders.")
            db.close()
            return
        
        try:
            if doc_type in ['packing', 'all']:
                items = db.query(OrderItem).filter(OrderItem.order_id == order_id).all()
                items_data = [{
                    'sku': item.sku,
                    'title': item.title,
                    'quantity': item.quantity,
                    'location': 'N/A'
                } for item in items]
                
                # Get locations from inventory
                for item_data in items_data:
                    inv_item = db.query(LocalInventory).filter(
                        LocalInventory.sku == item_data['sku']
                    ).first()
                    if inv_item and inv_item.location:
                        item_data['location'] = inv_item.location
                
                order_data = {
                    'order_id': order.etsy_order_id,
                    'order_date': order.order_date.strftime('%Y-%m-%d') if order.order_date else 'N/A',
                    'buyer_name': order.buyer_name,
                    'shipping_address': order.shipping_address
                }
                
                pdf_path = self.doc_generator.generate_packing_list(order_data, items_data)
                messagebox.showinfo("Success", f"Packing list generated:\n{pdf_path}")
            
            if doc_type in ['invoice', 'all']:
                items = db.query(OrderItem).filter(OrderItem.order_id == order_id).all()
                items_data = [{
                    'sku': item.sku,
                    'title': item.title,
                    'quantity': item.quantity,
                    'price': item.price
                } for item in items]
                
                order_data = {
                    'order_id': order.etsy_order_id,
                    'order_date': order.order_date.strftime('%Y-%m-%d') if order.order_date else 'N/A',
                    'buyer_name': order.buyer_name,
                    'buyer_email': order.buyer_email,
                    'total_amount': order.total_amount,
                    'status': order.status
                }
                
                shop_info = {'shop_name': 'Your Shop', 'address': 'Your Address'}
                pdf_path = self.doc_generator.generate_invoice(order_data, items_data, shop_info)
                messagebox.showinfo("Success", f"Invoice generated:\n{pdf_path}")
                
                order.invoice_generated = True
                db.commit()
            
            if doc_type in ['label', 'all']:
                order_data = {
                    'order_id': order.etsy_order_id,
                    'buyer_name': order.buyer_name,
                    'shipping_address': order.shipping_address,
                    'tracking_number': order.tracking_number or 'N/A',
                    'shop_name': 'Your Shop',
                    'shop_address': 'Your Address'
                }
                
                pdf_path = self.doc_generator.generate_shipping_label(order_data)
                messagebox.showinfo("Success", f"Shipping label generated:\n{pdf_path}")
                
                order.label_generated = True
                db.commit()
            
            self.refresh_recent_docs()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to generate document: {str(e)}")
        
        db.close()
    
    def refresh_recent_docs(self):
        """Refresh recent documents list."""
        self.recent_docs_list.delete(0, tk.END)
        
        output_dir = Path(Config.PDF_OUTPUT_DIR)
        if output_dir.exists():
            files = sorted(output_dir.glob('*.pdf'), key=lambda x: x.stat().st_mtime, reverse=True)
            for f in files[:10]:  # Show last 10
                self.recent_docs_list.insert(tk.END, f.name)
    
    def open_selected_document(self, event=None):
        """Open selected document from recent list."""
        selection = self.recent_docs_list.curselection()
        if selection:
            filename = self.recent_docs_list.get(selection[0])
            filepath = Path(Config.PDF_OUTPUT_DIR) / filename
            if filepath.exists():
                os.startfile(str(filepath))
    
    def open_output_folder(self):
        """Open the output folder."""
        output_dir = Path(Config.PDF_OUTPUT_DIR)
        if output_dir.exists():
            os.startfile(str(output_dir))
        else:
            messagebox.showwarning("Not Found", "Output folder doesn't exist yet")
    
    def edit_config(self):
        """Open settings dialog for editing configuration."""
        show_settings_dialog(self.root, callback=self.on_settings_saved)
    
    def on_settings_saved(self):
        """Callback when settings are saved."""
        messagebox.showinfo("Settings Saved", 
                          "Settings have been saved to Windows Registry.\n\n"
                          "Please restart the application for changes to take effect.")
    
    def test_etsy_connection(self):
        """Test the Etsy API connection."""
        messagebox.showinfo("Testing Connection", "Testing Etsy API connection...")
        
        status = self.check_etsy_connection()
        
        if status['available']:
            shop_name = status.get('shop_data', {}).get('shop_name', 'Unknown')
            messagebox.showinfo("Connection Successful", 
                              f"✅ Successfully connected to Etsy!\n\n"
                              f"Shop: {shop_name}\n\n"
                              f"All sync features are available.")
        else:
            error_msg = status.get('error', 'Unknown error')
            message = f"❌ Connection Failed\n\n{status['message']}\n\n"
            
            if 'pending approval' in error_msg.lower() or status['message'].find('not approved') != -1:
                message += "Your API key is awaiting approval from Etsy.\n"
                message += "Check your email or Etsy Developer Dashboard for approval status."
            elif 'authentication failed' in error_msg.lower():
                message += "Your access token may be invalid or expired.\n"
                message += "Please update it in Edit Configuration."
            elif 'not configured' in status['message'].lower():
                message += "Please configure your Etsy API credentials in Edit Configuration."
            else:
                message += f"Error: {error_msg}"
            
            messagebox.showerror("Connection Failed", message)
    
    
    def view_docs(self):
        """Open README documentation."""
        readme = Path('README.md')
        if readme.exists():
            os.startfile(str(readme))
        else:
            messagebox.showwarning("Not Found", "README.md not found")
    
    def show_help(self):
        """Show help dialog."""
        help_text = """
Etsy Shop Manager - Quick Help

INVENTORY TAB:
• Add, edit, and view your inventory items
• Track quantities, prices, costs, and locations
• Set low stock alerts
• Sync with Etsy (when API configured)

ORDERS TAB:
• View and manage orders
• Mark orders as packed
• Add tracking numbers
• Filter by status

DOCUMENTS TAB:
• Generate packing lists
• Create invoices
• Generate shipping labels
• View recent documents

For detailed help, see README.md
        """
        messagebox.showinfo("Help", help_text)


class PriceDialog(tk.Toplevel):
    """Simple dialog for entering a price."""
    
    def __init__(self, parent, title, prompt, initial_value="0"):
        super().__init__(parent)
        self.result = None
        
        self.title(title)
        self.geometry("350x150")
        self.transient(parent)
        self.grab_set()
        
        # Center on parent
        self.update_idletasks()
        parent_x = parent.winfo_x()
        parent_y = parent.winfo_y()
        parent_width = parent.winfo_width()
        parent_height = parent.winfo_height()
        dialog_width = self.winfo_width()
        dialog_height = self.winfo_height()
        x = parent_x + (parent_width - dialog_width) // 2
        y = parent_y + (parent_height - dialog_height) // 2
        self.geometry(f"+{x}+{y}")
        
        # Prompt
        ttk.Label(self, text=prompt, padding=10).pack()
        
        # Entry
        self.entry = ttk.Entry(self, width=30)
        self.entry.insert(0, initial_value)
        self.entry.pack(pady=10)
        self.entry.select_range(0, tk.END)
        self.entry.focus()
        
        # Buttons
        btn_frame = ttk.Frame(self)
        btn_frame.pack(pady=10)
        ttk.Button(btn_frame, text="OK", command=self.ok, width=10).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Cancel", command=self.cancel, width=10).pack(side=tk.LEFT, padx=5)
        
        # Bind Enter key
        self.entry.bind('<Return>', lambda e: self.ok())
        self.bind('<Escape>', lambda e: self.cancel())
        
        self.wait_window()
    
    def ok(self):
        self.result = self.entry.get()
        self.destroy()
    
    def cancel(self):
        self.result = None
        self.destroy()


class CustomerSearchDialog(tk.Toplevel):
    """Dialog for searching and selecting customers."""
    
    def __init__(self, parent, customer_manager):
        super().__init__(parent)
        self.customer_manager = customer_manager
        self.result = None
        
        self.title("Search Customers")
        self.geometry("700x500")
        self.transient(parent)
        self.grab_set()
        
        # Center on parent
        self.update_idletasks()
        parent_x = parent.winfo_x()
        parent_y = parent.winfo_y()
        parent_width = parent.winfo_width()
        parent_height = parent.winfo_height()
        dialog_width = self.winfo_width()
        dialog_height = self.winfo_height()
        x = parent_x + (parent_width - dialog_width) // 2
        y = parent_y + (parent_height - dialog_height) // 2
        self.geometry(f"+{x}+{y}")
        
        self.create_widgets()
        self.wait_window()
    
    def create_widgets(self):
        """Create dialog widgets."""
        # Search frame
        search_frame = ttk.Frame(self, padding=10)
        search_frame.pack(fill=tk.X)
        
        ttk.Label(search_frame, text="Search:").pack(side=tk.LEFT)
        self.search_var = tk.StringVar()
        search_entry = ttk.Entry(search_frame, textvariable=self.search_var, width=30)
        search_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        ttk.Button(search_frame, text="🔍 Search", command=self.do_search).pack(side=tk.LEFT, padx=5)
        ttk.Button(search_frame, text="➕ New Customer", command=self.create_new_customer).pack(side=tk.LEFT)
        
        # Bind Enter key to search
        search_entry.bind('<Return>', lambda e: self.do_search())
        search_entry.focus()
        
        # Results tree
        results_frame = ttk.Frame(self)
        results_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        scrollbar = ttk.Scrollbar(results_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.tree = ttk.Treeview(results_frame,
                                columns=("Name", "Email", "City", "State"),
                                show="headings",
                                yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.tree.yview)
        
        self.tree.heading("Name", text="Name")
        self.tree.heading("Email", text="Email")
        self.tree.heading("City", text="City")
        self.tree.heading("State", text="State")
        
        self.tree.column("Name", width=200)
        self.tree.column("Email", width=200)
        self.tree.column("City", width=120)
        self.tree.column("State", width=80)
        
        self.tree.pack(fill=tk.BOTH, expand=True)
        self.tree.bind('<Double-Button-1>', lambda e: self.select_customer())
        
        # Buttons
        btn_frame = ttk.Frame(self)
        btn_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Button(btn_frame, text="Select", command=self.select_customer, width=12).pack(side=tk.RIGHT, padx=5)
        ttk.Button(btn_frame, text="Cancel", command=self.cancel, width=12).pack(side=tk.RIGHT)
        
        # Load all customers initially
        self.load_all_customers()
    
    def load_all_customers(self):
        """Load all active customers."""
        from database import get_db
        db = get_db()
        try:
            customers = self.customer_manager.get_all_customers(db=db)
            self.display_customers(customers)
        finally:
            db.close()
    
    def do_search(self):
        """Perform customer search."""
        search_term = self.search_var.get().strip()
        if not search_term:
            self.load_all_customers()
            return
        
        from database import get_db
        db = get_db()
        try:
            customers = self.customer_manager.search_customers(search_term, db=db)
            self.display_customers(customers)
            
            if not customers:
                messagebox.showinfo("No Results", f"No customers found matching '{search_term}'")
        finally:
            db.close()
    
    def display_customers(self, customers):
        """Display customers in tree."""
        self.tree.delete(*self.tree.get_children())
        
        for customer in customers:
            self.tree.insert("", tk.END, iid=str(customer.id), values=(
                customer.name,
                customer.email or '',
                customer.city or '',
                customer.state or ''
            ))
    
    def select_customer(self):
        """Select the highlighted customer."""
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a customer")
            return
        
        customer_id = int(selection[0])
        from database import get_db
        db = get_db()
        try:
            self.result = self.customer_manager.get_customer(customer_id, db=db)
            self.destroy()
        finally:
            db.close()
    
    def create_new_customer(self):
        """Create a new customer."""
        new_customer_dialog = NewCustomerDialog(self, self.customer_manager)
        if new_customer_dialog.result:
            self.result = new_customer_dialog.result
            self.destroy()
    
    def cancel(self):
        """Cancel selection."""
        self.result = None
        self.destroy()


class NewCustomerDialog(tk.Toplevel):
    """Dialog for creating a new customer."""
    
    def __init__(self, parent, customer_manager):
        super().__init__(parent)
        self.customer_manager = customer_manager
        self.result = None
        
        self.title("New Customer")
        self.geometry("500x550")
        self.transient(parent)
        self.grab_set()
        
        # Center on parent
        self.update_idletasks()
        parent_x = parent.winfo_x()
        parent_y = parent.winfo_y()
        parent_width = parent.winfo_width()
        parent_height = parent.winfo_height()
        dialog_width = self.winfo_width()
        dialog_height = self.winfo_height()
        x = parent_x + (parent_width - dialog_width) // 2
        y = parent_y + (parent_height - dialog_height) // 2
        self.geometry(f"+{x}+{y}")
        
        self.create_widgets()
        self.wait_window()
    
    def create_widgets(self):
        """Create dialog widgets."""
        form_frame = ttk.Frame(self, padding=10)
        form_frame.pack(fill=tk.BOTH, expand=True)
        
        row = 0
        ttk.Label(form_frame, text="Name:*").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.name_var = tk.StringVar()
        ttk.Entry(form_frame, textvariable=self.name_var, width=40).grid(row=row, column=1, sticky=tk.EW, pady=5)
        
        row += 1
        ttk.Label(form_frame, text="Email:").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.email_var = tk.StringVar()
        ttk.Entry(form_frame, textvariable=self.email_var, width=40).grid(row=row, column=1, sticky=tk.EW, pady=5)
        
        row += 1
        ttk.Label(form_frame, text="Phone:").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.phone_var = tk.StringVar()
        ttk.Entry(form_frame, textvariable=self.phone_var, width=40).grid(row=row, column=1, sticky=tk.EW, pady=5)
        
        row += 1
        ttk.Label(form_frame, text="Address Line 1:").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.addr1_var = tk.StringVar()
        ttk.Entry(form_frame, textvariable=self.addr1_var, width=40).grid(row=row, column=1, sticky=tk.EW, pady=5)
        
        row += 1
        ttk.Label(form_frame, text="Address Line 2:").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.addr2_var = tk.StringVar()
        ttk.Entry(form_frame, textvariable=self.addr2_var, width=40).grid(row=row, column=1, sticky=tk.EW, pady=5)
        
        row += 1
        ttk.Label(form_frame, text="City:").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.city_var = tk.StringVar()
        ttk.Entry(form_frame, textvariable=self.city_var, width=40).grid(row=row, column=1, sticky=tk.EW, pady=5)
        
        row += 1
        ttk.Label(form_frame, text="State:").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.state_var = tk.StringVar()
        ttk.Entry(form_frame, textvariable=self.state_var, width=10).grid(row=row, column=1, sticky=tk.W, pady=5)
        
        row += 1
        ttk.Label(form_frame, text="Postal Code:").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.postal_var = tk.StringVar()
        ttk.Entry(form_frame, textvariable=self.postal_var, width=15).grid(row=row, column=1, sticky=tk.W, pady=5)
        
        row += 1
        ttk.Label(form_frame, text="Country:").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.country_var = tk.StringVar(value="US")
        ttk.Entry(form_frame, textvariable=self.country_var, width=10).grid(row=row, column=1, sticky=tk.W, pady=5)
        
        row += 1
        ttk.Label(form_frame, text="Notes:").grid(row=row, column=0, sticky=tk.NW, pady=5)
        self.notes_text = tk.Text(form_frame, height=4, width=40)
        self.notes_text.grid(row=row, column=1, sticky=tk.EW, pady=5)
        
        form_frame.columnconfigure(1, weight=1)
        
        # Buttons
        btn_frame = ttk.Frame(self)
        btn_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Button(btn_frame, text="Create", command=self.save_customer, width=12).pack(side=tk.RIGHT, padx=5)
        ttk.Button(btn_frame, text="Cancel", command=self.cancel, width=12).pack(side=tk.RIGHT)
    
    def save_customer(self):
        """Save the new customer."""
        name = self.name_var.get().strip()
        if not name:
            messagebox.showerror("Validation Error", "Name is required")
            return
        
        from database import get_db
        db = get_db()
        try:
            self.result = self.customer_manager.create_customer(
                name=name,
                email=self.email_var.get().strip() or None,
                phone=self.phone_var.get().strip() or None,
                address_line1=self.addr1_var.get().strip() or None,
                address_line2=self.addr2_var.get().strip() or None,
                city=self.city_var.get().strip() or None,
                state=self.state_var.get().strip() or None,
                postal_code=self.postal_var.get().strip() or None,
                country=self.country_var.get().strip() or 'US',
                notes=self.notes_text.get(1.0, tk.END).strip() or None,
                db=db
            )
            messagebox.showinfo("Success", "Customer created successfully!")
            self.destroy()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to create customer: {e}")
        finally:
            db.close()
    
    def cancel(self):
        """Cancel creation."""
        self.result = None
        self.destroy()


class ManualOrderDialog(tk.Toplevel):
    """Dialog for manually creating an order."""
    
    def __init__(self, parent, order_manager, item_manager):
        super().__init__(parent)
        self.order_manager = order_manager
        self.item_manager = item_manager
        from customer_manager import CustomerManager
        self.customer_manager = CustomerManager()
        self.result = None
        self.items = []
        self.selected_customer = None
        
        self.title("Create Manual Order")
        self.geometry("850x750")
        self.transient(parent)
        self.grab_set()
        
        # Center on parent
        self.update_idletasks()
        parent_x = parent.winfo_x()
        parent_y = parent.winfo_y()
        parent_width = parent.winfo_width()
        parent_height = parent.winfo_height()
        dialog_width = self.winfo_width()
        dialog_height = self.winfo_height()
        x = parent_x + (parent_width - dialog_width) // 2
        y = parent_y + (parent_height - dialog_height) // 2
        self.geometry(f"+{x}+{y}")
        
        self.create_widgets()
        self.wait_window()
    
    def create_widgets(self):
        """Create dialog widgets."""
        # Customer Info Section
        info_frame = ttk.LabelFrame(self, text="Customer Information", padding=10)
        info_frame.pack(fill=tk.X, padx=10, pady=10)
        
        row = 0
        ttk.Label(info_frame, text="Order ID:*").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.order_id_var = tk.StringVar(value=f"MANUAL-{datetime.now().strftime('%Y%m%d-%H%M%S')}")
        ttk.Entry(info_frame, textvariable=self.order_id_var, width=40).grid(row=row, column=1, sticky=tk.EW, pady=5, columnspan=2)
        
        row += 1
        ttk.Label(info_frame, text="Customer Name:*").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.name_var = tk.StringVar()
        ttk.Entry(info_frame, textvariable=self.name_var, width=30).grid(row=row, column=1, sticky=tk.EW, pady=5)
        ttk.Button(info_frame, text="🔍 Search", command=self.search_customer, width=10).grid(row=row, column=2, sticky=tk.W, pady=5, padx=5)
        
        row += 1
        ttk.Label(info_frame, text="Email:").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.email_var = tk.StringVar()
        ttk.Entry(info_frame, textvariable=self.email_var, width=40).grid(row=row, column=1, sticky=tk.EW, pady=5, columnspan=2)
        
        row += 1
        ttk.Label(info_frame, text="Shipping Address:*").grid(row=row, column=0, sticky=tk.NW, pady=5)
        self.address_text = tk.Text(info_frame, height=4, width=40)
        self.address_text.grid(row=row, column=1, sticky=tk.EW, pady=5, columnspan=2)
        
        row += 1
        ttk.Label(info_frame, text="Order Date:").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.date_var = tk.StringVar(value=datetime.now().strftime("%Y-%m-%d"))
        ttk.Entry(info_frame, textvariable=self.date_var, width=20).grid(row=row, column=1, sticky=tk.W, pady=5)
        
        info_frame.columnconfigure(1, weight=1)
        
        # Items Section
        items_frame = ttk.LabelFrame(self, text="Order Items", padding=10)
        items_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        toolbar = ttk.Frame(items_frame)
        toolbar.pack(fill=tk.X)
        
        ttk.Button(toolbar, text="➕ Add Item", command=self.add_item).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="❌ Remove", command=self.remove_item).pack(side=tk.LEFT, padx=2)
        
        self.total_label = ttk.Label(toolbar, text="Total: $0.00", font=("Arial", 12, "bold"))
        self.total_label.pack(side=tk.RIGHT, padx=10)
        
        # Items tree
        tree_frame = ttk.Frame(items_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        scrollbar = ttk.Scrollbar(tree_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.items_tree = ttk.Treeview(tree_frame,
                                      columns=("SKU", "Title", "Qty", "Price", "Total"),
                                      show="headings",
                                      yscrollcommand=scrollbar.set,
                                      height=8)
        scrollbar.config(command=self.items_tree.yview)
        
        self.items_tree.heading("SKU", text="SKU")
        self.items_tree.heading("Title", text="Title")
        self.items_tree.heading("Qty", text="Quantity")
        self.items_tree.heading("Price", text="Price")
        self.items_tree.heading("Total", text="Total")
        
        self.items_tree.column("SKU", width=100)
        self.items_tree.column("Title", width=300)
        self.items_tree.column("Qty", width=70)
        self.items_tree.column("Price", width=80)
        self.items_tree.column("Total", width=80)
        
        self.items_tree.pack(fill=tk.BOTH, expand=True)
        
        # Buttons
        btn_frame = ttk.Frame(self, padding=10)
        btn_frame.pack(side=tk.BOTTOM, fill=tk.X)
        
        ttk.Button(btn_frame, text="Create Order", command=self.save_order, width=15).pack(side=tk.RIGHT, padx=5)
        ttk.Button(btn_frame, text="Cancel", command=self.destroy, width=12).pack(side=tk.RIGHT)
    
    def add_item(self):
        """Add item to order."""
        from item_master_tab import ComponentPickerDialog
        dialog = ComponentPickerDialog(self, self.item_manager)
        if dialog.result:
            # Get price
            item = self.item_manager.get_item_by_sku(dialog.result['sku'])
            initial_price = str(item.sell_price or item.calculated_cost or item.base_cost or 0)
            
            price_dialog = PriceDialog(self, "Item Price", 
                                      f"Price for {dialog.result['sku']}:",
                                      initial_price)
            
            if price_dialog.result:
                try:
                    price = float(price_dialog.result)
                    self.items.append({
                        'sku': dialog.result['sku'],
                        'title': dialog.result['title'],
                        'quantity': int(dialog.result['quantity']),
                        'price': price
                    })
                    self.refresh_items()
                except:
                    messagebox.showerror("Error", "Invalid price")
    
    def remove_item(self):
        """Remove selected item."""
        selection = self.items_tree.selection()
        if selection:
            index = int(selection[0])
            del self.items[index]
            self.refresh_items()
    
    def refresh_items(self):
        """Refresh items tree."""
        for item in self.items_tree.get_children():
            self.items_tree.delete(item)
        
        total = 0.0
        for i, item in enumerate(self.items):
            item_total = item['quantity'] * item['price']
            total += item_total
            
            self.items_tree.insert("", tk.END, iid=str(i), values=(
                item['sku'],
                item['title'],
                item['quantity'],
                f"${item['price']:.2f}",
                f"${item_total:.2f}"
            ))
        
        self.total_label.config(text=f"Total: ${total:.2f}")
    
    def search_customer(self):
        """Search for existing customers."""
        search_dialog = CustomerSearchDialog(self, self.customer_manager)
        if search_dialog.result:
            customer = search_dialog.result
            self.selected_customer = customer
            
            # Fill in customer information
            self.name_var.set(customer.name)
            self.email_var.set(customer.email or '')
            
            # Fill in address
            self.address_text.delete(1.0, tk.END)
            address = self.customer_manager.get_customer_formatted_address(customer)
            self.address_text.insert(1.0, address)
    
    def save_order(self):
        """Save the manual order."""
        if not self.order_id_var.get() or not self.name_var.get():
            messagebox.showerror("Validation Error", "Order ID and Customer Name are required")
            return
        
        address = self.address_text.get(1.0, tk.END).strip()
        if not address:
            messagebox.showerror("Validation Error", "Shipping address is required")
            return
        
        if not self.items:
            messagebox.showerror("Validation Error", "Order must have at least one item")
            return
        
        try:
            order_date = datetime.strptime(self.date_var.get(), "%Y-%m-%d")
        except:
            messagebox.showerror("Error", "Invalid date format (use YYYY-MM-DD)")
            return
        
        # Calculate total
        total_amount = sum(item['quantity'] * item['price'] for item in self.items)
        
        # Get or create customer
        customer_id = None
        if self.selected_customer:
            customer_id = self.selected_customer.id
        else:
            # Create a new customer from the entered data
            try:
                from database import get_db
                db = get_db()
                customer = self.customer_manager.create_customer(
                    name=self.name_var.get(),
                    email=self.email_var.get().strip() or None,
                    address_line1=address,  # Store full address for now
                    db=db
                )
                customer_id = customer.id
                db.close()
            except Exception as e:
                print(f"Warning: Could not create customer record: {e}")
        
        try:
            # Create order
            self.result = self.order_manager.create_manual_order(
                order_id=self.order_id_var.get(),
                buyer_name=self.name_var.get(),
                buyer_email=self.email_var.get() or None,
                shipping_address=address,
                total_amount=total_amount,
                order_date=order_date,
                customer_id=customer_id,
                items=self.items
            )
            self.destroy()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to create order: {e}")


def main():
    """Main entry point for GUI application."""
    root = tk.Tk()
    app = EtsyAppGUI(root)
    root.mainloop()

if __name__ == '__main__':
    main()
