#!/usr/bin/env python3
"""Verify LINE webhook configuration"""

import urllib.request
import json

LINE_CHANNEL_ACCESS_TOKEN = '9JTrTJ3+0lXerYu6HRjq4LNF+3UuDG5IwxfU0S8f5QYMJNai+WU3dgs2U5RfO74YDGGh5B1eAi4DoDxl0lq5CAA/kDkAwfaz2AL/qTEiO3Toiz1pS0nCtRNZKDoY0sI3JIWQucLySxrq7gEf7Rvx/QdB04t89/1O/w1cDnyilFU='

def test_webhook():
    """Test if webhook is working"""
    
    print("🔍 Testing LINE Webhook Configuration")
    print("="*50)
    
    # Test production endpoint
    print("\n1. Testing production endpoint...")
    try:
        test_url = "https://article-hub-959205905728.asia-northeast1.run.app/callback"
        test_data = {
            "events": [{
                "type": "message",
                "message": {"type": "text", "text": "test"},
                "replyToken": "test",
                "source": {"userId": "test"}
            }]
        }
        
        req = urllib.request.Request(
            test_url,
            data=json.dumps(test_data).encode('utf-8'),
            headers={'Content-Type': 'application/json'},
            method='POST'
        )
        
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read())
            if result.get('success'):
                print("✅ Webhook endpoint is working")
            else:
                print("⚠️ Webhook returned error")
    except Exception as e:
        print(f"❌ Webhook test failed: {e}")
    
    # Get webhook endpoint info
    print("\n2. Getting LINE webhook info...")
    try:
        url = 'https://api.line.me/v2/bot/channel/webhook/endpoint'
        headers = {
            'Authorization': f'Bearer {LINE_CHANNEL_ACCESS_TOKEN}'
        }
        
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read())
            print(f"✅ Webhook URL: {data.get('endpoint', 'Not set')}")
            print(f"   Active: {data.get('active', False)}")
    except Exception as e:
        print(f"⚠️ Could not get webhook info: {e}")
    
    # Test webhook
    print("\n3. Testing webhook verification...")
    try:
        test_url = 'https://api.line.me/v2/bot/channel/webhook/test'
        headers = {
            'Authorization': f'Bearer {LINE_CHANNEL_ACCESS_TOKEN}',
            'Content-Type': 'application/json'
        }
        
        test_data = {
            "endpoint": "https://09f85f116221.ngrok-free.app/callback"
        }
        
        req = urllib.request.Request(
            test_url,
            data=json.dumps(test_data).encode('utf-8'),
            headers=headers,
            method='POST'
        )
        
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read())
            if result.get('success'):
                print("✅ Webhook verification successful")
                print(f"   Status: {result.get('statusCode', 'Unknown')}")
                print(f"   Timestamp: {result.get('timestamp', 'Unknown')}")
            else:
                print(f"⚠️ Webhook verification failed: {result}")
    except Exception as e:
        print(f"❌ Webhook test failed: {e}")
    
    print("\n" + "="*50)
    print("\n📝 To fix webhook issues:")
    print("1. Go to LINE Developers Console")
    print("2. Select your channel → Messaging API")
    print("3. Set Webhook URL to:")
    print("   https://09f85f116221.ngrok-free.app/callback")
    print("4. Enable 'Use webhook'")
    print("5. Disable 'Auto-reply messages'")
    print("6. Click 'Verify' button")
    
    print("\n✅ Current webhook URL:")
    print("   https://09f85f116221.ngrok-free.app/callback")

if __name__ == "__main__":
    test_webhook()