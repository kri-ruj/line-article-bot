#!/usr/bin/env python3
"""
Test script to verify LINE Article Bot setup
Run this to check if everything is configured correctly
"""

import os
import sys
from dotenv import load_dotenv
import json

# Load environment variables
load_dotenv()

print("=" * 60)
print("LINE Article Bot - Setup Verification")
print("=" * 60)

# Check Python version
print(f"\n[OK] Python version: {sys.version}")

# Check required files
print("\n[FILES] Checking required files:")
required_files = [
    '.env',
    'app.py',
    'article_extractor.py',
    'google_sheets.py',
    'message_templates.py'
]

for file in required_files:
    if os.path.exists(file):
        print(f"  [OK] {file} exists")
    else:
        print(f"  [X] {file} NOT FOUND")

# Check environment variables
print("\n[ENV] Checking environment variables:")
env_vars = {
    'LINE_CHANNEL_ACCESS_TOKEN': os.getenv('LINE_CHANNEL_ACCESS_TOKEN'),
    'LINE_CHANNEL_SECRET': os.getenv('LINE_CHANNEL_SECRET'),
    'GOOGLE_SHEETS_ID': os.getenv('GOOGLE_SHEETS_ID'),
    'SHEET_NAME': os.getenv('SHEET_NAME', 'Articles'),
    'GOOGLE_CREDENTIALS_PATH': os.getenv('GOOGLE_CREDENTIALS_PATH', 'credentials.json')
}

all_configured = True
for var, value in env_vars.items():
    if value and value not in ['your_line_channel_access_token_here', 
                               'your_line_channel_secret_here', 
                               'your_google_sheets_id_here']:
        if var in ['LINE_CHANNEL_ACCESS_TOKEN', 'LINE_CHANNEL_SECRET']:
            print(f"  [OK] {var}: ***{value[-4:]}")
        else:
            print(f"  [OK] {var}: {value}")
    else:
        print(f"  [X] {var}: NOT CONFIGURED")
        all_configured = False

# Check Google credentials file
print("\n[GOOGLE] Checking Google credentials:")
creds_path = os.getenv('GOOGLE_CREDENTIALS_PATH', 'credentials.json')
if os.path.exists(creds_path):
    print(f"  [OK] {creds_path} exists")
    try:
        with open(creds_path, 'r') as f:
            creds = json.load(f)
            if 'client_email' in creds:
                print(f"  [OK] Service account: {creds['client_email']}")
            else:
                print(f"  [X] Invalid credentials file format")
    except Exception as e:
        print(f"  [X] Error reading credentials: {e}")
else:
    print(f"  [X] {creds_path} NOT FOUND")
    print(f"     Download from Google Cloud Console and save as '{creds_path}'")

# Check Python packages
print("\n[PACKAGES] Checking required packages:")
packages = {
    'flask': 'Flask',
    'linebot': 'line-bot-sdk',
    'bs4': 'beautifulsoup4',
    'requests': 'requests',
    'google.auth': 'google-auth',
    'googleapiclient': 'google-api-python-client',
    'dotenv': 'python-dotenv'
}

missing_packages = []
for module, package in packages.items():
    try:
        __import__(module)
        print(f"  [OK] {package} installed")
    except ImportError:
        print(f"  [X] {package} NOT INSTALLED")
        missing_packages.append(package)

# Summary
print("\n" + "=" * 60)
print("SETUP SUMMARY")
print("=" * 60)

if all_configured and not missing_packages and os.path.exists(creds_path):
    print("\n[SUCCESS] Everything is configured! You can run the bot.")
    print("\nNext steps:")
    print("1. Run: python app.py")
    print("2. In another terminal: ngrok http 5000")
    print("3. Set webhook URL in LINE Console")
    print("4. Test by sending a URL to your bot")
else:
    print("\n[WARNING] Setup incomplete. Please fix the following:")
    
    if not all_configured:
        print("\n1. Configure environment variables in .env file")
        
    if not os.path.exists(creds_path):
        print(f"\n2. Download Google credentials and save as {creds_path}")
        
    if missing_packages:
        print(f"\n3. Install missing packages:")
        print(f"   pip install {' '.join(missing_packages)}")

print("\nSee setup_guide.md for detailed instructions")
print("=" * 60)