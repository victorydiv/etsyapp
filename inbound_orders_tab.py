"""Inbound Orders (Purchase Orders) GUI tab."""
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from datetime import datetime
from inbound_order_manager import InboundOrderManager
from item_master_manager import ItemMasterManager


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


class InboundOrdersTab:
    """GUI tab for managing inbound orders (purchase orders)."""
    
    def __init__(self, parent_frame, app):
        self.frame = parent_frame
        self.app = app
        self.manager = InboundOrderManager()
        self.item_manager = ItemMasterManager()
        
        self.setup_ui()
        self.load_orders()
    
    def setup_ui(self):
        """Set up UI components."""
        # Toolbar
        toolbar = ttk.Frame(self.frame)
        toolbar.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)
        
        ttk.Button(toolbar, text="➕ New PO", 
                  command=self.create_po).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="📦 Receive", 
                  command=self.receive_order).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="✏️ Edit", 
                  command=self.edit_order).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="❌ Cancel PO", 
                  command=self.cancel_order).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="🔄 Refresh", 
                  command=self.load_orders).pack(side=tk.LEFT, padx=2)
        
        # Filter
        ttk.Label(toolbar, text="Status:").pack(side=tk.LEFT, padx=(20, 2))
        self.status_var = tk.StringVar(value="all")
        status_combo = ttk.Combobox(toolbar, textvariable=self.status_var,
                                   values=["all", "ordered", "in_transit", "received", "cancelled"],
                                   width=12, state="readonly")
        status_combo.pack(side=tk.LEFT, padx=2)
        status_combo.bind('<<ComboboxSelected>>', lambda e: self.load_orders())
        
        # Split view
        content = ttk.PanedWindow(self.frame, orient=tk.HORIZONTAL)
        content.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Left: Order list
        left_frame = ttk.Frame(content)
        content.add(left_frame, weight=2)
        
        tree_frame = ttk.Frame(left_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(tree_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.tree = ttk.Treeview(tree_frame,
                                columns=("PO", "Date", "Supplier", "Status", "Items", "Total"),
                                show="headings",
                                yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.tree.yview)
        
        self.tree.heading("PO", text="PO Number")
        self.tree.heading("Date", text="Order Date")
        self.tree.heading("Supplier", text="Supplier")
        self.tree.heading("Status", text="Status")
        self.tree.heading("Items", text="Items")
        self.tree.heading("Total", text="Total")
        
        self.tree.column("PO", width=100)
        self.tree.column("Date", width=100)
        self.tree.column("Supplier", width=150)
        self.tree.column("Status", width=90)
        self.tree.column("Items", width=60)
        self.tree.column("Total", width=80)
        
        self.tree.pack(fill=tk.BOTH, expand=True)
        self.tree.bind('<<TreeviewSelect>>', self.on_order_select)
        self.tree.bind('<Double-Button-1>', lambda e: self.edit_order())
        
        # Right: Details
        right_frame = ttk.Frame(content)
        content.add(right_frame, weight=3)
        
        ttk.Label(right_frame, text="Order Details", 
                 font=("Arial", 12, "bold")).pack(anchor=tk.W, pady=5)
        
        # Details text
        details_frame = ttk.Frame(right_frame)
        details_frame.pack(fill=tk.BOTH, expand=True)
        
        details_scroll = ttk.Scrollbar(details_frame)
        details_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.details_text = tk.Text(details_frame, wrap=tk.WORD,
                                   yscrollcommand=details_scroll.set,
                                   font=("Consolas", 9))
        details_scroll.config(command=self.details_text.yview)
        self.details_text.pack(fill=tk.BOTH, expand=True)
    
    def load_orders(self):
        """Load orders into tree."""
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        status = None if self.status_var.get() == "all" else self.status_var.get()
        orders = self.manager.list_inbound_orders(status=status)
        
        for order in orders:
            items = self.manager.get_order_items(order.id)
            
            self.tree.insert("", tk.END, iid=str(order.id), values=(
                order.po_number,
                order.order_date.strftime("%Y-%m-%d"),
                order.supplier_name,
                order.status,
                len(items),
                f"${order.total_cost:.2f}" if order.total_cost else "-"
            ))
    
    def on_order_select(self, event):
        """Handle order selection."""
        selection = self.tree.selection()
        if not selection:
            return
        
        order_id = int(selection[0])
        order = self.manager.get_inbound_order(order_id)
        items = self.manager.get_order_items(order_id)
        
        # Build details
        details = []
        details.append(f"PO Number: {order.po_number}")
        details.append(f"Supplier: {order.supplier_name}")
        details.append(f"Status: {order.status.upper()}")
        details.append("")
        
        details.append(f"Order Date: {order.order_date.strftime('%Y-%m-%d')}")
        if order.expected_date:
            details.append(f"Expected: {order.expected_date.strftime('%Y-%m-%d')}")
        if order.received_date:
            details.append(f"Received: {order.received_date.strftime('%Y-%m-%d')}")
        details.append("")
        
        if order.supplier_reference:
            details.append(f"Supplier Ref: {order.supplier_reference}")
        if order.supplier_url:
            details.append(f"URL: {order.supplier_url}")
        if order.tracking_number:
            details.append(f"Tracking: {order.tracking_number} ({order.carrier or 'Unknown'})")
        details.append("")
        
        details.append("=== LINE ITEMS ===")
        for item in items:
            status_icon = "✓" if item['quantity_received'] >= item['quantity_ordered'] else "○"
            details.append(f"{status_icon} {item['sku']} - {item['title']}")
            details.append(f"    Ordered: {item['quantity_ordered']}  Received: {item['quantity_received']}")
            details.append(f"    @ ${item['unit_cost']:.2f} ea = ${item['extended_cost']:.2f}")
            if item['quantity_remaining'] > 0:
                details.append(f"    ** {item['quantity_remaining']} remaining **")
        details.append("")
        
        details.append("=== COSTS ===")
        if order.subtotal:
            details.append(f"Subtotal: ${order.subtotal:.2f}")
        if order.shipping_cost:
            details.append(f"Shipping: ${order.shipping_cost:.2f}")
        if order.tax:
            details.append(f"Tax: ${order.tax:.2f}")
        if order.total_cost:
            details.append(f"TOTAL: ${order.total_cost:.2f}")
        details.append("")
        
        if order.notes:
            details.append("=== NOTES ===")
            details.append(order.notes)
        
        self.details_text.config(state=tk.NORMAL)
        self.details_text.delete(1.0, tk.END)
        self.details_text.insert(1.0, "\n".join(details))
        self.details_text.config(state=tk.DISABLED)
    
    def create_po(self):
        """Create new purchase order."""
        dialog = InboundOrderDialog(self.app.root, self.manager, self.item_manager, mode="add")
        if dialog.result:
            self.load_orders()
            messagebox.showinfo("Success", f"PO {dialog.result.po_number} created")
    
    def edit_order(self):
        """Edit selected order."""
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select an order")
            return
        
        order_id = int(selection[0])
        order = self.manager.get_inbound_order(order_id)
        
        if order.status == 'received':
            messagebox.showwarning("Cannot Edit", "Cannot edit a received order")
            return
        
        dialog = InboundOrderDialog(self.app.root, self.manager, self.item_manager, 
                                   mode="edit", order=order)
        if dialog.result:
            self.load_orders()
            self.on_order_select(None)
    
    def receive_order(self):
        """Receive selected order."""
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select an order")
            return
        
        order_id = int(selection[0])
        order = self.manager.get_inbound_order(order_id)
        
        if order.status == 'received':
            messagebox.showinfo("Already Received", "This order has already been received")
            return
        
        dialog = ReceiveOrderDialog(self.app.root, self.manager, order)
        if dialog.result:
            self.load_orders()
            self.on_order_select(None)
            messagebox.showinfo("Success", "Order received into inventory")
    
    def cancel_order(self):
        """Cancel selected order."""
        selection = self.tree.selection()
        if not selection:
            return
        
        order_id = int(selection[0])
        order = self.manager.get_inbound_order(order_id)
        
        if order.status == 'received':
            messagebox.showwarning("Cannot Cancel", "Cannot cancel a received order")
            return
        
        if messagebox.askyesno("Confirm Cancel", 
                             f"Cancel PO {order.po_number}?"):
            notes = simpledialog.askstring("Cancel Reason", "Reason for cancellation:")
            self.manager.cancel_order(order_id, notes)
            self.load_orders()
            self.on_order_select(None)


class InboundOrderDialog(tk.Toplevel):
    """Dialog for creating/editing inbound orders."""
    
    def __init__(self, parent, manager, item_manager, mode="add", order=None):
        super().__init__(parent)
        self.manager = manager
        self.item_manager = item_manager
        self.mode = mode
        self.order = order
        self.result = None
        self.items = []
        
        self.title("New Purchase Order" if mode == "add" else "Edit Purchase Order")
        self.geometry("900x800")
        self.transient(parent)
        self.grab_set()
        
        # Center on parent window
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
        
        if mode == "edit" and order:
            self.load_order_data()
        
        self.wait_window()
    
    def create_widgets(self):
        """Create widgets."""
        # Header form
        form = ttk.Frame(self, padding=10)
        form.pack(fill=tk.X)
        
        row = 0
        
        # PO Number (auto-generated on add)
        if self.mode == "edit":
            ttk.Label(form, text="PO Number:").grid(row=row, column=0, sticky=tk.W, pady=5)
            self.po_var = tk.StringVar()
            ttk.Entry(form, textvariable=self.po_var, width=20, state="readonly").grid(row=row, column=1, sticky=tk.W, pady=5)
            row += 1
        
        # Supplier
        ttk.Label(form, text="Supplier:*").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.supplier_var = tk.StringVar()
        ttk.Entry(form, textvariable=self.supplier_var, width=40).grid(row=row, column=1, columnspan=2, sticky=tk.EW, pady=5)
        row += 1
        
        # Supplier Reference
        ttk.Label(form, text="Supplier Ref:").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.supplier_ref_var = tk.StringVar()
        ttk.Entry(form, textvariable=self.supplier_ref_var, width=40).grid(row=row, column=1, columnspan=2, sticky=tk.EW, pady=5)
        row += 1
        
        # URL
        ttk.Label(form, text="Supplier URL:").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.url_var = tk.StringVar()
        ttk.Entry(form, textvariable=self.url_var, width=40).grid(row=row, column=1, columnspan=2, sticky=tk.EW, pady=5)
        row += 1
        
        # Dates
        ttk.Label(form, text="Order Date:*").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.order_date_var = tk.StringVar(value=datetime.now().strftime("%Y-%m-%d"))
        ttk.Entry(form, textvariable=self.order_date_var, width=15).grid(row=row, column=1, sticky=tk.W, pady=5)
        
        ttk.Label(form, text="Expected:").grid(row=row, column=2, sticky=tk.W, padx=(10, 0), pady=5)
        self.expected_var = tk.StringVar()
        ttk.Entry(form, textvariable=self.expected_var, width=15).grid(row=row, column=3, sticky=tk.W, pady=5)
        row += 1
        
        # Status (edit only)
        if self.mode == "edit":
            ttk.Label(form, text="Status:").grid(row=row, column=0, sticky=tk.W, pady=5)
            self.status_var = tk.StringVar()
            ttk.Combobox(form, textvariable=self.status_var,
                        values=["ordered", "in_transit", "received", "cancelled"],
                        width=15, state="readonly").grid(row=row, column=1, sticky=tk.W, pady=5)
            row += 1
        
        # Tracking
        ttk.Label(form, text="Tracking #:").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.tracking_var = tk.StringVar()
        ttk.Entry(form, textvariable=self.tracking_var, width=20).grid(row=row, column=1, sticky=tk.W, pady=5)
        
        ttk.Label(form, text="Carrier:").grid(row=row, column=2, sticky=tk.W, padx=(10, 0), pady=5)
        self.carrier_var = tk.StringVar()
        ttk.Entry(form, textvariable=self.carrier_var, width=15).grid(row=row, column=3, sticky=tk.W, pady=5)
        row += 1
        
        form.columnconfigure(1, weight=1)
        
        # Line items
        items_frame = ttk.LabelFrame(self, text="Line Items", padding=10)
        items_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        toolbar = ttk.Frame(items_frame)
        toolbar.pack(fill=tk.X)
        
        ttk.Button(toolbar, text="➕ Add Item", command=self.add_item).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="❌ Remove", command=self.remove_item).pack(side=tk.LEFT, padx=2)
        
        self.subtotal_label = ttk.Label(toolbar, text="Subtotal: $0.00", font=("Arial", 10, "bold"))
        self.subtotal_label.pack(side=tk.RIGHT, padx=10)
        
        tree_frame = ttk.Frame(items_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        scrollbar = ttk.Scrollbar(tree_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.items_tree = ttk.Treeview(tree_frame,
                                      columns=("SKU", "Title", "Qty", "Cost", "Total"),
                                      show="headings",
                                      yscrollcommand=scrollbar.set,
                                      height=8)
        scrollbar.config(command=self.items_tree.yview)
        
        self.items_tree.heading("SKU", text="SKU")
        self.items_tree.heading("Title", text="Title")
        self.items_tree.heading("Qty", text="Quantity")
        self.items_tree.heading("Cost", text="Unit Cost")
        self.items_tree.heading("Total", text="Total")
        
        self.items_tree.column("SKU", width=100)
        self.items_tree.column("Title", width=250)
        self.items_tree.column("Qty", width=70)
        self.items_tree.column("Cost", width=80)
        self.items_tree.column("Total", width=80)
        
        self.items_tree.pack(fill=tk.BOTH, expand=True)
        
        # Costs
        costs_frame = ttk.Frame(self, padding=10)
        costs_frame.pack(fill=tk.X)
        
        ttk.Label(costs_frame, text="Shipping:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.shipping_var = tk.StringVar()
        ttk.Entry(costs_frame, textvariable=self.shipping_var, width=15).grid(row=0, column=1, sticky=tk.W, pady=2)
        self.shipping_var.trace('w', lambda *args: self.update_totals())
        
        ttk.Label(costs_frame, text="Tax:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.tax_var = tk.StringVar()
        ttk.Entry(costs_frame, textvariable=self.tax_var, width=15).grid(row=1, column=1, sticky=tk.W, pady=2)
        self.tax_var.trace('w', lambda *args: self.update_totals())
        
        self.total_label = ttk.Label(costs_frame, text="TOTAL: $0.00", 
                                     font=("Arial", 12, "bold"))
        self.total_label.grid(row=0, column=2, rowspan=2, sticky=tk.E, padx=20)
        
        costs_frame.columnconfigure(2, weight=1)
        
        # Notes
        notes_frame = ttk.LabelFrame(self, text="Notes", padding=10)
        notes_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.notes_text = tk.Text(notes_frame, height=3)
        self.notes_text.pack(fill=tk.X)
        
        # Buttons - fixed at bottom
        btn_frame = ttk.Frame(self, padding=10)
        btn_frame.pack(side=tk.BOTTOM, fill=tk.X)
        
        ttk.Button(btn_frame, text="Save", command=self.save, width=12).pack(side=tk.RIGHT, padx=5)
        ttk.Button(btn_frame, text="Cancel", command=self.destroy, width=12).pack(side=tk.RIGHT)
    
    def load_order_data(self):
        """Load existing order data."""
        self.po_var.set(self.order.po_number)
        self.supplier_var.set(self.order.supplier_name)
        self.supplier_ref_var.set(self.order.supplier_reference or "")
        self.url_var.set(self.order.supplier_url or "")
        self.order_date_var.set(self.order.order_date.strftime("%Y-%m-%d"))
        self.expected_var.set(self.order.expected_date.strftime("%Y-%m-%d") if self.order.expected_date else "")
        self.status_var.set(self.order.status)
        self.tracking_var.set(self.order.tracking_number or "")
        self.carrier_var.set(self.order.carrier or "")
        self.shipping_var.set(str(self.order.shipping_cost) if self.order.shipping_cost else "")
        self.tax_var.set(str(self.order.tax) if self.order.tax else "")
        self.notes_text.insert(1.0, self.order.notes or "")
        
        # Load items
        order_items = self.manager.get_order_items(self.order.id)
        for item in order_items:
            self.items.append({
                'sku': item['sku'],
                'title': item['title'],
                'quantity': item['quantity_ordered'],
                'unit_cost': item['unit_cost']
            })
        
        self.refresh_items()
    
    def add_item(self):
        """Add item to order."""
        from item_master_tab import ComponentPickerDialog
        dialog = ComponentPickerDialog(self, self.item_manager)
        if dialog.result:
            # Get unit cost
            item = self.item_manager.get_item_by_sku(dialog.result['sku'])
            initial_cost = str(item.base_cost or 0)
            
            cost_dialog = PriceDialog(self, "Unit Cost", 
                                     f"Unit cost for {dialog.result['sku']}:",
                                     initial_cost)
            
            if cost_dialog.result:
                try:
                    unit_cost = float(cost_dialog.result)
                    self.items.append({
                        'sku': dialog.result['sku'],
                        'title': dialog.result['title'],
                        'quantity': int(dialog.result['quantity']),
                        'unit_cost': unit_cost
                    })
                    self.refresh_items()
                except:
                    messagebox.showerror("Error", "Invalid cost")
    
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
        
        subtotal = 0.0
        for i, item in enumerate(self.items):
            total = item['quantity'] * item['unit_cost']
            subtotal += total
            
            self.items_tree.insert("", tk.END, iid=str(i), values=(
                item['sku'],
                item['title'],
                item['quantity'],
                f"${item['unit_cost']:.2f}",
                f"${total:.2f}"
            ))
        
        self.subtotal_label.config(text=f"Subtotal: ${subtotal:.2f}")
        self.update_totals()
    
    def update_totals(self):
        """Update total calculations."""
        subtotal = sum(item['quantity'] * item['unit_cost'] for item in self.items)
        
        try:
            shipping = float(self.shipping_var.get()) if self.shipping_var.get() else 0
        except:
            shipping = 0
        
        try:
            tax = float(self.tax_var.get()) if self.tax_var.get() else 0
        except:
            tax = 0
        
        total = subtotal + shipping + tax
        self.total_label.config(text=f"TOTAL: ${total:.2f}")
    
    def save(self):
        """Save the order."""
        if not self.supplier_var.get():
            messagebox.showerror("Validation Error", "Supplier is required")
            return
        
        if not self.items:
            messagebox.showerror("Validation Error", "Order must have at least one item")
            return
        
        # Parse date
        try:
            order_date = datetime.strptime(self.order_date_var.get(), "%Y-%m-%d")
        except:
            messagebox.showerror("Validation Error", "Invalid order date format (use YYYY-MM-DD)")
            return
        
        expected_date = None
        if self.expected_var.get():
            try:
                expected_date = datetime.strptime(self.expected_var.get(), "%Y-%m-%d")
            except:
                messagebox.showerror("Validation Error", "Invalid expected date format")
                return
        
        # Build data
        data = {
            'supplier_name': self.supplier_var.get(),
            'order_date': order_date,
            'supplier_reference': self.supplier_ref_var.get() or None,
            'supplier_url': self.url_var.get() or None,
            'expected_date': expected_date,
            'tracking_number': self.tracking_var.get() or None,
            'carrier': self.carrier_var.get() or None,
            'notes': self.notes_text.get(1.0, tk.END).strip() or None
        }
        
        try:
            data['shipping_cost'] = float(self.shipping_var.get()) if self.shipping_var.get() else None
            data['tax'] = float(self.tax_var.get()) if self.tax_var.get() else None
        except:
            messagebox.showerror("Error", "Invalid shipping or tax amount")
            return
        
        try:
            if self.mode == "add":
                self.result = self.manager.create_inbound_order(
                    items=[{'sku': i['sku'], 'quantity': i['quantity'], 'unit_cost': i['unit_cost']} 
                          for i in self.items],
                    **data
                )
            else:
                # Update order header (includes shipping and tax)
                if hasattr(self, 'status_var'):
                    data['status'] = self.status_var.get()
                self.result = self.manager.update_inbound_order(self.order.id, **data)
                
                # Update line items (this recalculates totals with new shipping/tax from above)
                self.manager.update_order_items(
                    self.order.id,
                    [{'sku': i['sku'], 'quantity': i['quantity'], 'unit_cost': i['unit_cost']} 
                     for i in self.items]
                )
            
            self.destroy()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save order: {e}")


class ReceiveOrderDialog(tk.Toplevel):
    """Dialog for receiving an inbound order."""
    
    def __init__(self, parent, manager, order):
        super().__init__(parent)
        self.manager = manager
        self.order = order
        self.result = None
        
        self.title(f"Receive Order - {order.po_number}")
        self.geometry("750x600")
        self.transient(parent)
        self.grab_set()
        
        # Center on parent window
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
        
        # Info
        info_frame = ttk.Frame(self, padding=10)
        info_frame.pack(fill=tk.X)
        
        ttk.Label(info_frame, text=f"PO: {order.po_number}", 
                 font=("Arial", 11, "bold")).pack(anchor=tk.W)
        ttk.Label(info_frame, text=f"Supplier: {order.supplier_name}").pack(anchor=tk.W)
        
        # Received date
        date_frame = ttk.Frame(self, padding=10)
        date_frame.pack(fill=tk.X)
        
        ttk.Label(date_frame, text="Received Date:").pack(side=tk.LEFT)
        self.date_var = tk.StringVar(value=datetime.now().strftime("%Y-%m-%d"))
        ttk.Entry(date_frame, textvariable=self.date_var, width=15).pack(side=tk.LEFT, padx=5)
        
        # Items
        items_frame = ttk.LabelFrame(self, text="Items to Receive", padding=10)
        items_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        ttk.Label(items_frame, text="Enter quantities received (leave blank to receive full amount)").pack(anchor=tk.W, pady=5)
        
        tree_frame = ttk.Frame(items_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(tree_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.tree = ttk.Treeview(tree_frame,
                                columns=("SKU", "Title", "Ordered", "Already", "Receive"),
                                show="headings",
                                yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.tree.yview)
        
        self.tree.heading("SKU", text="SKU")
        self.tree.heading("Title", text="Title")
        self.tree.heading("Ordered", text="Ordered")
        self.tree.heading("Already", text="Already Received")
        self.tree.heading("Receive", text="Receive Now")
        
        self.tree.column("SKU", width=100)
        self.tree.column("Title", width=200)
        self.tree.column("Ordered", width=80)
        self.tree.column("Already", width=120)
        self.tree.column("Receive", width=100)
        
        self.tree.pack(fill=tk.BOTH, expand=True)
        
        # Load items
        self.items = self.manager.get_order_items(order.id)
        self.qty_vars = {}
        
        for item in self.items:
            remaining = item['quantity_remaining']
            var = tk.StringVar(value=str(remaining))
            self.qty_vars[item['item_id']] = var
            
            self.tree.insert("", tk.END, values=(
                item['sku'],
                item['title'],
                item['quantity_ordered'],
                item['quantity_received'],
                remaining
            ))
        
        # Notes
        notes_frame = ttk.LabelFrame(self, text="Receiving Notes", padding=10)
        notes_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.notes_text = tk.Text(notes_frame, height=3)
        self.notes_text.pack(fill=tk.X)
        
        # Buttons - fixed at bottom
        btn_frame = ttk.Frame(self, padding=10)
        btn_frame.pack(side=tk.BOTTOM, fill=tk.X)
        
        ttk.Button(btn_frame, text="Receive Into Inventory", 
                  command=self.receive, width=20).pack(side=tk.RIGHT, padx=5)
        ttk.Button(btn_frame, text="Cancel", command=self.destroy, width=12).pack(side=tk.RIGHT)
        
        self.wait_window()
    
    def receive(self):
        """Receive the items."""
        try:
            received_date = datetime.strptime(self.date_var.get(), "%Y-%m-%d")
        except:
            messagebox.showerror("Error", "Invalid date format")
            return
        
        # Build received items dict
        received_items = {}
        for item in self.items:
            item_id = item['item_id']
            var = self.qty_vars.get(item_id)
            if var and var.get():
                try:
                    qty = int(var.get())
                    if qty > 0:
                        received_items[item_id] = qty
                except:
                    messagebox.showerror("Error", f"Invalid quantity for {item['sku']}")
                    return
        
        if not received_items:
            messagebox.showwarning("No Items", "No items to receive")
            return
        
        notes = self.notes_text.get(1.0, tk.END).strip()
        
        try:
            self.manager.receive_order(self.order.id, received_items, received_date, notes)
            self.result = True
            self.destroy()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to receive order: {e}")
