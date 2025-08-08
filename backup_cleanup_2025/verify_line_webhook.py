#!/usr/bin/env python3
"""
Verify LINE webhook configuration
"""
import urllib.request
import json

CHANNEL_ACCESS_TOKEN = '9JTrTJ3+0lXerYu6HRjq4LNF+3UuDG5IwxfU0S8f5QYMJNai+WU3dgs2U5RfO74YDGGh5B1eAi4DoDxl0lq5CAA/kDkAwfaz2AL/qTEiO3Toiz1pS0nCtRNZKDoY0sI3JIWQucLySxrq7gEf7Rvx/QdB04t89/1O/w1cDnyilFU='

def get_webhook_endpoint():
    """Get current webhook endpoint from LINE API"""
    url = 'https://api.line.me/v2/bot/channel/webhook/endpoint'
    
    req = urllib.request.Request(
        url,
        headers={
            'Authorization': f'Bearer {CHANNEL_ACCESS_TOKEN}'
        }
    )
    
    try:
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode('utf-8'))
            return data
    except Exception as e:
        print(f"Error: {e}")
        return None

def test_webhook():
    """Test webhook endpoint"""
    url = 'https://api.line.me/v2/bot/channel/webhook/test'
    
    data = json.dumps({
        "endpoint": "https://article-hub-959205905728.asia-northeast1.run.app/callback"
    }).encode('utf-8')
    
    req = urllib.request.Request(
        url,
        data=data,
        headers={
            'Authorization': f'Bearer {CHANNEL_ACCESS_TOKEN}',
            'Content-Type': 'application/json'
        },
        method='POST'
    )
    
    try:
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read().decode('utf-8'))
            return result
    except Exception as e:
        print(f"Error: {e}")
        return None

print("🔍 Checking LINE webhook configuration...")
print("-" * 50)

# Get current webhook
endpoint_info = get_webhook_endpoint()
if endpoint_info:
    print(f"✅ Current webhook endpoint:")
    print(f"   URL: {endpoint_info.get('endpoint', 'Not set')}")
    print(f"   Active: {endpoint_info.get('active', False)}")
else:
    print("❌ Failed to get webhook endpoint")

print("\n📝 Expected webhook URL:")
print("   https://article-hub-959205905728.asia-northeast1.run.app/callback")

# Test webhook
print("\n🧪 Testing webhook connection...")
test_result = test_webhook()
if test_result:
    print(f"✅ Webhook test result:")
    print(f"   Success: {test_result.get('success', False)}")
    print(f"   Timestamp: {test_result.get('timestamp', 'N/A')}")
    print(f"   Status Code: {test_result.get('statusCode', 'N/A')}")
    if test_result.get('detail'):
        print(f"   Detail: {test_result.get('detail')}")
else:
    print("❌ Webhook test failed")

print("\n💡 To update webhook URL in LINE Developers Console:")
print("1. Go to https://developers.line.biz/console/")
print("2. Select your channel")
print("3. Go to Messaging API tab")
print("4. Set Webhook URL to: https://article-hub-959205905728.asia-northeast1.run.app/callback")
print("5. Enable 'Use webhook'")
print("6. Click 'Verify' to test")