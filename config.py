"""Configuration management for the Etsy app."""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    """Application configuration."""
    
    # Etsy API Configuration
    ETSY_API_KEY = os.getenv('ETSY_API_KEY')
    ETSY_API_SECRET = os.getenv('ETSY_API_SECRET')
    ETSY_ACCESS_TOKEN = os.getenv('ETSY_ACCESS_TOKEN')
    ETSY_SHOP_ID = os.getenv('ETSY_SHOP_ID')
    
    # Etsy API Base URL (v3)
    ETSY_API_BASE_URL = 'https://openapi.etsy.com/v3/application'
    
    # Database Configuration
    DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///etsy_inventory.db')
    
    # PDF Output Configuration
    PDF_OUTPUT_DIR = Path(os.getenv('PDF_OUTPUT_DIR', './output'))
    
    @classmethod
    def validate(cls):
        """Validate that all required configuration is present."""
        required = [
            'ETSY_API_KEY',
            'ETSY_API_SECRET',
            'ETSY_ACCESS_TOKEN',
            'ETSY_SHOP_ID'
        ]
        missing = [key for key in required if not getattr(cls, key)]
        if missing:
            raise ValueError(f"Missing required configuration: {', '.join(missing)}")
        
        # Create output directory if it doesn't exist
        cls.PDF_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
