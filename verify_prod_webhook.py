#!/usr/bin/env python3
"""Verify production webhook configuration"""

import urllib.request
import json

LINE_CHANNEL_ACCESS_TOKEN = '9JTrTJ3+0lXerYu6HRjq4LNF+3UuDG5IwxfU0S8f5QYMJNai+WU3dgs2U5RfO74YDGGh5B1eAi4DoDxl0lq5CAA/kDkAwfaz2AL/qTEiO3Toiz1pS0nCtRNZKDoY0sI3JIWQucLySxrq7gEf7Rvx/QdB04t89/1O/w1cDnyilFU='

def check_webhook():
    """Check webhook configuration"""
    
    print("🔍 Checking LINE Webhook Configuration")
    print("="*50)
    
    # 1. Get current webhook endpoint
    print("\n1. Getting webhook endpoint info...")
    try:
        url = 'https://api.line.me/v2/bot/channel/webhook/endpoint'
        headers = {
            'Authorization': f'Bearer {LINE_CHANNEL_ACCESS_TOKEN}'
        }
        
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read())
            print(f"✅ Current webhook URL: {data.get('endpoint', 'Not set')}")
            print(f"   Active: {data.get('active', False)}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # 2. Set webhook endpoint
    print("\n2. Setting webhook endpoint...")
    try:
        url = 'https://api.line.me/v2/bot/channel/webhook/endpoint'
        headers = {
            'Authorization': f'Bearer {LINE_CHANNEL_ACCESS_TOKEN}',
            'Content-Type': 'application/json'
        }
        
        data = {
            'endpoint': 'https://article-hub-959205905728.asia-northeast1.run.app/webhook'
        }
        
        req = urllib.request.Request(
            url,
            data=json.dumps(data).encode('utf-8'),
            headers=headers,
            method='PUT'
        )
        
        with urllib.request.urlopen(req) as response:
            print(f"✅ Webhook URL updated successfully")
    except Exception as e:
        print(f"❌ Error setting webhook: {e}")
    
    # 3. Test webhook
    print("\n3. Testing webhook verification...")
    try:
        test_url = 'https://api.line.me/v2/bot/channel/webhook/test'
        headers = {
            'Authorization': f'Bearer {LINE_CHANNEL_ACCESS_TOKEN}',
            'Content-Type': 'application/json'
        }
        
        test_data = {
            'endpoint': 'https://article-hub-959205905728.asia-northeast1.run.app/webhook'
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
    print("\n✅ Production webhook URL:")
    print("   https://article-hub-959205905728.asia-northeast1.run.app/webhook")
    print("\n📝 Make sure in LINE Developers Console:")
    print("1. Webhook URL is set correctly")
    print("2. 'Use webhook' is ON")
    print("3. 'Auto-reply messages' is OFF")
    print("4. 'Greeting messages' is OFF")

if __name__ == "__main__":
    check_webhook()