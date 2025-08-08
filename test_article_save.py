#!/usr/bin/env python3
"""
Test article saving through webhook
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
YOUR_USER_ID = 'U4e61eb9b003d63f8dc30bb98ae91b859'

def create_signature(body: str, channel_secret: str) -> str:
    """Create LINE webhook signature"""
    hash = hmac.new(
        channel_secret.encode('utf-8'),
        body.encode('utf-8'),
        hashlib.sha256
    ).digest()
    return base64.b64encode(hash).decode('utf-8')

def test_save_article(url: str, message: str = None):
    """Test saving an article through webhook"""
    timestamp = str(int(time.time() * 1000))
    
    # Use provided message or just the URL
    text = message if message else url
    
    event_data = {
        "destination": "Ub00111122223333444455556666777",
        "events": [
            {
                "type": "message",
                "message": {
                    "type": "text",
                    "id": f"test_{timestamp}",
                    "text": text
                },
                "timestamp": int(time.time() * 1000),
                "source": {
                    "type": "user",
                    "userId": YOUR_USER_ID
                },
                "replyToken": f"test_token_{timestamp}",
                "mode": "active"
            }
        ]
    }
    
    body = json.dumps(event_data)
    signature = create_signature(body, CHANNEL_SECRET)
    
    req = urllib.request.Request(
        WEBHOOK_URL,
        data=body.encode('utf-8'),
        headers={
            'Content-Type': 'application/json',
            'X-Line-Signature': signature
        },
        method='POST'
    )
    
    print(f"📤 Sending: {text}")
    
    try:
        with urllib.request.urlopen(req) as response:
            result = response.read().decode('utf-8')
            print(f"✅ Article saved successfully!")
            return True
    except urllib.error.HTTPError as e:
        error_body = e.read().decode('utf-8')
        print(f"❌ Failed: {e.code} - {error_body}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

print("🧪 Testing Article Saving to Firestore")
print("=" * 50)

# Test 1: Single URL
print("\n📝 Test 1: Single URL")
print("-" * 30)
test_save_article("https://www.example.com/firestore-test-article")

# Test 2: Text with URL
print("\n📝 Test 2: Text containing URL")
print("-" * 30)
test_save_article("", "Check out this article: https://medium.com/test-article-123 it's really interesting!")

# Test 3: Multiple URLs
print("\n📝 Test 3: Multiple URLs in one message")
print("-" * 30)
test_save_article("", "Here are some articles:\nhttps://dev.to/article1\nhttps://github.com/repo\nhttps://stackoverflow.com/question")

print("\n" + "=" * 50)
print("✅ Testing complete!")
print("\n📊 Check your saved articles:")
print("1. Firestore Console: https://console.firebase.google.com/project/secondbrain-app-20250612/firestore/data/~2Farticles")
print("2. Dashboard: https://article-hub-959205905728.asia-northeast1.run.app/dashboard")
print("3. Kanban Board: https://article-hub-959205905728.asia-northeast1.run.app/kanban")
print("\n💡 You can now send URLs to your LINE bot and they will be permanently saved in Firestore!")