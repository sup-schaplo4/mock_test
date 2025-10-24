"""
Configuration settings for RBI Mock Test Generator
"""

import os
from pathlib import Path

# Project root directory
PROJECT_ROOT = Path(__file__).parent.parent

# Data directories
DATA_DIR = PROJECT_ROOT / "data"
GENERATED_DIR = DATA_DIR / "generated"
REFERENCE_DIR = DATA_DIR / "reference_questions"
BLUEPRINTS_DIR = DATA_DIR / "blueprints"

# Output directories
OUTPUT_DIR = PROJECT_ROOT / "generated_tests"
CHARTS_DIR = PROJECT_ROOT / "docs" / "output_charts"

# Script directories
SCRIPTS_DIR = PROJECT_ROOT / "scripts"
GENERATION_DIR = SCRIPTS_DIR / "generation"
VALIDATION_DIR = SCRIPTS_DIR / "validation"
UTILITIES_DIR = SCRIPTS_DIR / "utilities"
PDF_PROCESSING_DIR = SCRIPTS_DIR / "pdf_processing"

# API Configuration
def get_api_key(service):
    """Get API key for a specific service"""
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

# Model configurations
MODELS = {
    'openai': {
        'gpt-4o': {
            'max_tokens': 8192,
            'temperature': 0.9
        },
        'gpt-4': {
            'max_tokens': 4096,
            'temperature': 0.9
        }
    },
    'gemini': {
        'gemini-2.5-pro': {
            'max_tokens': 8192,
            'temperature': 0.9
        },
        'gemini-2.0-flash-exp': {
            'max_tokens': 4096,
            'temperature': 0.9
        }
    }
}

# Question generation settings
GENERATION_SETTINGS = {
    'batch_size': 20,
    'delay_between_batches': 5,
    'max_retries': 3,
    'rate_limit_per_minute': 15
}

# Validation settings
VALIDATION_SETTINGS = {
    'ai_check_enabled': True,
    'batch_size': 10,
    'confidence_threshold': 0.8
}
