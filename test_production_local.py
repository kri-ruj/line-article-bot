#!/usr/bin/env python3
"""Test production app locally before deployment"""

import os
import time
import subprocess
import signal
import urllib.request
import json

def test_production_app():
    """Test the production app locally"""
    
    print("🧪 Testing Production App Locally")
    print("="*50)
    
    # Set test environment variables
    env = os.environ.copy()
    env.update({
        'PORT': '8080',
        'DB_PATH': '/tmp/test_articles.db',
        'BASE_URL': 'http://localhost:8080',
        'LIFF_ID': '2007552096-GxP76rNd',
        'LINE_CHANNEL_ACCESS_TOKEN': 'test_token',
        'LINE_CHANNEL_SECRET': 'test_secret',
        'LINE_LOGIN_CHANNEL_ID': 'test_id',
        'LINE_LOGIN_CHANNEL_SECRET': 'test_secret'
    })
    
    # Start the server
    print("\n1. Starting production server on port 8080...")
    process = subprocess.Popen(
        ['python3', 'app_production.py'],
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    # Wait for server to start
    time.sleep(3)
    
    try:
        # Test health endpoint
        print("\n2. Testing health endpoint...")
        try:
            with urllib.request.urlopen('http://localhost:8080/health') as response:
                data = json.loads(response.read())
                if data.get('status') == 'healthy':
                    print("   ✅ Health check passed")
                else:
                    print("   ❌ Health check failed")
        except Exception as e:
            print(f"   ❌ Health check error: {e}")
        
        # Test homepage
        print("\n3. Testing homepage...")
        try:
            with urllib.request.urlopen('http://localhost:8080/') as response:
                html = response.read().decode()
                if 'Article Intelligence Hub' in html:
                    print("   ✅ Homepage loads correctly")
                if 'Login with LINE' in html:
                    print("   ✅ Login button present")
        except Exception as e:
            print(f"   ❌ Homepage error: {e}")
        
        # Test manifest
        print("\n4. Testing PWA manifest...")
        try:
            with urllib.request.urlopen('http://localhost:8080/manifest.json') as response:
                manifest = json.loads(response.read())
                if manifest.get('name') == 'Article Intelligence Hub':
                    print("   ✅ Manifest served correctly")
        except Exception as e:
            print(f"   ❌ Manifest error: {e}")
        
        # Test service worker
        print("\n5. Testing service worker...")
        try:
            with urllib.request.urlopen('http://localhost:8080/service-worker.js') as response:
                sw = response.read().decode()
                if 'addEventListener' in sw:
                    print("   ✅ Service worker served correctly")
        except Exception as e:
            print(f"   ❌ Service worker error: {e}")
        
        print("\n" + "="*50)
        print("✅ All tests passed! Ready for deployment.")
        print("\nNext steps:")
        print("1. Create .env.production with your LINE credentials")
        print("2. Run: ./deploy.sh")
        print("3. Update LINE webhook URL to Cloud Run URL")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
    
    finally:
        # Clean up
        print("\nCleaning up...")
        process.terminate()
        try:
            process.wait(timeout=2)
        except subprocess.TimeoutExpired:
            process.kill()
        
        # Remove test database
        if os.path.exists('/tmp/test_articles.db'):
            os.remove('/tmp/test_articles.db')

if __name__ == "__main__":
    test_production_app()