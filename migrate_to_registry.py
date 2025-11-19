"""
Migrate credentials from .env file to Windows Registry
Run this once to transfer your existing settings
"""

from config import Config
from pathlib import Path

def migrate_from_env():
    """Migrate settings from .env file to registry."""
    env_file = Path('.env')
    
    if not env_file.exists():
        print("❌ No .env file found")
        print("\nYou can enter your credentials manually:")
        
        api_key = input("Enter API Key: ").strip()
        api_secret = input("Enter API Secret: ").strip()
        access_token = input("Enter Access Token: ").strip()
        shop_id = input("Enter Shop ID: ").strip()
        
        if all([api_key, api_secret, access_token, shop_id]):
            Config.save_etsy_credentials(api_key, api_secret, access_token, shop_id)
            print("\n✅ Credentials saved to Windows Registry!")
            print("\nRegistry Path: HKEY_CURRENT_USER\\Software\\EtsyShopManager")
            print("\nYou can now delete the .env file if you wish.")
        else:
            print("❌ Missing information - credentials not saved")
        
        return
    
    print("📄 Found .env file - migrating settings to Windows Registry...")
    
    # Read .env file
    settings = {}
    with open(env_file, 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                settings[key.strip()] = value.strip()
    
    # Extract credentials
    api_key = settings.get('ETSY_API_KEY', '')
    api_secret = settings.get('ETSY_API_SECRET', '')
    access_token = settings.get('ETSY_ACCESS_TOKEN', '')
    shop_id = settings.get('ETSY_SHOP_ID', '')
    
    if not all([api_key, api_secret, access_token, shop_id]):
        print("⚠️  .env file incomplete - some credentials missing")
        print(f"   API Key: {'✓' if api_key else '✗'}")
        print(f"   API Secret: {'✓' if api_secret else '✗'}")
        print(f"   Access Token: {'✓' if access_token else '✗'}")
        print(f"   Shop ID: {'✓' if shop_id else '✗'}")
        
        if not api_key:
            api_key = input("\nEnter API Key: ").strip()
        if not api_secret:
            api_secret = input("Enter API Secret: ").strip()
        if not access_token:
            access_token = input("Enter Access Token: ").strip()
        if not shop_id:
            shop_id = input("Enter Shop ID: ").strip()
    
    # Save to registry
    try:
        Config.save_etsy_credentials(api_key, api_secret, access_token, shop_id)
        
        # Also save other settings if present
        if 'DATABASE_URL' in settings:
            Config.save_setting('DATABASE_URL', settings['DATABASE_URL'])
        if 'PDF_OUTPUT_DIR' in settings:
            Config.save_setting('PDF_OUTPUT_DIR', settings['PDF_OUTPUT_DIR'])
        
        print("\n✅ Migration successful!")
        print("\nCredentials saved to Windows Registry:")
        print("   Location: HKEY_CURRENT_USER\\Software\\EtsyShopManager")
        print(f"   API Key: {api_key[:10]}..." if len(api_key) > 10 else api_key)
        print(f"   Shop ID: {shop_id}")
        
        print("\n📋 Current Registry Settings:")
        all_settings = Config.get_all_settings()
        for key, value in all_settings.items():
            if 'SECRET' in key or 'TOKEN' in key:
                display_value = value[:10] + '...' if len(value) > 10 else value
            else:
                display_value = value
            print(f"   {key}: {display_value}")
        
        print("\n💡 You can now delete the .env file if you wish")
        print("   Credentials are safely stored in Windows Registry")
        
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")

def view_registry_settings():
    """View current registry settings."""
    print("\n📋 Current Registry Settings:")
    print("="*50)
    
    all_settings = Config.get_all_settings()
    
    if not all_settings:
        print("   No settings found in registry")
    else:
        for key, value in all_settings.items():
            if 'SECRET' in key or 'TOKEN' in key:
                display_value = value[:10] + '...' if len(value) > 10 else value
            else:
                display_value = value
            print(f"   {key}: {display_value}")
    
    print("="*50)

def main():
    """Main function."""
    print("\n" + "="*60)
    print("  ETSY SHOP MANAGER - CREDENTIALS MIGRATION TOOL")
    print("="*60)
    print("\nThis tool migrates credentials from .env to Windows Registry")
    print("Registry is more secure and doesn't risk accidental commits")
    
    print("\nOptions:")
    print("  1. Migrate from .env file")
    print("  2. View current registry settings")
    print("  3. Enter credentials manually")
    print("  4. Clear all registry settings")
    print("  0. Exit")
    
    choice = input("\nEnter choice: ").strip()
    
    if choice == '1':
        migrate_from_env()
    elif choice == '2':
        view_registry_settings()
    elif choice == '3':
        api_key = input("\nEnter API Key: ").strip()
        api_secret = input("Enter API Secret: ").strip()
        access_token = input("Enter Access Token: ").strip()
        shop_id = input("Enter Shop ID: ").strip()
        
        if all([api_key, api_secret, access_token, shop_id]):
            Config.save_etsy_credentials(api_key, api_secret, access_token, shop_id)
            print("\n✅ Credentials saved to Windows Registry!")
            view_registry_settings()
        else:
            print("❌ Missing information - credentials not saved")
    elif choice == '4':
        confirm = input("\n⚠️  Clear all registry settings? (yes/no): ").strip().lower()
        if confirm == 'yes':
            if Config.delete_all_settings():
                print("✅ All settings cleared")
            else:
                print("❌ Failed to clear settings")
    elif choice == '0':
        print("\n👋 Goodbye!")
    else:
        print("\n❌ Invalid choice")

if __name__ == '__main__':
    main()
