#!/usr/bin/env python3
"""
Update LINE webhook URL to correct endpoint
"""
import urllib.request
import json

CHANNEL_ACCESS_TOKEN = '9JTrTJ3+0lXerYu6HRjq4LNF+3UuDG5IwxfU0S8f5QYMJNai+WU3dgs2U5RfO74YDGGh5B1eAi4DoDxl0lq5CAA/kDkAwfaz2AL/qTEiO3Toiz1pS0nCtRNZKDoY0sI3JIWQucLySxrq7gEf7Rvx/QdB04t89/1O/w1cDnyilFU='

def set_webhook_url(webhook_url):
    """Set webhook URL via LINE API"""
    url = 'https://api.line.me/v2/bot/channel/webhook/endpoint'
    
    data = json.dumps({
        "endpoint": webhook_url
    }).encode('utf-8')
    
    req = urllib.request.Request(
        url,
        data=data,
        headers={
            'Authorization': f'Bearer {CHANNEL_ACCESS_TOKEN}',
            'Content-Type': 'application/json'
        },
        method='PUT'
    )
    
    try:
        with urllib.request.urlopen(req) as response:
            print(f"✅ Webhook URL updated successfully!")
            return True
    except urllib.error.HTTPError as e:
        error_body = e.read().decode('utf-8')
        print(f"❌ Failed to update webhook: {e.code}")
        print(f"   Error: {error_body}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

print("🔄 Updating LINE webhook URL...")
print("-" * 50)

new_webhook_url = "https://article-hub-959205905728.asia-northeast1.run.app/callback"
print(f"📝 Setting webhook URL to: {new_webhook_url}")

if set_webhook_url(new_webhook_url):
    print("\n✅ Webhook URL has been updated!")
    print("📱 Now you can send URLs to your LINE bot and they will be saved to Firestore")
    print("\n🧪 To test:")
    print("1. Send any URL to your LINE bot")
    print("2. Check Firestore console: https://console.firebase.google.com/project/secondbrain-app-20250612/firestore")
else:
    print("\n❌ Failed to update webhook URL")
    print("Please update manually in LINE Developers Console")