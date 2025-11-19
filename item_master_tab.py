"""Item Master management GUI tab."""
import os
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from item_master_manager import ItemMasterManager
from database import ItemMaster

class ItemMasterTab:
    """GUI tab for managing item master records."""
    
    def __init__(self, parent_frame, app):
        self.frame = parent_frame
        self.app = app
        self.manager = ItemMasterManager()
        
        self.setup_ui()
        self.load_items()
    
    def setup_ui(self):
        """Set up the UI components."""
        # Top toolbar
        toolbar = ttk.Frame(self.frame)
        toolbar.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)
        
        ttk.Button(toolbar, text="➕ Add Item", 
                  command=self.add_item).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="📦 Add Kit", 
                  command=self.add_kit).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="✏️ Edit", 
                  command=self.edit_item).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="🔧 Adjust Inventory", 
                  command=self.adjust_inventory).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="🔄 Refresh", 
                  command=self.load_items).pack(side=tk.LEFT, padx=2)
        
        # Filter
        ttk.Label(toolbar, text="Category:").pack(side=tk.LEFT, padx=(20, 2))
        self.category_var = tk.StringVar(value="all")
        category_combo = ttk.Combobox(toolbar, textvariable=self.category_var,
                                     values=["all", "raw material", "component", 
                                            "finished good", "kit"],
                                     width=15, state="readonly")
        category_combo.pack(side=tk.LEFT, padx=2)
        category_combo.bind('<<ComboboxSelected>>', lambda e: self.load_items())
        
        # Main content - split view
        content = ttk.PanedWindow(self.frame, orient=tk.HORIZONTAL)
        content.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Left: Item list
        left_frame = ttk.Frame(content)
        content.add(left_frame, weight=3)
        
        # Item tree
        tree_frame = ttk.Frame(left_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(tree_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.tree = ttk.Treeview(tree_frame, 
                                columns=("SKU", "Title", "Category", "On Hand", "Available", "Cost", "Price"),
                                show="headings",
                                yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.tree.yview)
        
        self.tree.heading("SKU", text="SKU")
        self.tree.heading("Title", text="Title")
        self.tree.heading("Category", text="Category")
        self.tree.heading("On Hand", text="On Hand")
        self.tree.heading("Available", text="Available")
        self.tree.heading("Cost", text="Cost")
        self.tree.heading("Price", text="Price")
        
        self.tree.column("SKU", width=100)
        self.tree.column("Title", width=250)
        self.tree.column("Category", width=100)
        self.tree.column("On Hand", width=70)
        self.tree.column("Available", width=70)
        self.tree.column("Cost", width=70)
        self.tree.column("Price", width=70)
        
        self.tree.pack(fill=tk.BOTH, expand=True)
        self.tree.bind('<<TreeviewSelect>>', self.on_item_select)
        self.tree.bind('<Double-Button-1>', lambda e: self.edit_item())
        
        # Image preview tooltip
        self.image_tooltip = None
        self.hover_job = None  # Track pending tooltip display
        self.last_hover_item = None  # Track which item we're hovering over
        self.tree.bind('<Motion>', self.on_tree_motion)
        self.tree.bind('<Leave>', lambda e: self.hide_image_tooltip())
        
        # Right: Details panel
        right_frame = ttk.Frame(content)
        content.add(right_frame, weight=2)
        
        ttk.Label(right_frame, text="Item Details", 
                 font=("Arial", 12, "bold")).pack(anchor=tk.W, pady=5)
        
        # Details text widget
        details_frame = ttk.Frame(right_frame)
        details_frame.pack(fill=tk.BOTH, expand=True)
        
        details_scroll = ttk.Scrollbar(details_frame)
        details_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.details_text = tk.Text(details_frame, wrap=tk.WORD, 
                                   yscrollcommand=details_scroll.set,
                                   font=("Consolas", 9))
        details_scroll.config(command=self.details_text.yview)
        self.details_text.pack(fill=tk.BOTH, expand=True)
        
        # Buttons for selected item
        btn_frame = ttk.Frame(right_frame)
        btn_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(btn_frame, text="View BOM", 
                  command=self.view_bom).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="Edit BOM", 
                  command=self.edit_bom).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="Assemble Kit", 
                  command=self.assemble_kit).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="Transaction History", 
                  command=self.view_history).pack(side=tk.LEFT, padx=2)
    
    def load_items(self):
        """Load items into the tree."""
        # Clear existing
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Get filter
        category = None if self.category_var.get() == "all" else self.category_var.get()
        
        # Load items
        items = self.manager.list_items(category=category, active_only=True)
        
        for item in items:
            inventory = self.manager.get_item_inventory(item.id)
            
            cost = item.calculated_cost if item.is_kit else item.base_cost
            
            self.tree.insert("", tk.END, iid=str(item.id), values=(
                item.sku,
                item.title,
                item.category or "",
                inventory.quantity_on_hand if inventory else 0,
                inventory.quantity_available if inventory else 0,
                f"${cost:.2f}" if cost else "-",
                f"${item.sell_price:.2f}" if item.sell_price else "-"
            ))
    
    def on_item_select(self, event):
        """Handle item selection."""
        selection = self.tree.selection()
        if not selection:
            return
        
        item_id = int(selection[0])
        item = self.manager.get_item_by_id(item_id)
        inventory = self.manager.get_item_inventory(item_id)
        
        # Build details text
        details = []
        details.append(f"SKU: {item.sku}")
        details.append(f"Title: {item.title}")
        details.append(f"Category: {item.category or 'Not set'}")
        details.append(f"Type: {'Kit/Assembly' if item.is_kit else 'Single Item'}")
        details.append("")
        
        if item.description:
            details.append(f"Description:\n{item.description}")
            details.append("")
        
        details.append("=== INVENTORY ===")
        if inventory:
            details.append(f"On Hand: {inventory.quantity_on_hand}")
            details.append(f"Reserved: {inventory.quantity_reserved}")
            details.append(f"Available: {inventory.quantity_available}")
            details.append(f"Last Updated: {inventory.last_updated.strftime('%Y-%m-%d %H:%M') if inventory.last_updated else 'Never'}")
        else:
            details.append("No inventory record")
        details.append("")
        
        details.append("=== PRICING ===")
        if item.base_cost:
            details.append(f"Base Cost: ${item.base_cost:.2f}")
        if item.calculated_cost:
            details.append(f"Calculated Cost: ${item.calculated_cost:.2f}")
        if item.sell_price:
            details.append(f"Sell Price: ${item.sell_price:.2f}")
            cost = item.calculated_cost or item.base_cost
            if cost:
                margin = ((item.sell_price - cost) / item.sell_price) * 100
                details.append(f"Margin: {margin:.1f}%")
        details.append("")
        
        if item.is_kit:
            details.append("=== BILL OF MATERIALS ===")
            bom = self.manager.get_kit_bom(item_id)
            if bom:
                for comp in bom:
                    details.append(f"  {comp['quantity_required']}x {comp['sku']} - {comp['title']}")
                    details.append(f"      @ ${comp['unit_cost']:.2f} ea = ${comp['extended_cost']:.2f}")
            else:
                details.append("  No components defined")
            details.append("")
        
        details.append("=== SUPPLIER INFO ===")
        if item.supplier_name:
            details.append(f"Supplier: {item.supplier_name}")
        if item.supplier_sku:
            details.append(f"Supplier SKU: {item.supplier_sku}")
        if item.supplier_url:
            details.append(f"URL: {item.supplier_url}")
        if item.lead_time_days:
            details.append(f"Lead Time: {item.lead_time_days} days")
        details.append("")
        
        details.append("=== REORDER ===")
        details.append(f"Reorder Point: {item.reorder_point}")
        details.append(f"Reorder Quantity: {item.reorder_quantity}")
        details.append(f"Track Inventory: {'Yes' if item.track_inventory else 'No'}")
        details.append("")
        
        details.append("=== OTHER ===")
        if item.weight:
            details.append(f"Weight: {item.weight} oz")
        if item.dimensions:
            details.append(f"Dimensions: {item.dimensions}")
        if item.storage_location:
            details.append(f"Storage: {item.storage_location}")
        if item.etsy_listing_id:
            details.append(f"Etsy Listing ID: {item.etsy_listing_id}")
        
        # Update text widget
        self.details_text.config(state=tk.NORMAL)
        self.details_text.delete(1.0, tk.END)
        self.details_text.insert(1.0, "\n".join(details))
        self.details_text.config(state=tk.DISABLED)
    
    def add_item(self):
        """Show dialog to add new item."""
        dialog = ItemMasterDialog(self.app.root, self.manager, mode="add")
        if dialog.result:
            self.load_items()
            messagebox.showinfo("Success", f"Item {dialog.result.sku} created")
    
    def add_kit(self):
        """Show dialog to add new kit."""
        dialog = KitDialog(self.app.root, self.manager, mode="add")
        if dialog.result:
            self.load_items()
            messagebox.showinfo("Success", f"Kit {dialog.result.sku} created")
    
    def edit_item(self):
        """Edit selected item."""
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select an item to edit")
            return
        
        item_id = int(selection[0])
        item = self.manager.get_item_by_id(item_id)
        
        if item.is_kit:
            dialog = KitDialog(self.app.root, self.manager, mode="edit", item=item)
        else:
            dialog = ItemMasterDialog(self.app.root, self.manager, mode="edit", item=item)
        
        if dialog.result:
            self.load_items()
            self.on_item_select(None)
    
    def adjust_inventory(self):
        """Adjust inventory for selected item."""
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select an item")
            return
        
        item_id = int(selection[0])
        item = self.manager.get_item_by_id(item_id)
        inventory = self.manager.get_item_inventory(item_id)
        
        dialog = InventoryAdjustmentDialog(self.app.root, item, inventory, self.manager)
        if dialog.result:
            self.load_items()
            self.on_item_select(None)
    
    def view_bom(self):
        """View bill of materials for kit."""
        selection = self.tree.selection()
        if not selection:
            return
        
        item_id = int(selection[0])
        item = self.manager.get_item_by_id(item_id)
        
        if not item.is_kit:
            messagebox.showinfo("Not a Kit", "This item is not a kit")
            return
        
        self.on_item_select(None)  # Refresh details which shows BOM
    
    def edit_bom(self):
        """Edit bill of materials."""
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a kit")
            return
        
        item_id = int(selection[0])
        item = self.manager.get_item_by_id(item_id)
        
        if not item.is_kit:
            messagebox.showinfo("Not a Kit", "This item is not a kit")
            return
        
        dialog = BOMEditorDialog(self.app.root, self.manager, item)
        if dialog.result:
            self.load_items()
            self.on_item_select(None)
    
    def assemble_kit(self):
        """Assemble a kit from components."""
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a kit")
            return
        
        item_id = int(selection[0])
        item = self.manager.get_item_by_id(item_id)
        
        if not item.is_kit:
            messagebox.showinfo("Not a Kit", "This item is not a kit")
            return
        
        # Ask quantity
        qty_str = simpledialog.askstring("Assemble Kit", 
                                        f"How many units of {item.sku} to assemble?",
                                        initialvalue="1")
        if not qty_str:
            return
        
        try:
            quantity = int(qty_str)
            if quantity <= 0:
                raise ValueError()
        except:
            messagebox.showerror("Invalid Input", "Please enter a positive number")
            return
        
        # Check if possible
        can_assemble, details = self.manager.can_assemble_kit(item_id, quantity)
        
        if not can_assemble:
            msg = f"Insufficient components to assemble {quantity} unit(s):\n\n"
            for sku, info in details.items():
                if not info['sufficient']:
                    msg += f"{sku}: Need {info['required']}, have {info['available']}\n"
            messagebox.showerror("Cannot Assemble", msg)
            return
        
        # Confirm
        if messagebox.askyesno("Confirm Assembly", 
                             f"Assemble {quantity} unit(s) of {item.sku}?\n\n"
                             f"This will consume components from inventory."):
            notes = simpledialog.askstring("Assembly Notes", "Notes (optional):")
            success = self.manager.assemble_kit(item_id, quantity, notes)
            
            if success:
                messagebox.showinfo("Success", f"Assembled {quantity} unit(s)")
                self.load_items()
                self.on_item_select(None)
            else:
                messagebox.showerror("Failed", "Assembly failed")
    
    def on_tree_motion(self, event):
        """Handle mouse motion over tree to show image tooltip."""
        # Get the item under the cursor
        item_id = self.tree.identify_row(event.y)
        
        # Cancel any pending tooltip display
        if self.hover_job:
            self.tree.after_cancel(self.hover_job)
            self.hover_job = None
        
        if item_id:
            # Check if we moved to a different item
            if self.last_hover_item != item_id:
                # Reset when moving to a new item
                self.last_hover_item = item_id
                self.hide_image_tooltip()
            
            # Get item data
            try:
                item_db_id = int(item_id)
                item = self.manager.get_item_by_id(item_db_id)
                
                # Only show tooltip if item has an image
                if item and item.image_path and os.path.exists(item.image_path):
                    # Schedule tooltip to show after 3 seconds (3000ms)
                    self.hover_job = self.tree.after(3000, 
                        lambda: self.show_image_tooltip(item_db_id, item.image_path))
                else:
                    self.hide_image_tooltip()
            except (ValueError, AttributeError):
                self.hide_image_tooltip()
        else:
            self.last_hover_item = None
            self.hide_image_tooltip()
    
    def show_image_tooltip(self, item_id, image_path):
        """Show image tooltip at cursor position."""
        # Verify we're still hovering over the same item
        if self.last_hover_item != str(item_id):
            return
        
        # Don't show if already showing for this item
        if self.image_tooltip and hasattr(self.image_tooltip, 'winfo_exists'):
            if self.image_tooltip.winfo_exists() and hasattr(self.image_tooltip, 'item_id'):
                if self.image_tooltip.item_id == item_id:
                    return
        
        try:
            from PIL import Image, ImageTk
            
            # Create tooltip window
            self.image_tooltip = tk.Toplevel(self.tree)
            self.image_tooltip.wm_overrideredirect(True)
            self.image_tooltip.item_id = item_id
            
            # Get current mouse position
            x = self.tree.winfo_pointerx() + 15
            y = self.tree.winfo_pointery() + 10
            self.image_tooltip.wm_geometry(f"+{x}+{y}")
            
            # Load and display image
            img = Image.open(image_path)
            img.thumbnail((400, 400), Image.Resampling.LANCZOS)
            
            photo = ImageTk.PhotoImage(img)
            label = tk.Label(self.image_tooltip, image=photo, relief=tk.SOLID, borderwidth=2)
            label.image = photo  # Keep reference
            label.pack()
            
        except Exception as e:
            # Silently fail if image can't be loaded
            if self.image_tooltip:
                self.image_tooltip.destroy()
                self.image_tooltip = None
    
    def hide_image_tooltip(self):
        """Hide the image tooltip."""
        # Cancel any pending tooltip display
        if self.hover_job:
            self.tree.after_cancel(self.hover_job)
            self.hover_job = None
        
        # Hide the tooltip if it's showing
        if self.image_tooltip:
            try:
                self.image_tooltip.destroy()
            except:
                pass
            self.image_tooltip = None
    
    def view_history(self):
        """View transaction history."""
        selection = self.tree.selection()
        if not selection:
            return
        
        item_id = int(selection[0])
        item = self.manager.get_item_by_id(item_id)
        
        TransactionHistoryDialog(self.app.root, self.manager, item)


class ItemMasterDialog(tk.Toplevel):
    """Dialog for adding/editing item master records."""
    
    def __init__(self, parent, manager, mode="add", item=None):
        super().__init__(parent)
        self.manager = manager
        self.mode = mode
        self.item = item
        self.result = None
        
        self.title("Add Item" if mode == "add" else "Edit Item")
        self.geometry("600x800")
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
        
        if mode == "edit" and item:
            self.load_item_data()
        
        self.wait_window()
    
    def create_widgets(self):
        """Create dialog widgets."""
        # Container with scrollbar for form
        container = ttk.Frame(self)
        container.pack(fill=tk.BOTH, expand=True)
        
        # Canvas for scrolling
        canvas = tk.Canvas(container)
        scrollbar = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Main form inside scrollable frame
        form = ttk.Frame(scrollable_frame, padding=10)
        form.pack(fill=tk.BOTH, expand=True)
        
        row = 0
        
        # SKU
        ttk.Label(form, text="SKU:*").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.sku_var = tk.StringVar()
        sku_entry = ttk.Entry(form, textvariable=self.sku_var, width=40)
        sku_entry.grid(row=row, column=1, sticky=tk.EW, pady=5)
        if self.mode == "edit":
            sku_entry.config(state="readonly")
        row += 1
        
        # Title
        ttk.Label(form, text="Title:*").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.title_var = tk.StringVar()
        ttk.Entry(form, textvariable=self.title_var, width=40).grid(row=row, column=1, sticky=tk.EW, pady=5)
        row += 1
        
        # Category
        ttk.Label(form, text="Category:").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.category_var = tk.StringVar()
        ttk.Combobox(form, textvariable=self.category_var,
                    values=["raw material", "component", "finished good"],
                    width=38).grid(row=row, column=1, sticky=tk.EW, pady=5)
        row += 1
        
        # Description
        ttk.Label(form, text="Description:").grid(row=row, column=0, sticky=tk.NW, pady=5)
        self.desc_text = tk.Text(form, width=40, height=4)
        self.desc_text.grid(row=row, column=1, sticky=tk.EW, pady=5)
        row += 1
        
        # Pricing section
        ttk.Separator(form, orient=tk.HORIZONTAL).grid(row=row, column=0, columnspan=2, sticky=tk.EW, pady=10)
        row += 1
        
        ttk.Label(form, text="Base Cost:").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.cost_var = tk.StringVar()
        ttk.Entry(form, textvariable=self.cost_var, width=20).grid(row=row, column=1, sticky=tk.W, pady=5)
        row += 1
        
        ttk.Label(form, text="Sell Price:").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.price_var = tk.StringVar()
        ttk.Entry(form, textvariable=self.price_var, width=20).grid(row=row, column=1, sticky=tk.W, pady=5)
        row += 1
        
        # Physical
        ttk.Separator(form, orient=tk.HORIZONTAL).grid(row=row, column=0, columnspan=2, sticky=tk.EW, pady=10)
        row += 1
        
        ttk.Label(form, text="Weight (oz):").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.weight_var = tk.StringVar()
        ttk.Entry(form, textvariable=self.weight_var, width=20).grid(row=row, column=1, sticky=tk.W, pady=5)
        row += 1
        
        ttk.Label(form, text="Dimensions:").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.dimensions_var = tk.StringVar()
        ttk.Entry(form, textvariable=self.dimensions_var, width=40).grid(row=row, column=1, sticky=tk.EW, pady=5)
        row += 1
        
        ttk.Label(form, text="Storage Location:").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.location_var = tk.StringVar()
        ttk.Entry(form, textvariable=self.location_var, width=40).grid(row=row, column=1, sticky=tk.EW, pady=5)
        row += 1
        
        # Supplier
        ttk.Separator(form, orient=tk.HORIZONTAL).grid(row=row, column=0, columnspan=2, sticky=tk.EW, pady=10)
        row += 1
        
        ttk.Label(form, text="Supplier:").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.supplier_var = tk.StringVar()
        ttk.Entry(form, textvariable=self.supplier_var, width=40).grid(row=row, column=1, sticky=tk.EW, pady=5)
        row += 1
        
        ttk.Label(form, text="Supplier SKU:").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.supplier_sku_var = tk.StringVar()
        ttk.Entry(form, textvariable=self.supplier_sku_var, width=40).grid(row=row, column=1, sticky=tk.EW, pady=5)
        row += 1
        
        ttk.Label(form, text="Supplier URL:").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.supplier_url_var = tk.StringVar()
        ttk.Entry(form, textvariable=self.supplier_url_var, width=40).grid(row=row, column=1, sticky=tk.EW, pady=5)
        row += 1
        
        # Inventory settings
        ttk.Separator(form, orient=tk.HORIZONTAL).grid(row=row, column=0, columnspan=2, sticky=tk.EW, pady=10)
        row += 1
        
        ttk.Label(form, text="Reorder Point:").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.reorder_point_var = tk.StringVar(value="5")
        ttk.Entry(form, textvariable=self.reorder_point_var, width=20).grid(row=row, column=1, sticky=tk.W, pady=5)
        row += 1
        
        ttk.Label(form, text="Reorder Qty:").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.reorder_qty_var = tk.StringVar(value="10")
        ttk.Entry(form, textvariable=self.reorder_qty_var, width=20).grid(row=row, column=1, sticky=tk.W, pady=5)
        row += 1
        
        self.track_inv_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(form, text="Track Inventory", 
                       variable=self.track_inv_var).grid(row=row, column=1, sticky=tk.W, pady=5)
        row += 1
        
        # Image
        ttk.Separator(form, orient=tk.HORIZONTAL).grid(row=row, column=0, columnspan=2, sticky=tk.EW, pady=10)
        row += 1
        
        ttk.Label(form, text="Item Image:").grid(row=row, column=0, sticky=tk.W, pady=5)
        image_frame = ttk.Frame(form)
        image_frame.grid(row=row, column=1, sticky=tk.EW, pady=5)
        
        self.image_path_var = tk.StringVar()
        self.image_entry = ttk.Entry(image_frame, textvariable=self.image_path_var, width=28, state='readonly')
        self.image_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(image_frame, text="Browse", command=self.browse_image, width=8).pack(side=tk.LEFT, padx=2)
        ttk.Button(image_frame, text="Clear", command=self.clear_image, width=8).pack(side=tk.LEFT)
        row += 1
        
        # Image preview
        self.image_label = ttk.Label(form, text="No image selected", relief=tk.SUNKEN, anchor=tk.CENTER)
        self.image_label.grid(row=row, column=1, sticky=tk.EW, pady=5)
        self.photo_image = None  # Keep reference to prevent garbage collection
        row += 1
        
        # Etsy
        ttk.Separator(form, orient=tk.HORIZONTAL).grid(row=row, column=0, columnspan=2, sticky=tk.EW, pady=10)
        row += 1
        
        ttk.Label(form, text="Etsy Listing ID:").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.etsy_id_var = tk.StringVar()
        ttk.Entry(form, textvariable=self.etsy_id_var, width=40).grid(row=row, column=1, sticky=tk.EW, pady=5)
        row += 1
        
        form.columnconfigure(1, weight=1)
        
        # Pack canvas and scrollbar
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Buttons - fixed at bottom, outside scrollable area
        btn_frame = ttk.Frame(self, padding=10)
        btn_frame.pack(side=tk.BOTTOM, fill=tk.X)
        
        ttk.Button(btn_frame, text="Save", command=self.save, width=12).pack(side=tk.RIGHT, padx=5)
        ttk.Button(btn_frame, text="Cancel", command=self.destroy, width=12).pack(side=tk.RIGHT)
    
    def load_item_data(self):
        """Load existing item data into form."""
        self.sku_var.set(self.item.sku)
        self.title_var.set(self.item.title)
        self.category_var.set(self.item.category or "")
        self.desc_text.insert(1.0, self.item.description or "")
        self.cost_var.set(str(self.item.base_cost) if self.item.base_cost else "")
        self.price_var.set(str(self.item.sell_price) if self.item.sell_price else "")
        self.weight_var.set(str(self.item.weight) if self.item.weight else "")
        self.dimensions_var.set(self.item.dimensions or "")
        self.location_var.set(self.item.storage_location or "")
        self.supplier_var.set(self.item.supplier_name or "")
        self.supplier_sku_var.set(self.item.supplier_sku or "")
        self.supplier_url_var.set(self.item.supplier_url or "")
        self.reorder_point_var.set(str(self.item.reorder_point))
        self.reorder_qty_var.set(str(self.item.reorder_quantity))
        self.track_inv_var.set(self.item.track_inventory)
        self.image_path_var.set(self.item.image_path or "")
        self.load_image_preview(self.item.image_path)
        self.etsy_id_var.set(self.item.etsy_listing_id or "")
    
    def load_image_preview(self, image_path):
        """Load and display image preview."""
        if not image_path or not os.path.exists(image_path):
            self.image_label.config(text="No image selected", image='')
            self.photo_image = None
            return
        
        try:
            from PIL import Image, ImageTk
            # Open and resize image to fit preview area (max 300x300)
            img = Image.open(image_path)
            img.thumbnail((300, 300), Image.Resampling.LANCZOS)
            
            # Convert to PhotoImage
            self.photo_image = ImageTk.PhotoImage(img)
            self.image_label.config(image=self.photo_image, text='')
        except Exception as e:
            self.image_label.config(text=f"Error loading image: {e}", image='')
            self.photo_image = None
    
    def browse_image(self):
        """Browse for an image file."""
        from tkinter import filedialog
        file_path = filedialog.askopenfilename(
            title="Select Item Image",
            filetypes=[
                ("Image files", "*.png *.jpg *.jpeg *.gif *.bmp"),
                ("All files", "*.*")
            ]
        )
        if file_path:
            self.image_path_var.set(file_path)
            self.load_image_preview(file_path)
    
    def clear_image(self):
        """Clear the image path."""
        self.image_path_var.set("")
        self.load_image_preview(None)
    
    def save(self):
        """Save the item."""
        # Validate
        if not self.sku_var.get() or not self.title_var.get():
            messagebox.showerror("Validation Error", "SKU and Title are required")
            return
        
        # Build data dict
        data = {
            'sku': self.sku_var.get(),
            'title': self.title_var.get(),
            'category': self.category_var.get() or None,
            'description': self.desc_text.get(1.0, tk.END).strip() or None,
            'storage_location': self.location_var.get() or None,
            'supplier_name': self.supplier_var.get() or None,
            'supplier_sku': self.supplier_sku_var.get() or None,
            'supplier_url': self.supplier_url_var.get() or None,
            'track_inventory': self.track_inv_var.get(),
            'image_path': self.image_path_var.get() or None,
            'etsy_listing_id': self.etsy_id_var.get() or None
        }
        
        # Parse numeric fields
        try:
            if self.cost_var.get():
                data['base_cost'] = float(self.cost_var.get())
            if self.price_var.get():
                data['sell_price'] = float(self.price_var.get())
            if self.weight_var.get():
                data['weight'] = float(self.weight_var.get())
            if self.dimensions_var.get():
                data['dimensions'] = self.dimensions_var.get()
            data['reorder_point'] = int(self.reorder_point_var.get())
            data['reorder_quantity'] = int(self.reorder_qty_var.get())
        except ValueError as e:
            messagebox.showerror("Validation Error", f"Invalid numeric value: {e}")
            return
        
        try:
            if self.mode == "add":
                self.result = self.manager.create_item(**data)
            else:
                self.result = self.manager.update_item(self.item.id, **data)
            self.destroy()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save item: {e}")


class KitDialog(tk.Toplevel):
    """Dialog for creating/editing kits with BOM."""
    
    def __init__(self, parent, manager, mode="add", item=None):
        super().__init__(parent)
        self.manager = manager
        self.mode = mode
        self.item = item
        self.result = None
        self.components = []
        
        self.title("Add Kit" if mode == "add" else "Edit Kit")
        self.geometry("750x700")
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
        
        if mode == "edit" and item:
            self.load_kit_data()
        
        self.wait_window()
    
    def create_widgets(self):
        """Create dialog widgets."""
        # Top form
        form = ttk.Frame(self, padding=10)
        form.pack(fill=tk.X)
        
        # SKU and Title
        ttk.Label(form, text="Kit SKU:*").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.sku_var = tk.StringVar()
        sku_entry = ttk.Entry(form, textvariable=self.sku_var, width=30)
        sku_entry.grid(row=0, column=1, sticky=tk.W, pady=5)
        if self.mode == "edit":
            sku_entry.config(state="readonly")
        
        ttk.Label(form, text="Kit Title:*").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.title_var = tk.StringVar()
        ttk.Entry(form, textvariable=self.title_var, width=50).grid(row=1, column=1, columnspan=2, sticky=tk.EW, pady=5)
        
        ttk.Label(form, text="Sell Price:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.price_var = tk.StringVar()
        ttk.Entry(form, textvariable=self.price_var, width=20).grid(row=2, column=1, sticky=tk.W, pady=5)
        
        form.columnconfigure(1, weight=1)
        
        # Components section
        comp_frame = ttk.LabelFrame(self, text="Bill of Materials (Components)", padding=10)
        comp_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Toolbar
        toolbar = ttk.Frame(comp_frame)
        toolbar.pack(fill=tk.X)
        
        ttk.Button(toolbar, text="➕ Add Component", 
                  command=self.add_component).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="❌ Remove", 
                  command=self.remove_component).pack(side=tk.LEFT, padx=2)
        
        self.total_cost_label = ttk.Label(toolbar, text="Total Cost: $0.00", 
                                         font=("Arial", 10, "bold"))
        self.total_cost_label.pack(side=tk.RIGHT, padx=10)
        
        # Tree
        tree_frame = ttk.Frame(comp_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        scrollbar = ttk.Scrollbar(tree_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.comp_tree = ttk.Treeview(tree_frame,
                                     columns=("SKU", "Title", "Qty", "Cost", "Total"),
                                     show="headings",
                                     yscrollcommand=scrollbar.set,
                                     height=10)
        scrollbar.config(command=self.comp_tree.yview)
        
        self.comp_tree.heading("SKU", text="Component SKU")
        self.comp_tree.heading("Title", text="Title")
        self.comp_tree.heading("Qty", text="Quantity")
        self.comp_tree.heading("Cost", text="Unit Cost")
        self.comp_tree.heading("Total", text="Total")
        
        self.comp_tree.column("SKU", width=100)
        self.comp_tree.column("Title", width=200)
        self.comp_tree.column("Qty", width=70)
        self.comp_tree.column("Cost", width=80)
        self.comp_tree.column("Total", width=80)
        
        self.comp_tree.pack(fill=tk.BOTH, expand=True)
        
        # Buttons - fixed at bottom
        btn_frame = ttk.Frame(self, padding=10)
        btn_frame.pack(side=tk.BOTTOM, fill=tk.X)
        
        ttk.Button(btn_frame, text="Save Kit", command=self.save, width=12).pack(side=tk.RIGHT, padx=5)
        ttk.Button(btn_frame, text="Cancel", command=self.destroy, width=12).pack(side=tk.RIGHT)
    
    def load_kit_data(self):
        """Load existing kit data."""
        self.sku_var.set(self.item.sku)
        self.title_var.set(self.item.title)
        self.price_var.set(str(self.item.sell_price) if self.item.sell_price else "")
        
        # Load BOM
        bom = self.manager.get_kit_bom(self.item.id)
        for comp in bom:
            self.components.append({
                'sku': comp['sku'],
                'title': comp['title'],
                'quantity': comp['quantity_required'],
                'cost': comp['unit_cost']
            })
        
        self.refresh_components()
    
    def add_component(self):
        """Add a component to the BOM."""
        dialog = ComponentPickerDialog(self, self.manager)
        if dialog.result:
            self.components.append(dialog.result)
            self.refresh_components()
    
    def remove_component(self):
        """Remove selected component."""
        selection = self.comp_tree.selection()
        if not selection:
            return
        
        index = int(selection[0])
        del self.components[index]
        self.refresh_components()
    
    def refresh_components(self):
        """Refresh component tree."""
        for item in self.comp_tree.get_children():
            self.comp_tree.delete(item)
        
        total_cost = 0.0
        for i, comp in enumerate(self.components):
            cost = comp['cost'] or 0
            ext_cost = cost * comp['quantity']
            total_cost += ext_cost
            
            # Format quantity nicely - show decimals only if needed
            qty = comp['quantity']
            qty_str = f"{qty:.4f}".rstrip('0').rstrip('.') if qty != int(qty) else str(int(qty))
            
            self.comp_tree.insert("", tk.END, iid=str(i), values=(
                comp['sku'],
                comp['title'],
                qty_str,
                f"${cost:.2f}",
                f"${ext_cost:.2f}"
            ))
        
        self.total_cost_label.config(text=f"Total Cost: ${total_cost:.2f}")
    
    def save(self):
        """Save the kit."""
        if not self.sku_var.get() or not self.title_var.get():
            messagebox.showerror("Validation Error", "SKU and Title are required")
            return
        
        if not self.components:
            messagebox.showerror("Validation Error", "Kit must have at least one component")
            return
        
        # Format components for manager
        comp_list = [{'sku': c['sku'], 'quantity': c['quantity']} for c in self.components]
        
        try:
            if self.mode == "add":
                sell_price = float(self.price_var.get()) if self.price_var.get() else None
                self.result = self.manager.create_kit(
                    kit_sku=self.sku_var.get(),
                    kit_title=self.title_var.get(),
                    components=comp_list,
                    sell_price=sell_price
                )
            else:
                # Update kit info
                updates = {'title': self.title_var.get()}
                if self.price_var.get():
                    updates['sell_price'] = float(self.price_var.get())
                self.result = self.manager.update_item(self.item.id, **updates)
                
                # Update BOM
                self.manager.update_kit_bom(self.item.id, comp_list)
            
            self.destroy()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save kit: {e}")


class ComponentPickerDialog(tk.Toplevel):
    """Dialog for selecting a component to add to BOM."""
    
    def __init__(self, parent, manager):
        super().__init__(parent)
        self.manager = manager
        self.result = None
        
        self.title("Add Component")
        self.geometry("650x600")
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
        
        # Search
        search_frame = ttk.Frame(self, padding=10)
        search_frame.pack(fill=tk.X)
        
        ttk.Label(search_frame, text="Search:").pack(side=tk.LEFT)
        self.search_var = tk.StringVar()
        self.search_var.trace('w', lambda *args: self.filter_items())
        ttk.Entry(search_frame, textvariable=self.search_var, width=40).pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        # Items list
        list_frame = ttk.Frame(self)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10)
        
        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.tree = ttk.Treeview(list_frame,
                                columns=("SKU", "Title", "Cost"),
                                show="headings",
                                yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.tree.yview)
        
        self.tree.heading("SKU", text="SKU")
        self.tree.heading("Title", text="Title")
        self.tree.heading("Cost", text="Cost")
        
        self.tree.column("SKU", width=100)
        self.tree.column("Title", width=350)
        self.tree.column("Cost", width=80)
        
        self.tree.pack(fill=tk.BOTH, expand=True)
        self.tree.bind('<Double-Button-1>', lambda e: self.select_item())
        
        # Quantity
        qty_frame = ttk.Frame(self, padding=10)
        qty_frame.pack(fill=tk.X)
        
        ttk.Label(qty_frame, text="Quantity:").pack(side=tk.LEFT)
        self.qty_var = tk.StringVar(value="1")
        ttk.Entry(qty_frame, textvariable=self.qty_var, width=15).pack(side=tk.LEFT, padx=5)
        ttk.Label(qty_frame, text="(decimals OK: e.g., 0.10 for consumables)", 
                 font=("Arial", 8), foreground="gray").pack(side=tk.LEFT, padx=5)
        
        # Buttons - fixed at bottom
        btn_frame = ttk.Frame(self, padding=10)
        btn_frame.pack(side=tk.BOTTOM, fill=tk.X)
        
        ttk.Button(btn_frame, text="Add", command=self.select_item, width=12).pack(side=tk.RIGHT, padx=5)
        ttk.Button(btn_frame, text="Cancel", command=self.destroy, width=12).pack(side=tk.RIGHT)
        
        self.load_items()
        self.wait_window()
    
    def load_items(self):
        """Load available items."""
        self.all_items = self.manager.list_items(active_only=True)
        self.filter_items()
    
    def filter_items(self):
        """Filter items based on search."""
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        search = self.search_var.get().lower()
        
        for item in self.all_items:
            if search and search not in item.sku.lower() and search not in item.title.lower():
                continue
            
            cost = item.calculated_cost or item.base_cost
            self.tree.insert("", tk.END, iid=str(item.id), values=(
                item.sku,
                item.title,
                f"${cost:.2f}" if cost else "-"
            ))
    
    def select_item(self):
        """Select the item."""
        selection = self.tree.selection()
        if not selection:
            return
        
        item_id = int(selection[0])
        item = self.manager.get_item_by_id(item_id)
        
        try:
            quantity = float(self.qty_var.get())
            if quantity <= 0:
                raise ValueError()
        except:
            messagebox.showerror("Invalid Input", "Please enter a valid quantity")
            return
        
        self.result = {
            'sku': item.sku,
            'title': item.title,
            'quantity': quantity,
            'cost': item.calculated_cost or item.base_cost
        }
        self.destroy()


class InventoryAdjustmentDialog(tk.Toplevel):
    """Dialog for manual inventory adjustment."""
    
    def __init__(self, parent, item, inventory, manager):
        super().__init__(parent)
        self.item = item
        self.inventory = inventory
        self.manager = manager
        self.result = None
        
        self.title(f"Adjust Inventory - {item.sku}")
        self.geometry("450x350")
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
        
        ttk.Label(info_frame, text=f"Item: {item.title}", 
                 font=("Arial", 10, "bold")).pack(anchor=tk.W)
        ttk.Label(info_frame, text=f"Current On Hand: {inventory.quantity_on_hand}").pack(anchor=tk.W)
        ttk.Label(info_frame, text=f"Available: {inventory.quantity_available}").pack(anchor=tk.W)
        
        # Adjustment
        adj_frame = ttk.LabelFrame(self, text="Adjustment", padding=10)
        adj_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        ttk.Label(adj_frame, text="Quantity:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.qty_var = tk.StringVar()
        ttk.Entry(adj_frame, textvariable=self.qty_var, width=15).grid(row=0, column=1, sticky=tk.W, pady=5)
        ttk.Label(adj_frame, text="(+ to add, - to remove)").grid(row=0, column=2, sticky=tk.W, pady=5, padx=5)
        
        ttk.Label(adj_frame, text="Notes:").grid(row=1, column=0, sticky=tk.NW, pady=5)
        self.notes_text = tk.Text(adj_frame, width=40, height=6)
        self.notes_text.grid(row=1, column=1, columnspan=2, sticky=tk.EW, pady=5)
        
        adj_frame.columnconfigure(1, weight=1)
        
        # Buttons - fixed at bottom
        btn_frame = ttk.Frame(self, padding=10)
        btn_frame.pack(side=tk.BOTTOM, fill=tk.X)
        
        ttk.Button(btn_frame, text="Apply", command=self.apply, width=12).pack(side=tk.RIGHT, padx=5)
        ttk.Button(btn_frame, text="Cancel", command=self.destroy, width=12).pack(side=tk.RIGHT)
        
        self.wait_window()
    
    def apply(self):
        """Apply the adjustment."""
        try:
            quantity = int(self.qty_var.get())
            if quantity == 0:
                messagebox.showwarning("Invalid Input", "Quantity cannot be zero")
                return
        except:
            messagebox.showerror("Invalid Input", "Please enter a valid integer")
            return
        
        notes = self.notes_text.get(1.0, tk.END).strip()
        
        try:
            self.manager.adjust_inventory(self.item.id, quantity, notes)
            self.result = True
            self.destroy()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to adjust inventory: {e}")


class BOMEditorDialog(tk.Toplevel):
    """Dialog for editing bill of materials."""
    
    def __init__(self, parent, manager, kit_item):
        super().__init__(parent)
        self.manager = manager
        self.kit_item = kit_item
        self.result = None
        self.components = []
        
        self.title(f"Edit BOM - {kit_item.sku}")
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
        
        # Load existing BOM
        bom = self.manager.get_kit_bom(kit_item.id)
        for comp in bom:
            self.components.append({
                'sku': comp['sku'],
                'title': comp['title'],
                'quantity': comp['quantity_required'],
                'cost': comp['unit_cost']
            })
        
        self.create_widgets()
        self.refresh_components()
        
        self.wait_window()
    
    def create_widgets(self):
        """Create widgets."""
        # Info
        info_frame = ttk.Frame(self, padding=10)
        info_frame.pack(fill=tk.X)
        ttk.Label(info_frame, text=f"Kit: {self.kit_item.title}", 
                 font=("Arial", 11, "bold")).pack(anchor=tk.W)
        
        # Components
        comp_frame = ttk.Frame(self, padding=10)
        comp_frame.pack(fill=tk.BOTH, expand=True)
        
        toolbar = ttk.Frame(comp_frame)
        toolbar.pack(fill=tk.X)
        
        ttk.Button(toolbar, text="➕ Add", command=self.add_component).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="❌ Remove", command=self.remove_component).pack(side=tk.LEFT, padx=2)
        
        self.total_label = ttk.Label(toolbar, text="Total: $0.00", font=("Arial", 10, "bold"))
        self.total_label.pack(side=tk.RIGHT, padx=10)
        
        tree_frame = ttk.Frame(comp_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        scrollbar = ttk.Scrollbar(tree_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.tree = ttk.Treeview(tree_frame,
                                columns=("SKU", "Title", "Qty", "Cost", "Total"),
                                show="headings",
                                yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.tree.yview)
        
        self.tree.heading("SKU", text="SKU")
        self.tree.heading("Title", text="Title")
        self.tree.heading("Qty", text="Qty")
        self.tree.heading("Cost", text="Unit Cost")
        self.tree.heading("Total", text="Total")
        
        self.tree.column("SKU", width=100)
        self.tree.column("Title", width=200)
        self.tree.column("Qty", width=70)
        self.tree.column("Cost", width=80)
        self.tree.column("Total", width=80)
        
        self.tree.pack(fill=tk.BOTH, expand=True)
        
        # Buttons - fixed at bottom
        btn_frame = ttk.Frame(self, padding=10)
        btn_frame.pack(side=tk.BOTTOM, fill=tk.X)
        
        ttk.Button(btn_frame, text="Save", command=self.save, width=12).pack(side=tk.RIGHT, padx=5)
        ttk.Button(btn_frame, text="Cancel", command=self.destroy, width=12).pack(side=tk.RIGHT)
    
    def add_component(self):
        """Add component."""
        dialog = ComponentPickerDialog(self, self.manager)
        if dialog.result:
            self.components.append(dialog.result)
            self.refresh_components()
    
    def remove_component(self):
        """Remove component."""
        selection = self.tree.selection()
        if selection:
            index = int(selection[0])
            del self.components[index]
            self.refresh_components()
    
    def refresh_components(self):
        """Refresh tree."""
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        total = 0.0
        for i, comp in enumerate(self.components):
            cost = comp['cost'] or 0
            ext = cost * comp['quantity']
            total += ext
            
            # Format quantity nicely - show decimals only if needed
            qty = comp['quantity']
            qty_str = f"{qty:.4f}".rstrip('0').rstrip('.') if qty != int(qty) else str(int(qty))
            
            self.tree.insert("", tk.END, iid=str(i), values=(
                comp['sku'],
                comp['title'],
                qty_str,
                f"${cost:.2f}",
                f"${ext:.2f}"
            ))
        
        self.total_label.config(text=f"Total: ${total:.2f}")
    
    def save(self):
        """Save BOM."""
        if not self.components:
            messagebox.showerror("Error", "Kit must have at least one component")
            return
        
        try:
            comp_list = [{'sku': c['sku'], 'quantity': c['quantity']} for c in self.components]
            self.manager.update_kit_bom(self.kit_item.id, comp_list)
            self.result = True
            self.destroy()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save BOM: {e}")


class TransactionHistoryDialog(tk.Toplevel):
    """Dialog showing inventory transaction history."""
    
    def __init__(self, parent, manager, item):
        super().__init__(parent)
        self.manager = manager
        self.item = item
        
        self.title(f"Transaction History - {item.sku}")
        self.geometry("900x600")
        self.transient(parent)
        
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
        ttk.Label(info_frame, text=f"{item.title}", 
                 font=("Arial", 11, "bold")).pack(anchor=tk.W)
        
        # Tree
        tree_frame = ttk.Frame(self, padding=10)
        tree_frame.pack(fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(tree_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        tree = ttk.Treeview(tree_frame,
                           columns=("Date", "Type", "Qty", "Ref", "Notes"),
                           show="headings",
                           yscrollcommand=scrollbar.set)
        scrollbar.config(command=tree.yview)
        
        tree.heading("Date", text="Date")
        tree.heading("Type", text="Type")
        tree.heading("Qty", text="Quantity")
        tree.heading("Ref", text="Reference")
        tree.heading("Notes", text="Notes")
        
        tree.column("Date", width=150)
        tree.column("Type", width=100)
        tree.column("Qty", width=70)
        tree.column("Ref", width=120)
        tree.column("Notes", width=300)
        
        tree.pack(fill=tk.BOTH, expand=True)
        
        # Load history
        transactions = self.manager.get_transaction_history(item.id)
        for txn in transactions:
            tree.insert("", tk.END, values=(
                txn.transaction_date.strftime("%Y-%m-%d %H:%M"),
                txn.transaction_type,
                f"{'+' if txn.quantity > 0 else ''}{txn.quantity}",
                f"{txn.reference_type or ''} {txn.reference_id or ''}".strip(),
                txn.notes or ""
            ))
        
        # Close button - fixed at bottom
        btn_frame = ttk.Frame(self, padding=10)
        btn_frame.pack(side=tk.BOTTOM, fill=tk.X)
        ttk.Button(btn_frame, text="Close", command=self.destroy, width=12).pack(side=tk.RIGHT)
