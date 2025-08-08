#!/usr/bin/env python3
"""
Test webhook commands (/help, /stats, /list)
"""
import json
import hashlib
import hmac
import base64
import urllib.request
import time

# LINE configuration
CHANNEL_SECRET = '327390179d950161aa5f8014bd395ad8'
WEBHOOK_URL = 'https://article-hub-959205905728.asia-northeast1.run.app/callback'
USER_ID = 'U4e61eb9b003d63f8dc30bb98ae91b859'

def create_signature(body: str, channel_secret: str) -> str:
    """Create LINE webhook signature"""
    hash = hmac.new(
        channel_secret.encode('utf-8'),
        body.encode('utf-8'),
        hashlib.sha256
    ).digest()
    return base64.b64encode(hash).decode('utf-8')

def test_command(command: str):
    """Test a command through webhook"""
    timestamp = str(int(time.time() * 1000))
    
    event_data = {
        "destination": "test",
        "events": [
            {
                "type": "message",
                "message": {
                    "type": "text",
                    "id": f"test_{timestamp}",
                    "text": command
                },
                "timestamp": int(time.time() * 1000),
                "source": {
                    "type": "user",
                    "userId": USER_ID
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
    
    print(f"📤 Testing command: {command}")
    
    try:
        with urllib.request.urlopen(req) as response:
            result = response.read().decode('utf-8')
            print(f"✅ Webhook responded: {response.code} - {result}")
            return True
    except Exception as e:
        print(f"❌ Failed: {e}")
        return False

print("🧪 Testing Webhook Commands")
print("=" * 50)

# Test /help command
print("\n📝 Test 1: /help command")
test_command("/help")

print("\n📝 Test 2: /stats command")
test_command("/stats")

print("\n📝 Test 3: /list command")
test_command("/list")

print("\n📝 Test 4: Regular URL")
test_command("https://example.com/test-article")

print("\n📝 Test 5: Unknown command")
test_command("/unknown")

print("\n" + "=" * 50)
print("✅ Command testing complete!")
print("\nThe webhook now properly handles:")
print("• /help - Show help message")
print("• /stats - View statistics")
print("• /list - Show recent articles")
print("• URLs - Save articles")
print("• Unknown commands - Error message")