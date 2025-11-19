"""Etsy API client for managing listings, inventory, and orders."""
import requests
from typing import Dict, List, Optional
from config import Config

class EtsyAPIClient:
    """Client for interacting with Etsy API v3."""
    
    def __init__(self):
        """Initialize the Etsy API client."""
        self.api_key = Config.ETSY_API_KEY
        self.access_token = Config.ETSY_ACCESS_TOKEN
        self.shop_id = Config.ETSY_SHOP_ID
        self.base_url = Config.ETSY_API_BASE_URL
        
    def _get_headers(self) -> Dict[str, str]:
        """Get headers for API requests."""
        return {
            'x-api-key': self.api_key,
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }
    
    def _make_request(self, method: str, endpoint: str, **kwargs) -> Dict:
        """Make a request to the Etsy API."""
        url = f"{self.base_url}/{endpoint}"
        headers = self._get_headers()
        
        response = requests.request(method, url, headers=headers, **kwargs)
        response.raise_for_status()
        return response.json()
    
    # Listing Management
    def get_shop_listings(self, state: str = 'active', limit: int = 100) -> List[Dict]:
        """Get all listings for the shop."""
        endpoint = f"shops/{self.shop_id}/listings/{state}"
        params = {'limit': limit}
        result = self._make_request('GET', endpoint, params=params)
        return result.get('results', [])
    
    def get_listing(self, listing_id: str) -> Dict:
        """Get a specific listing by ID."""
        endpoint = f"listings/{listing_id}"
        return self._make_request('GET', endpoint)
    
    def update_listing(self, listing_id: str, data: Dict) -> Dict:
        """Update a listing."""
        endpoint = f"shops/{self.shop_id}/listings/{listing_id}"
        return self._make_request('PATCH', endpoint, json=data)
    
    def create_listing(self, data: Dict) -> Dict:
        """Create a new listing."""
        endpoint = f"shops/{self.shop_id}/listings"
        return self._make_request('POST', endpoint, json=data)
    
    # Inventory Management
    def get_listing_inventory(self, listing_id: str) -> Dict:
        """Get inventory for a specific listing."""
        endpoint = f"listings/{listing_id}/inventory"
        return self._make_request('GET', endpoint)
    
    def update_listing_inventory(self, listing_id: str, products: List[Dict]) -> Dict:
        """Update inventory for a listing."""
        endpoint = f"listings/{listing_id}/inventory"
        data = {'products': products}
        return self._make_request('PUT', endpoint, json=data)
    
    # Order Management
    def get_shop_receipts(self, limit: int = 100, offset: int = 0) -> List[Dict]:
        """Get shop receipts (orders)."""
        endpoint = f"shops/{self.shop_id}/receipts"
        params = {'limit': limit, 'offset': offset}
        result = self._make_request('GET', endpoint, params=params)
        return result.get('results', [])
    
    def get_receipt(self, receipt_id: str) -> Dict:
        """Get a specific receipt by ID."""
        endpoint = f"shops/{self.shop_id}/receipts/{receipt_id}"
        return self._make_request('GET', endpoint)
    
    def get_receipt_transactions(self, receipt_id: str) -> List[Dict]:
        """Get transactions (line items) for a receipt."""
        endpoint = f"shops/{self.shop_id}/receipts/{receipt_id}/transactions"
        result = self._make_request('GET', endpoint)
        return result.get('results', [])
    
    def update_receipt_tracking(self, receipt_id: str, tracking_code: str, carrier_name: str) -> Dict:
        """Update tracking information for a receipt."""
        endpoint = f"shops/{self.shop_id}/receipts/{receipt_id}/tracking"
        data = {
            'tracking_code': tracking_code,
            'carrier_name': carrier_name
        }
        return self._make_request('POST', endpoint, json=data)
    
    # Shop Information
    def get_shop(self) -> Dict:
        """Get shop information."""
        endpoint = f"shops/{self.shop_id}"
        return self._make_request('GET', endpoint)
    
    def get_shop_info(self) -> Dict:
        """Get formatted shop information for documents."""
        shop_data = self.get_shop()
        
        # Extract shop name
        shop_name = shop_data.get('shop_name', '')
        
        # Build address from components
        address_parts = []
        if 'street' in shop_data and shop_data['street']:
            address_parts.append(shop_data['street'])
        if 'city' in shop_data and shop_data['city']:
            city_line = shop_data['city']
            if 'state' in shop_data and shop_data['state']:
                city_line += f", {shop_data['state']}"
            if 'zip' in shop_data and shop_data['zip']:
                city_line += f" {shop_data['zip']}"
            address_parts.append(city_line)
        if 'country_iso' in shop_data and shop_data['country_iso']:
            address_parts.append(shop_data['country_iso'])
        
        address = '\n'.join(address_parts)
        
        return {
            'shop_name': shop_name,
            'address': address
        }
