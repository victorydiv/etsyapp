"""Quick script to save your Etsy credentials to the registry."""
from config import Config

# Your credentials
API_KEY = "dc6y7mtxrdlzkqdwdrzfyr37"
API_SECRET = "86bnhfm6ub"
ACCESS_TOKEN = "your_access_token_here"  # Update this when you get it
SHOP_ID = "MEWorksCreations"

# Save to registry
print("Saving credentials to Windows Registry...")
Config.save_etsy_credentials(API_KEY, API_SECRET, ACCESS_TOKEN, SHOP_ID)

print("\n✅ Credentials saved successfully!")
print("\nRegistry Location: HKEY_CURRENT_USER\\Software\\EtsyShopManager")
print("\nSaved settings:")
print(f"  API Key: {API_KEY}")
print(f"  API Secret: {API_SECRET[:5]}...")
print(f"  Access Token: {'(pending)' if ACCESS_TOKEN == 'your_access_token_here' else ACCESS_TOKEN[:10] + '...'}")
print(f"  Shop ID: {SHOP_ID}")

print("\n💡 Note: You still need to get your OAuth access token")
print("   Once you have it, run this script again with the token")
print("   OR use the Settings dialog in the GUI (⚙️ Settings > Edit Configuration)")

print("\n📋 Current Registry Settings:")
all_settings = Config.get_all_settings()
for key, value in all_settings.items():
    if 'SECRET' in key or 'TOKEN' in key:
        display_value = value[:10] + '...' if len(value) > 10 else value
    else:
        display_value = value
    print(f"   {key}: {display_value}")
