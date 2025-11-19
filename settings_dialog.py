"""Settings dialog for configuring Etsy API credentials."""
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from config import Config
from pathlib import Path
from PIL import Image as PILImage

class SettingsDialog:
    """Dialog for editing application settings."""
    
    def __init__(self, parent, on_save_callback=None):
        """Initialize the settings dialog."""
        self.parent = parent
        self.on_save_callback = on_save_callback
        
        # Create dialog window
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Application Settings")
        self.dialog.geometry("700x750")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Center the dialog
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - (700 // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (750 // 2)
        self.dialog.geometry(f"700x750+{x}+{y}")
        
        self.create_widgets()
        self.load_settings()
    
    def create_widgets(self):
        """Create dialog widgets."""
        # Button frame at bottom (pack first so it stays at bottom)
        button_frame = ttk.Frame(self.dialog)
        button_frame.pack(fill='x', padx=20, pady=10, side='bottom')
        
        ttk.Button(button_frame, text="Save", 
                  command=self.save_settings, 
                  style='Action.TButton').pack(side='right', padx=5)
        ttk.Button(button_frame, text="Cancel", 
                  command=self.dialog.destroy).pack(side='right', padx=5)
        ttk.Button(button_frame, text="Clear All", 
                  command=self.clear_settings).pack(side='left', padx=5)
        ttk.Button(button_frame, text="Test Connection", 
                  command=self.test_connection).pack(side='left', padx=5)
        
        # Separator above buttons
        ttk.Separator(self.dialog, orient='horizontal').pack(fill='x', padx=20, pady=5, side='bottom')
        
        # Create main container frame for scrollable content
        main_container = ttk.Frame(self.dialog)
        main_container.pack(fill='both', expand=True)
        
        # Create canvas with scrollbar for scrollable content
        self.canvas = tk.Canvas(main_container, highlightthickness=0)
        scrollbar = ttk.Scrollbar(main_container, orient="vertical", command=self.canvas.yview)
        scrollable_frame = ttk.Frame(self.canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        
        self.canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=scrollbar.set)
        
        # Pack canvas and scrollbar
        self.canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Enable mousewheel scrolling on the canvas only
        def _on_mousewheel(event):
            self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        self.canvas.bind("<MouseWheel>", _on_mousewheel)
        
        # Make sure mousewheel works when mouse is over the dialog
        self.dialog.bind("<MouseWheel>", _on_mousewheel)
        
        # Header
        header_frame = ttk.Frame(scrollable_frame)
        header_frame.pack(fill='x', padx=20, pady=10)
        
        ttk.Label(header_frame, text="Etsy API Configuration", 
                 font=('Segoe UI', 14, 'bold')).pack(anchor='w')
        ttk.Label(header_frame, text="Enter your Etsy API credentials to enable sync features",
                 foreground='gray').pack(anchor='w')
        
        # Form frame
        form_frame = ttk.Frame(scrollable_frame)
        form_frame.pack(fill='both', expand=True, padx=20, pady=10)
        
        self.fields = {}
        
        # API Key
        row = 0
        ttk.Label(form_frame, text="API Key (Keystring):").grid(
            row=row, column=0, sticky='w', pady=5)
        self.fields['api_key'] = ttk.Entry(form_frame, width=50)
        self.fields['api_key'].grid(row=row, column=1, pady=5, sticky='ew')
        
        # API Secret
        row += 1
        ttk.Label(form_frame, text="API Secret (Shared Secret):").grid(
            row=row, column=0, sticky='w', pady=5)
        self.fields['api_secret'] = ttk.Entry(form_frame, width=50, show='*')
        self.fields['api_secret'].grid(row=row, column=1, pady=5, sticky='ew')
        
        # Access Token
        row += 1
        ttk.Label(form_frame, text="Access Token:").grid(
            row=row, column=0, sticky='w', pady=5)
        self.fields['access_token'] = ttk.Entry(form_frame, width=50, show='*')
        self.fields['access_token'].grid(row=row, column=1, pady=5, sticky='ew')
        
        # Shop ID
        row += 1
        ttk.Label(form_frame, text="Shop ID:").grid(
            row=row, column=0, sticky='w', pady=5)
        self.fields['shop_id'] = ttk.Entry(form_frame, width=50)
        self.fields['shop_id'].grid(row=row, column=1, pady=5, sticky='ew')
        
        # Separator
        row += 1
        ttk.Separator(form_frame, orient='horizontal').grid(
            row=row, column=0, columnspan=2, sticky='ew', pady=15)
        
        # Document Settings Section
        row += 1
        ttk.Label(form_frame, text="Document Settings", 
                 font=('Segoe UI', 10, 'bold')).grid(
            row=row, column=0, columnspan=2, sticky='w', pady=(5, 10))
        
        # Logo
        row += 1
        ttk.Label(form_frame, text="Logo Image:").grid(
            row=row, column=0, sticky='w', pady=5)
        
        logo_frame = ttk.Frame(form_frame)
        logo_frame.grid(row=row, column=1, pady=5, sticky='ew')
        
        self.logo_path_var = tk.StringVar()
        logo_entry = ttk.Entry(logo_frame, textvariable=self.logo_path_var, state='readonly')
        logo_entry.pack(side='left', fill='x', expand=True, padx=(0, 5))
        
        ttk.Button(logo_frame, text="Browse...", 
                  command=self.browse_logo).pack(side='left', padx=2)
        ttk.Button(logo_frame, text="Clear", 
                  command=self.clear_logo).pack(side='left', padx=2)
        
        row += 1
        ttk.Label(form_frame, text="(Logo will appear on packing lists and invoices)",
                 foreground='gray', font=('Segoe UI', 8)).grid(
            row=row, column=1, sticky='w', pady=(0, 5))
        
        # Shop Information Section
        row += 1
        ttk.Separator(form_frame, orient='horizontal').grid(
            row=row, column=0, columnspan=2, sticky='ew', pady=15)
        
        row += 1
        ttk.Label(form_frame, text="Shop Information (for invoices)", 
                 font=('Segoe UI', 10, 'bold')).grid(
            row=row, column=0, columnspan=2, sticky='w', pady=(5, 10))
        
        # Shop info source toggle
        row += 1
        ttk.Label(form_frame, text="Shop Info Source:").grid(
            row=row, column=0, sticky='w', pady=5)
        
        source_frame = ttk.Frame(form_frame)
        source_frame.grid(row=row, column=1, pady=5, sticky='w')
        
        self.shop_info_source_var = tk.StringVar(value="manual")
        ttk.Radiobutton(source_frame, text="Manual Entry", 
                       variable=self.shop_info_source_var, 
                       value="manual",
                       command=self.toggle_shop_info_source).pack(side='left', padx=5)
        ttk.Radiobutton(source_frame, text="Fetch from Etsy", 
                       variable=self.shop_info_source_var, 
                       value="etsy",
                       command=self.toggle_shop_info_source).pack(side='left', padx=5)
        
        # Shop Name
        row += 1
        ttk.Label(form_frame, text="Shop Name:").grid(
            row=row, column=0, sticky='w', pady=5)
        self.shop_name_var = tk.StringVar()
        self.shop_name_entry = ttk.Entry(form_frame, textvariable=self.shop_name_var, width=40)
        self.shop_name_entry.grid(row=row, column=1, sticky='ew', pady=5)
        
        # Shop Address
        row += 1
        ttk.Label(form_frame, text="Shop Address:").grid(
            row=row, column=0, sticky='nw', pady=5)
        self.shop_address_text = tk.Text(form_frame, height=3, width=40)
        self.shop_address_text.grid(row=row, column=1, sticky='ew', pady=5)
        
        row += 1
        ttk.Button(form_frame, text="🔄 Fetch from Etsy Now", 
                  command=self.fetch_shop_info_from_etsy).grid(
            row=row, column=1, sticky='w', pady=5)
        
        form_frame.columnconfigure(1, weight=1)
        
        # Help text
        row += 1
        help_frame = ttk.Frame(form_frame)
        help_frame.grid(row=row, column=0, columnspan=2, sticky='ew', pady=20)
        
        help_text = """
How to get your Etsy API credentials:
1. Go to https://www.etsy.com/developers/
2. Create a new app or use an existing one
3. Copy the Keystring (API Key) and Shared Secret
4. Generate an OAuth access token
5. Your Shop ID is in your shop URL or from API

Note: Credentials are stored securely in Windows Registry
        """
        ttk.Label(help_frame, text=help_text.strip(), 
                 foreground='gray', justify='left').pack(anchor='w')
    
    def load_settings(self):
        """Load current settings from registry."""
        self.fields['api_key'].insert(0, Config.ETSY_API_KEY or '')
        self.fields['api_secret'].insert(0, Config.ETSY_API_SECRET or '')
        self.fields['access_token'].insert(0, Config.ETSY_ACCESS_TOKEN or '')
        self.fields['shop_id'].insert(0, Config.ETSY_SHOP_ID or '')
        
        # Load logo path
        logo_path = Config.get_logo_path()
        if logo_path:
            self.logo_path_var.set(str(logo_path))
        
        # Load shop info
        self.shop_info_source_var.set(Config._get_value('SHOP_INFO_SOURCE', 'manual'))
        self.shop_name_var.set(Config._get_value('SHOP_NAME', ''))
        shop_address = Config._get_value('SHOP_ADDRESS', '')
        if shop_address:
            self.shop_address_text.insert(1.0, shop_address)
        
        self.toggle_shop_info_source()
    
    def toggle_shop_info_source(self):
        """Enable/disable shop info fields based on source."""
        if self.shop_info_source_var.get() == "manual":
            self.shop_name_entry.config(state='normal')
            self.shop_address_text.config(state='normal')
        else:
            self.shop_name_entry.config(state='readonly')
            self.shop_address_text.config(state='disabled')
    
    def fetch_shop_info_from_etsy(self):
        """Fetch shop info from Etsy API."""
        try:
            from etsy_api import EtsyAPI
            api = EtsyAPI()
            shop_info = api.get_shop_info()
            
            if shop_info:
                self.shop_name_var.set(shop_info.get('shop_name', ''))
                
                # Build address from shop data
                address_parts = []
                if shop_info.get('street'):
                    address_parts.append(shop_info['street'])
                if shop_info.get('city'):
                    city_line = shop_info['city']
                    if shop_info.get('state'):
                        city_line += f", {shop_info['state']}"
                    if shop_info.get('zip'):
                        city_line += f" {shop_info['zip']}"
                    address_parts.append(city_line)
                if shop_info.get('country'):
                    address_parts.append(shop_info['country'])
                
                address = '\n'.join(address_parts)
                self.shop_address_text.delete(1.0, tk.END)
                self.shop_address_text.insert(1.0, address)
                
                messagebox.showinfo("Success", "Shop information fetched from Etsy!")
            else:
                messagebox.showerror("Error", "Could not fetch shop information from Etsy")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to fetch shop info: {e}")
    
    def browse_logo(self):
        """Browse for a logo image file."""
        file_path = filedialog.askopenfilename(
            title="Select Logo Image",
            filetypes=[
                ("Image files", "*.png *.jpg *.jpeg *.gif *.bmp"),
                ("All files", "*.*")
            ]
        )
        if file_path:
            # Validate it's an image
            try:
                img = PILImage.open(file_path)
                img.verify()
                self.logo_path_var.set(file_path)
            except Exception as e:
                messagebox.showerror("Invalid Image", 
                                   f"Could not open image file: {e}")
    
    def clear_logo(self):
        """Clear the logo setting."""
        self.logo_path_var.set('')
    
    def save_settings(self):
        """Save settings to registry."""
        api_key = self.fields['api_key'].get().strip()
        api_secret = self.fields['api_secret'].get().strip()
        access_token = self.fields['access_token'].get().strip()
        shop_id = self.fields['shop_id'].get().strip()
        
        if not all([api_key, api_secret, access_token, shop_id]):
            messagebox.showwarning("Missing Information", 
                                 "Please fill in all Etsy API fields")
            return
        
        try:
            # Save Etsy credentials
            Config.save_etsy_credentials(api_key, api_secret, access_token, shop_id)
            
            # Save logo path
            logo_path = self.logo_path_var.get().strip()
            if logo_path:
                Config.save_setting('LOGO_PATH', logo_path)
            else:
                # Clear logo if empty
                Config.save_setting('LOGO_PATH', '')
            
            # Save shop info
            Config.save_setting('SHOP_INFO_SOURCE', self.shop_info_source_var.get())
            Config.save_setting('SHOP_NAME', self.shop_name_var.get().strip())
            shop_address = self.shop_address_text.get(1.0, tk.END).strip()
            Config.save_setting('SHOP_ADDRESS', shop_address)
            
            messagebox.showinfo("Success", 
                              "Settings saved successfully!")
            
            if self.on_save_callback:
                self.on_save_callback()
            
            self.dialog.destroy()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save settings: {str(e)}")
    
    def clear_settings(self):
        """Clear all settings."""
        if messagebox.askyesno("Confirm", 
                              "Are you sure you want to clear all settings?\n"
                              "This will remove all Etsy API credentials."):
            try:
                Config.delete_all_settings()
                messagebox.showinfo("Success", "All settings cleared")
                self.dialog.destroy()
                
                if self.on_save_callback:
                    self.on_save_callback()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to clear settings: {str(e)}")
    
    def test_connection(self):
        """Test the Etsy API connection."""
        api_key = self.fields['api_key'].get().strip()
        access_token = self.fields['access_token'].get().strip()
        
        if not api_key or not access_token:
            messagebox.showwarning("Missing Information", 
                                 "API Key and Access Token are required for testing")
            return
        
        # Try a simple API call
        try:
            import requests
            
            headers = {
                'x-api-key': api_key,
                'Authorization': f'Bearer {access_token}'
            }
            
            response = requests.get(
                'https://openapi.etsy.com/v3/application/shops/' + 
                self.fields['shop_id'].get().strip(),
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                shop_data = response.json()
                messagebox.showinfo("Connection Successful", 
                                  f"✅ Successfully connected to Etsy!\n\n"
                                  f"Shop: {shop_data.get('shop_name', 'Unknown')}")
            elif response.status_code == 401:
                messagebox.showerror("Authentication Failed", 
                                   "❌ Invalid credentials\n\n"
                                   "Please check your API Key and Access Token")
            elif response.status_code == 404:
                messagebox.showerror("Shop Not Found", 
                                   "❌ Shop ID not found\n\n"
                                   "Please check your Shop ID")
            else:
                messagebox.showerror("Connection Failed", 
                                   f"❌ API returned error: {response.status_code}\n\n"
                                   f"{response.text}")
        except requests.exceptions.Timeout:
            messagebox.showerror("Timeout", 
                               "❌ Connection timed out\n\n"
                               "Please check your internet connection")
        except Exception as e:
            messagebox.showerror("Error", 
                               f"❌ Connection failed:\n\n{str(e)}")


def show_settings_dialog(parent, callback=None):
    """Show the settings dialog."""
    SettingsDialog(parent, callback)
