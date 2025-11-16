"""Utility functions for the Etsy app."""
from datetime import datetime
from typing import Dict, Any
import json

def format_currency(amount: float, currency: str = 'USD') -> str:
    """Format a currency amount."""
    symbols = {
        'USD': '$',
        'EUR': '€',
        'GBP': '£',
        'CAD': 'C$',
        'AUD': 'A$'
    }
    symbol = symbols.get(currency, '$')
    return f"{symbol}{amount:.2f}"

def format_date(dt: datetime, format_str: str = '%Y-%m-%d') -> str:
    """Format a datetime object."""
    if dt is None:
        return 'N/A'
    return dt.strftime(format_str)

def parse_etsy_timestamp(timestamp: int) -> datetime:
    """Convert Etsy timestamp to datetime."""
    return datetime.fromtimestamp(timestamp)

def format_address(address_dict: Dict[str, str]) -> str:
    """Format an address dictionary to a string."""
    parts = []
    if address_dict.get('first_line'):
        parts.append(address_dict['first_line'])
    if address_dict.get('second_line'):
        parts.append(address_dict['second_line'])
    
    city_state_zip = []
    if address_dict.get('city'):
        city_state_zip.append(address_dict['city'])
    if address_dict.get('state'):
        city_state_zip.append(address_dict['state'])
    if address_dict.get('zip'):
        city_state_zip.append(address_dict['zip'])
    
    if city_state_zip:
        parts.append(', '.join(city_state_zip))
    
    if address_dict.get('country'):
        parts.append(address_dict['country'])
    
    return '\n'.join(parts)

def truncate_string(text: str, max_length: int, suffix: str = '...') -> str:
    """Truncate a string to a maximum length."""
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix

def safe_get(dictionary: Dict, *keys, default=None) -> Any:
    """Safely get nested dictionary values."""
    result = dictionary
    for key in keys:
        if isinstance(result, dict):
            result = result.get(key)
            if result is None:
                return default
        else:
            return default
    return result if result is not None else default

def export_to_json(data: Any, filename: str) -> str:
    """Export data to a JSON file."""
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, default=str)
    return filename

def validate_sku(sku: str) -> bool:
    """Validate SKU format."""
    if not sku:
        return False
    # Basic validation - alphanumeric and hyphens
    return all(c.isalnum() or c in '-_' for c in sku)

def calculate_profit(price: float, cost: float, quantity: int = 1) -> float:
    """Calculate profit for an item."""
    return (price - cost) * quantity

def get_status_emoji(status: str) -> str:
    """Get emoji for order status."""
    status_emojis = {
        'pending': '⏳',
        'packed': '📦',
        'shipped': '🚚',
        'delivered': '✅',
        'cancelled': '❌',
        'refunded': '💰'
    }
    return status_emojis.get(status.lower(), '❓')

def format_phone(phone: str) -> str:
    """Format phone number."""
    # Remove all non-numeric characters
    digits = ''.join(filter(str.isdigit, phone))
    
    if len(digits) == 10:
        return f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"
    elif len(digits) == 11 and digits[0] == '1':
        return f"+1 ({digits[1:4]}) {digits[4:7]}-{digits[7:]}"
    return phone

def batch_list(items: list, batch_size: int = 100):
    """Split a list into batches."""
    for i in range(0, len(items), batch_size):
        yield items[i:i + batch_size]

class ProgressTracker:
    """Simple progress tracker for operations."""
    
    def __init__(self, total: int, description: str = "Processing"):
        self.total = total
        self.current = 0
        self.description = description
    
    def update(self, increment: int = 1):
        """Update progress."""
        self.current += increment
        self.display()
    
    def display(self):
        """Display progress."""
        percentage = (self.current / self.total * 100) if self.total > 0 else 0
        bar_length = 30
        filled = int(bar_length * self.current / self.total) if self.total > 0 else 0
        bar = '█' * filled + '░' * (bar_length - filled)
        print(f"\r{self.description}: [{bar}] {percentage:.1f}% ({self.current}/{self.total})", end='', flush=True)
    
    def complete(self):
        """Mark as complete."""
        self.current = self.total
        self.display()
        print()  # New line

# Color codes for terminal output
class Colors:
    """ANSI color codes for terminal output."""
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    
    @staticmethod
    def colored(text: str, color: str) -> str:
        """Return colored text."""
        return f"{color}{text}{Colors.ENDC}"
