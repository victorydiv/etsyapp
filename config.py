"""Configuration management for the Etsy app using Windows Registry."""
import winreg
from pathlib import Path

# Registry key path
REGISTRY_PATH = r"Software\EtsyShopManager"

class Config:
    """Application configuration stored in Windows Registry."""
    
    # Registry handle (cached)
    _reg_key = None
    
    # Etsy API Base URL (v3)
    ETSY_API_BASE_URL = 'https://openapi.etsy.com/v3/application'
    
    # Default values
    _defaults = {
        'DATABASE_URL': 'sqlite:///etsy_inventory.db',
        'PDF_OUTPUT_DIR': './output',
        'LOGO_PATH': None
    }
    
    @classmethod
    def _get_reg_key(cls, write=False):
        """Get or create registry key."""
        try:
            access = winreg.KEY_READ | winreg.KEY_WRITE if write else winreg.KEY_READ
            return winreg.OpenKey(winreg.HKEY_CURRENT_USER, REGISTRY_PATH, 0, access)
        except FileNotFoundError:
            if write:
                return winreg.CreateKey(winreg.HKEY_CURRENT_USER, REGISTRY_PATH)
            return None
    
    @classmethod
    def _get_value(cls, name, default=None):
        """Get a value from registry."""
        try:
            key = cls._get_reg_key()
            if key:
                value, _ = winreg.QueryValueEx(key, name)
                winreg.CloseKey(key)
                return value
        except (FileNotFoundError, OSError):
            pass
        return default
    
    @classmethod
    def _set_value(cls, name, value):
        """Set a value in registry."""
        try:
            key = cls._get_reg_key(write=True)
            if key:
                winreg.SetValueEx(key, name, 0, winreg.REG_SZ, str(value))
                winreg.CloseKey(key)
                return True
        except Exception as e:
            print(f"Error writing to registry: {e}")
            return False
    
    @classmethod
    def get_all_settings(cls):
        """Get all settings from registry."""
        settings = {}
        try:
            key = cls._get_reg_key()
            if key:
                i = 0
                while True:
                    try:
                        name, value, _ = winreg.EnumValue(key, i)
                        settings[name] = value
                        i += 1
                    except OSError:
                        break
                winreg.CloseKey(key)
        except:
            pass
        return settings
    
    @classmethod
    def delete_all_settings(cls):
        """Delete all settings (for uninstall/reset)."""
        try:
            winreg.DeleteKey(winreg.HKEY_CURRENT_USER, REGISTRY_PATH)
            return True
        except:
            return False
    
    # Property accessors for configuration values
    @property
    def ETSY_API_KEY(self):
        return self._get_value('ETSY_API_KEY')
    
    @property
    def ETSY_API_SECRET(self):
        return self._get_value('ETSY_API_SECRET')
    
    @property
    def ETSY_ACCESS_TOKEN(self):
        return self._get_value('ETSY_ACCESS_TOKEN')
    
    @property
    def ETSY_SHOP_ID(self):
        return self._get_value('ETSY_SHOP_ID')
    
    @property
    def DATABASE_URL(self):
        return self._get_value('DATABASE_URL', self._defaults['DATABASE_URL'])
    
    @property
    def PDF_OUTPUT_DIR(self):
        path_str = self._get_value('PDF_OUTPUT_DIR', self._defaults['PDF_OUTPUT_DIR'])
        path = Path(path_str)
        # Create output directory if it doesn't exist
        path.mkdir(parents=True, exist_ok=True)
        return path
    
    @classmethod
    def get_logo_path(cls):
        """Get the logo path if set."""
        logo_path = cls._get_value('LOGO_PATH', cls._defaults['LOGO_PATH'])
        if logo_path and Path(logo_path).exists():
            return Path(logo_path)
        return None
    
    @classmethod
    def get_shop_info(cls):
        """Get shop information for documents."""
        source = cls._get_value('SHOP_INFO_SOURCE', 'manual')
        shop_name = cls._get_value('SHOP_NAME', '')
        shop_address = cls._get_value('SHOP_ADDRESS', '')
        
        if source == 'etsy':
            # Try to fetch from Etsy
            try:
                from etsy_api import EtsyAPI
                api = EtsyAPI()
                etsy_info = api.get_shop_info()
                if etsy_info:
                    # Build address from Etsy data
                    address_parts = []
                    if etsy_info.get('street'):
                        address_parts.append(etsy_info['street'])
                    if etsy_info.get('city'):
                        city_line = etsy_info['city']
                        if etsy_info.get('state'):
                            city_line += f", {etsy_info['state']}"
                        if etsy_info.get('zip'):
                            city_line += f" {etsy_info['zip']}"
                        address_parts.append(city_line)
                    if etsy_info.get('country'):
                        address_parts.append(etsy_info['country'])
                    
                    return {
                        'shop_name': etsy_info.get('shop_name', shop_name),
                        'address': '\n'.join(address_parts) if address_parts else shop_address
                    }
            except:
                pass  # Fall back to manual
        
        # Use manual entry
        return {
            'shop_name': shop_name,
            'address': shop_address
        } if shop_name else None
    
    @classmethod
    def save_etsy_credentials(cls, api_key, api_secret, access_token, shop_id):
        """Save Etsy API credentials to registry."""
        cls._set_value('ETSY_API_KEY', api_key)
        cls._set_value('ETSY_API_SECRET', api_secret)
        cls._set_value('ETSY_ACCESS_TOKEN', access_token)
        cls._set_value('ETSY_SHOP_ID', shop_id)
    
    @classmethod
    def save_setting(cls, name, value):
        """Save a single setting."""
        return cls._set_value(name, value)
    
    @classmethod
    def validate(cls):
        """Validate that all required configuration is present."""
        instance = cls()
        required = {
            'ETSY_API_KEY': instance.ETSY_API_KEY,
            'ETSY_API_SECRET': instance.ETSY_API_SECRET,
            'ETSY_ACCESS_TOKEN': instance.ETSY_ACCESS_TOKEN,
            'ETSY_SHOP_ID': instance.ETSY_SHOP_ID
        }
        missing = [key for key, value in required.items() if not value]
        if missing:
            raise ValueError(f"Missing required configuration: {', '.join(missing)}")
        
        # Create output directory if it doesn't exist
        instance.PDF_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Create a singleton instance for easy access
Config = Config()
