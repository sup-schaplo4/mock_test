"""
Setup script for RBI Mock Test Generator
"""

import os
import sys
from pathlib import Path

def setup_environment():
    """Set up the environment for the project"""
    
    # Check if .env file exists
    env_file = Path('.env')
    if not env_file.exists():
        print("❌ .env file not found!")
        print("Please copy .env.example to .env and fill in your API keys:")
        print("cp .env.example .env")
        return False
    
    # Load environment variables
    try:
        from dotenv import load_dotenv
        load_dotenv()
        print("✅ Environment variables loaded")
    except ImportError:
        print("⚠️  python-dotenv not installed. Install with: pip install python-dotenv")
        return False
    
    # Check required API keys
    required_keys = [
        'OPENAI_API_KEY',
        'GEMINI_API_KEY',
        'ADOBE_CLIENT_ID',
        'ADOBE_CLIENT_SECRET'
    ]
    
    missing_keys = []
    for key in required_keys:
        if not os.environ.get(key):
            missing_keys.append(key)
    
    if missing_keys:
        print(f"❌ Missing required environment variables: {', '.join(missing_keys)}")
        return False
    
    print("✅ All required environment variables are set")
    return True

def create_directories():
    """Create necessary directories"""
    directories = [
        'data/generated/checkpoints',
        'data/generated/english_questions',
        'data/generated/ga_questions',
        'data/generated/master_questions',
        'data/generated/quant_questions',
        'data/generated/reasoning_questions',
        'data/generated/tests',
        'generated_tests/commercial_series',
        'generated_tests/quizmaker_ready',
        'docs/prompts',
        'docs/rbi_prev_paper',
        'docs/rbi_txt',
        'docs/output_charts'
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
    
    print("✅ Directories created")

def main():
    """Main setup function"""
    print("🚀 Setting up RBI Mock Test Generator...")
    
    # Create directories
    create_directories()
    
    # Setup environment
    if not setup_environment():
        print("❌ Setup failed. Please fix the issues above and try again.")
        sys.exit(1)
    
    print("✅ Setup completed successfully!")
    print("\nNext steps:")
    print("1. Run generation scripts to create questions")
    print("2. Use validation scripts to check question quality")
    print("3. Deploy the practice platform")

if __name__ == "__main__":
    main()
