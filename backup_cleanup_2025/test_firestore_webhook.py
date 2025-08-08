#!/usr/bin/env python3
"""
Test Firestore webhook with proper signature
"""
import json
import hashlib
import hmac
import base64
import urllib.request
import urllib.error
import time

# LINE configuration
CHANNEL_SECRET = '327390179d950161aa5f8014bd395ad8'
WEBHOOK_URL = 'https://article-hub-959205905728.asia-northeast1.run.app/callback'

def create_signature(body: str, channel_secret: str) -> str:
    """Create LINE webhook signature"""
    hash = hmac.new(
        channel_secret.encode('utf-8'),
        body.encode('utf-8'),
        hashlib.sha256
    ).digest()
    return base64.b64encode(hash).decode('utf-8')

def test_webhook():
    """Test webhook with article URL"""
    # Create test event
    timestamp = str(int(time.time() * 1000))
    event_data = {
        "destination": "test",
        "events": [
            {
                "type": "message",
                "message": {
                    "type": "text",
                    "id": f"test_{timestamp}",
                    "text": "https://www.example.com/test-article-firestore"
                },
                "timestamp": int(time.time() * 1000),
                "source": {
                    "type": "user",
                    "userId": "U4e61eb9b003d63f8dc30bb98ae91b859"
                },
                "replyToken": f"test_token_{timestamp}",
                "mode": "active"
            }
        ]
    }
    
    # Convert to JSON
    body = json.dumps(event_data)
    
    # Create signature
    signature = create_signature(body, CHANNEL_SECRET)
    
    # Send request
    req = urllib.request.Request(
        WEBHOOK_URL,
        data=body.encode('utf-8'),
        headers={
            'Content-Type': 'application/json',
            'X-Line-Signature': signature
        },
        method='POST'
    )
    
    print(f"🔍 Testing webhook at: {WEBHOOK_URL}")
    print(f"📝 Signature: {signature}")
    print(f"📦 Body: {json.dumps(event_data, indent=2)}")
    
    try:
        with urllib.request.urlopen(req) as response:
            result = response.read().decode('utf-8')
            print(f"✅ Webhook responded successfully: {response.code}")
            print(f"📄 Response: {result}")
            return True
    except urllib.error.HTTPError as e:
        error_body = e.read().decode('utf-8')
        print(f"❌ Webhook failed: {e.code}")
        print(f"📄 Error: {error_body}")
        return False
    except Exception as e:
        print(f"❌ Request failed: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Testing Firestore webhook...")
    print("-" * 50)
    test_webhook()
    print("-" * 50)
    print("\n💡 Check the Firestore console to see if the article was saved:")
    print("https://console.firebase.google.com/project/secondbrain-app-20250612/firestore/data/~2Farticles")