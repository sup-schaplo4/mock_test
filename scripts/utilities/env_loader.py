"""
Environment variable loader utility
Loads environment variables from .env file if it exists
"""

import os
from pathlib import Path

def load_env():
    """Load environment variables from .env file if it exists"""
    env_file = Path(__file__).parent.parent.parent / '.env'
    if env_file.exists():
        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key] = value

def get_api_key(service):
    """Get API key for a specific service"""
    load_env()
    
    key_mapping = {
        'openai': 'OPENAI_API_KEY',
        'gemini': 'GEMINI_API_KEY',
        'adobe_client_id': 'ADOBE_CLIENT_ID',
        'adobe_client_secret': 'ADOBE_CLIENT_SECRET',
        'adobe_org_id': 'ADOBE_ORGANIZATION_ID'
    }
    
    env_key = key_mapping.get(service.lower())
    if not env_key:
        raise ValueError(f"Unknown service: {service}")
    
    value = os.environ.get(env_key)
    if not value:
        raise ValueError(f"❌ Please set {env_key} environment variable")
    
    return value
