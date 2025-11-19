"""Reset database configuration back to SQLite."""
import winreg

def reset_to_sqlite():
    """Reset database type to SQLite in Windows Registry."""
    try:
        # Open registry key
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r'Software\EtsyShopManager',
            0,
            winreg.KEY_SET_VALUE
        )
        
        # Set database type to sqlite
        winreg.SetValueEx(key, 'DB_TYPE', 0, winreg.REG_SZ, 'sqlite')
        
        # Set SQLite path to default
        winreg.SetValueEx(key, 'SQLITE_PATH', 0, winreg.REG_SZ, 'etsy_inventory.db')
        
        winreg.CloseKey(key)
        
        print("✅ Successfully reset to SQLite database!")
        print("   Database file: etsy_inventory.db")
        print("\nYou can now start the application.")
        
    except FileNotFoundError:
        print("⚠️ Registry key not found - creating new one...")
        key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, r'Software\EtsyShopManager')
        winreg.SetValueEx(key, 'DB_TYPE', 0, winreg.REG_SZ, 'sqlite')
        winreg.SetValueEx(key, 'SQLITE_PATH', 0, winreg.REG_SZ, 'etsy_inventory.db')
        winreg.CloseKey(key)
        print("✅ Created registry key and set to SQLite!")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == '__main__':
    reset_to_sqlite()
