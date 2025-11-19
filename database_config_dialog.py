"""Database configuration dialog."""
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from database_manager import DatabaseManager
from config import Config
import threading

class DatabaseConfigDialog(tk.Toplevel):
    """Dialog for configuring and switching databases."""
    
    def __init__(self, parent, on_change_callback=None):
        super().__init__(parent)
        self.parent = parent
        self.on_change_callback = on_change_callback
        self.result = None
        
        self.title("Database Configuration")
        self.geometry("700x650")
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
        self.load_current_config()
        
        self.wait_window()
    
    def create_widgets(self):
        """Create dialog widgets."""
        # Header
        header_frame = ttk.Frame(self, padding=10)
        header_frame.pack(fill=tk.X)
        
        ttk.Label(header_frame, text="Database Configuration", 
                 font=("Arial", 14, "bold")).pack(anchor=tk.W)
        ttk.Label(header_frame, text="Choose between SQLite (local file) or MySQL (network database)",
                 foreground="gray").pack(anchor=tk.W)
        
        # Database type selection
        type_frame = ttk.LabelFrame(self, text="Database Type", padding=10)
        type_frame.pack(fill=tk.X, padx=10, pady=10)
        
        self.db_type_var = tk.StringVar(value="sqlite")
        ttk.Radiobutton(type_frame, text="SQLite (Local File)", 
                       variable=self.db_type_var, value="sqlite",
                       command=self.on_type_change).pack(anchor=tk.W, pady=5)
        ttk.Radiobutton(type_frame, text="MySQL (Network Database)", 
                       variable=self.db_type_var, value="mysql",
                       command=self.on_type_change).pack(anchor=tk.W, pady=5)
        
        # SQLite configuration
        self.sqlite_frame = ttk.LabelFrame(self, text="SQLite Configuration", padding=10)
        self.sqlite_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(self.sqlite_frame, text="Database File:").grid(row=0, column=0, sticky=tk.W, pady=5)
        path_frame = ttk.Frame(self.sqlite_frame)
        path_frame.grid(row=0, column=1, sticky=tk.EW, pady=5)
        
        self.sqlite_path_var = tk.StringVar()
        ttk.Entry(path_frame, textvariable=self.sqlite_path_var).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        ttk.Button(path_frame, text="Browse...", command=self.browse_sqlite, width=10).pack(side=tk.LEFT)
        
        self.sqlite_frame.columnconfigure(1, weight=1)
        
        # MySQL configuration
        self.mysql_frame = ttk.LabelFrame(self, text="MySQL Configuration", padding=10)
        self.mysql_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(self.mysql_frame, text="Host:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.mysql_host_var = tk.StringVar()
        ttk.Entry(self.mysql_frame, textvariable=self.mysql_host_var, width=40).grid(row=0, column=1, sticky=tk.EW, pady=5)
        
        ttk.Label(self.mysql_frame, text="Port:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.mysql_port_var = tk.StringVar()
        ttk.Entry(self.mysql_frame, textvariable=self.mysql_port_var, width=40).grid(row=1, column=1, sticky=tk.EW, pady=5)
        
        ttk.Label(self.mysql_frame, text="Database:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.mysql_database_var = tk.StringVar()
        ttk.Entry(self.mysql_frame, textvariable=self.mysql_database_var, width=40).grid(row=2, column=1, sticky=tk.EW, pady=5)
        
        ttk.Label(self.mysql_frame, text="Username:").grid(row=3, column=0, sticky=tk.W, pady=5)
        self.mysql_user_var = tk.StringVar()
        ttk.Entry(self.mysql_frame, textvariable=self.mysql_user_var, width=40).grid(row=3, column=1, sticky=tk.EW, pady=5)
        
        ttk.Label(self.mysql_frame, text="Password:").grid(row=4, column=0, sticky=tk.W, pady=5)
        self.mysql_password_var = tk.StringVar()
        ttk.Entry(self.mysql_frame, textvariable=self.mysql_password_var, width=40, show="*").grid(row=4, column=1, sticky=tk.EW, pady=5)
        
        self.mysql_frame.columnconfigure(1, weight=1)
        
        # Test connection button
        test_frame = ttk.Frame(self, padding=10)
        test_frame.pack(fill=tk.X)
        
        ttk.Button(test_frame, text="🔌 Test Connection", 
                  command=self.test_connection).pack(side=tk.LEFT, padx=5)
        
        self.test_result_label = ttk.Label(test_frame, text="", foreground="gray")
        self.test_result_label.pack(side=tk.LEFT, padx=10)
        
        # Progress bar (hidden initially)
        self.progress_frame = ttk.Frame(self, padding=10)
        self.progress_label = ttk.Label(self.progress_frame, text="")
        self.progress_label.pack(anchor=tk.W)
        self.progress_bar = ttk.Progressbar(self.progress_frame, mode='determinate', length=400)
        self.progress_bar.pack(fill=tk.X, pady=5)
        
        # Buttons
        btn_frame = ttk.Frame(self, padding=10)
        btn_frame.pack(side=tk.BOTTOM, fill=tk.X)
        
        ttk.Button(btn_frame, text="Save & Switch", 
                  command=self.save_and_switch, width=15).pack(side=tk.RIGHT, padx=5)
        ttk.Button(btn_frame, text="Cancel", 
                  command=self.destroy, width=12).pack(side=tk.RIGHT)
    
    def load_current_config(self):
        """Load current database configuration."""
        config = DatabaseManager.get_current_config()
        
        if config:
            self.db_type_var.set(config['type'])
            
            if config['type'] == 'sqlite':
                self.sqlite_path_var.set(config.get('path', 'etsy_inventory.db'))
            elif config['type'] == 'mysql':
                self.mysql_host_var.set(config.get('host', 'localhost'))
                self.mysql_port_var.set(config.get('port', '3306'))
                self.mysql_database_var.set(config.get('database', 'etsy_inventory'))
                self.mysql_user_var.set(config.get('user', 'root'))
        
        self.on_type_change()
    
    def on_type_change(self):
        """Handle database type change."""
        db_type = self.db_type_var.get()
        
        if db_type == 'sqlite':
            self.mysql_frame.pack_forget()
            self.sqlite_frame.pack(fill=tk.X, padx=10, pady=10)
        else:
            self.sqlite_frame.pack_forget()
            self.mysql_frame.pack(fill=tk.X, padx=10, pady=10)
        
        self.test_result_label.config(text="")
    
    def browse_sqlite(self):
        """Browse for SQLite database file."""
        file_path = filedialog.asksaveasfilename(
            title="Select SQLite Database File",
            defaultextension=".db",
            filetypes=[("SQLite Database", "*.db"), ("All Files", "*.*")]
        )
        if file_path:
            self.sqlite_path_var.set(file_path)
    
    def get_connection_string(self):
        """Build connection string from form inputs."""
        db_type = self.db_type_var.get()
        
        if db_type == 'sqlite':
            path = self.sqlite_path_var.get()
            return f'sqlite:///{path}'
        elif db_type == 'mysql':
            host = self.mysql_host_var.get()
            port = self.mysql_port_var.get()
            database = self.mysql_database_var.get()
            user = self.mysql_user_var.get()
            password = self.mysql_password_var.get()
            
            return f'mysql+pymysql://{user}:{password}@{host}:{port}/{database}'
    
    def test_connection(self):
        """Test the database connection."""
        try:
            conn_string = self.get_connection_string()
            success, message = DatabaseManager.test_connection(conn_string)
            
            if success:
                self.test_result_label.config(text="✓ " + message, foreground="green")
            else:
                self.test_result_label.config(text="✗ " + message, foreground="red")
        except Exception as e:
            self.test_result_label.config(text=f"✗ Error: {str(e)}", foreground="red")
    
    def save_and_switch(self):
        """Save configuration and migrate data if needed."""
        db_type = self.db_type_var.get()
        
        # Validate inputs
        if db_type == 'sqlite':
            if not self.sqlite_path_var.get():
                messagebox.showerror("Error", "Please specify a database file path")
                return
        elif db_type == 'mysql':
            if not all([self.mysql_host_var.get(), self.mysql_database_var.get(), self.mysql_user_var.get()]):
                messagebox.showerror("Error", "Please fill in all MySQL connection fields")
                return
        
        # Test connection first
        target_conn_string = self.get_connection_string()
        success, message = DatabaseManager.test_connection(target_conn_string)
        
        if not success:
            messagebox.showerror("Connection Failed", 
                               f"Cannot connect to target database:\n\n{message}")
            return
        
        # Get current configuration
        current_config = DatabaseManager.get_current_config()
        source_conn_string = current_config['connection_string'] if current_config else None
        
        # Check if we're switching databases
        if source_conn_string and source_conn_string != target_conn_string:
            # Ask if user wants to migrate data
            migrate = messagebox.askyesno("Migrate Data?", 
                                        "Do you want to migrate all data from the current database to the new database?\n\n"
                                        "This will copy all tables and data.\n\n"
                                        "Choose 'No' to start with an empty database.")
            
            if migrate:
                self.perform_migration(source_conn_string, target_conn_string)
                return
        
        # Save configuration
        self.save_config()
        messagebox.showinfo("Success", "Database configuration saved!\n\nPlease restart the application.")
        self.result = True
        self.destroy()
    
    def save_config(self):
        """Save database configuration."""
        db_type = self.db_type_var.get()
        
        if db_type == 'sqlite':
            DatabaseManager.save_database_config('sqlite', path=self.sqlite_path_var.get())
        elif db_type == 'mysql':
            DatabaseManager.save_database_config('mysql',
                host=self.mysql_host_var.get(),
                port=self.mysql_port_var.get(),
                database=self.mysql_database_var.get(),
                user=self.mysql_user_var.get(),
                password=self.mysql_password_var.get()
            )
    
    def perform_migration(self, source_conn, target_conn):
        """Perform database migration in background thread."""
        # Show progress bar
        self.progress_frame.pack(fill=tk.X, padx=10, pady=10, before=self.children['!frame4'])
        self.progress_bar['value'] = 0
        self.progress_label.config(text="Starting migration...")
        
        # Disable buttons during migration
        for child in self.children['!frame4'].winfo_children():
            if isinstance(child, ttk.Button):
                child.config(state='disabled')
        
        def update_progress(message, percent):
            """Update progress from background thread."""
            self.after(0, lambda: self.progress_label.config(text=message))
            self.after(0, lambda: self.progress_bar.config(value=percent))
        
        def do_migration():
            """Run migration in background thread."""
            success, message, stats = DatabaseManager.migrate_database(
                source_conn, target_conn, update_progress
            )
            
            # Update UI in main thread
            self.after(0, lambda: self.migration_complete(success, message, stats))
        
        # Start migration thread
        thread = threading.Thread(target=do_migration, daemon=True)
        thread.start()
    
    def migration_complete(self, success, message, stats):
        """Handle migration completion."""
        # Re-enable buttons
        for child in self.children['!frame4'].winfo_children():
            if isinstance(child, ttk.Button):
                child.config(state='normal')
        
        if success:
            # Save new configuration
            self.save_config()
            
            messagebox.showinfo("Migration Complete", message + "\n\nPlease restart the application.")
            self.result = True
            self.destroy()
        else:
            messagebox.showerror("Migration Failed", message)
            self.progress_frame.pack_forget()


def show_database_config_dialog(parent, callback=None):
    """Show the database configuration dialog."""
    return DatabaseConfigDialog(parent, callback)
