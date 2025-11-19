"""
Helper script to obtain Etsy OAuth 2.0 access token.
This script will guide you through the OAuth flow to get your access token.
"""

import webbrowser
import secrets
from urllib.parse import urlencode
from config import Config

def generate_oauth_url():
    """Generate the OAuth authorization URL."""
    
    # Generate code verifier and challenge for PKCE
    code_verifier = secrets.token_urlsafe(32)
    
    # OAuth parameters
    params = {
        'response_type': 'code',
        'client_id': Config.ETSY_API_KEY,
        'redirect_uri': 'urn:ietf:wg:oauth:2.0:oob',  # For apps without redirect
        'scope': 'transactions_r transactions_w listings_r listings_w email_r address_r',
        'state': secrets.token_urlsafe(16),
        'code_challenge': code_verifier,
        'code_challenge_method': 'S256'
    }
    
    auth_url = f"https://www.etsy.com/oauth/connect?{urlencode(params)}"
    
    print("\n" + "="*70)
    print("ETSY OAUTH 2.0 AUTHORIZATION")
    print("="*70)
    print("\n📋 Your API Key:", Config.ETSY_API_KEY)
    print("📋 Shop ID:", Config.ETSY_SHOP_ID)
    
    print("\n" + "="*70)
    print("STEP 1: Authorize the Application")
    print("="*70)
    print("\nI'll open a browser window to Etsy's authorization page.")
    print("Please follow these steps:")
    print("\n1. Log in to your Etsy account if prompted")
    print("2. Review the permissions requested")
    print("3. Click 'Allow Access' to authorize the application")
    print("4. You'll see an authorization code - COPY IT!")
    print("5. Come back here and paste the code")
    
    input("\nPress Enter to open the authorization page in your browser...")
    
    try:
        webbrowser.open(auth_url)
        print("\n✅ Browser opened. If it didn't open, copy this URL:")
        print(f"\n{auth_url}\n")
    except:
        print("\n⚠️  Couldn't open browser automatically. Please copy and paste this URL:")
        print(f"\n{auth_url}\n")
    
    print("\n" + "="*70)
    print("STEP 2: Exchange Code for Access Token")
    print("="*70)
    
    auth_code = input("\nPaste the authorization code here: ").strip()
    
    if not auth_code:
        print("❌ No code provided. Exiting.")
        return
    
    print("\n" + "="*70)
    print("STEP 3: Get Your Access Token")
    print("="*70)
    print("\nNow we need to exchange the authorization code for an access token.")
    print("You'll need to make a POST request to Etsy's token endpoint.")
    print("\nUse this curl command (or use Postman/similar tool):\n")
    
    print("curl -X POST 'https://api.etsy.com/v3/public/oauth/token' \\")
    print(f"  -d 'grant_type=authorization_code' \\")
    print(f"  -d 'client_id={Config.ETSY_API_KEY}' \\")
    print(f"  -d 'redirect_uri=urn:ietf:wg:oauth:2.0:oob' \\")
    print(f"  -d 'code={auth_code}' \\")
    print(f"  -d 'code_verifier={code_verifier}'")
    
    print("\n" + "="*70)
    print("\nOR use this Python code:")
    print("="*70)
    print(f"""
import requests

response = requests.post('https://api.etsy.com/v3/public/oauth/token', data={{
    'grant_type': 'authorization_code',
    'client_id': '{Config.ETSY_API_KEY}',
    'redirect_uri': 'urn:ietf:wg:oauth:2.0:oob',
    'code': '{auth_code}',
    'code_verifier': '{code_verifier}'
}})

print(response.json())
""")
    
    print("\n" + "="*70)
    print("STEP 4: Update Your .env File")
    print("="*70)
    print("\nOnce you get the response, copy the 'access_token' value")
    print("and update your .env file:")
    print("\nETSY_ACCESS_TOKEN=your_actual_access_token_here")
    print("\n" + "="*70)
    
    # Try to get the token programmatically
    try:
        import requests
        
        print("\n💡 Would you like me to try getting the token automatically? (y/n): ", end='')
        choice = input().strip().lower()
        
        if choice == 'y':
            response = requests.post('https://api.etsy.com/v3/public/oauth/token', data={
                'grant_type': 'authorization_code',
                'client_id': Config.ETSY_API_KEY,
                'redirect_uri': 'urn:ietf:wg:oauth:2.0:oob',
                'code': auth_code,
                'code_verifier': code_verifier
            })
            
            if response.status_code == 200:
                token_data = response.json()
                access_token = token_data.get('access_token')
                
                if access_token:
                    print(f"\n✅ SUCCESS! Your access token is:")
                    print(f"\n{access_token}\n")
                    
                    # Update .env file
                    update_choice = input("Would you like me to update your .env file? (y/n): ").strip().lower()
                    if update_choice == 'y':
                        with open('.env', 'r') as f:
                            content = f.read()
                        
                        content = content.replace('ETSY_ACCESS_TOKEN=your_access_token_here', 
                                                 f'ETSY_ACCESS_TOKEN={access_token}')
                        
                        with open('.env', 'w') as f:
                            f.write(content)
                        
                        print("\n✅ .env file updated successfully!")
                        print("🎉 You're all set! Run 'python main.py' to start the app!")
                else:
                    print("\n❌ Couldn't find access token in response")
                    print("Response:", response.json())
            else:
                print(f"\n❌ Error: {response.status_code}")
                print("Response:", response.text)
                print("\nPlease use the manual method above.")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nPlease use the manual method shown above.")

def simple_token_exchange():
    """Simpler method - just exchange the code."""
    print("\n" + "="*70)
    print("SIMPLE TOKEN EXCHANGE")
    print("="*70)
    
    print("\nFirst, get your authorization code:")
    print("1. Go to: https://www.etsy.com/oauth/connect")
    print("2. Add these parameters:")
    print(f"   - response_type: code")
    print(f"   - client_id: {Config.ETSY_API_KEY}")
    print(f"   - redirect_uri: urn:ietf:wg:oauth:2.0:oob")
    print(f"   - scope: transactions_r transactions_w listings_r listings_w")
    print(f"   - state: random_string")
    
    auth_code = input("\nEnter the authorization code you received: ").strip()
    
    if not auth_code:
        print("No code provided.")
        return
    
    try:
        import requests
        
        code_verifier = secrets.token_urlsafe(32)
        
        response = requests.post('https://api.etsy.com/v3/public/oauth/token', data={
            'grant_type': 'authorization_code',
            'client_id': Config.ETSY_API_KEY,
            'redirect_uri': 'urn:ietf:wg:oauth:2.0:oob',
            'code': auth_code,
            'code_verifier': code_verifier
        })
        
        print("\nResponse:", response.status_code)
        print(response.json())
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == '__main__':
    try:
        generate_oauth_url()
    except KeyboardInterrupt:
        print("\n\n👋 Cancelled by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nTrying simple method...")
        simple_token_exchange()
