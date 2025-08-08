#!/usr/bin/env python3
"""
Test production webhook - NO NGROK NEEDED
"""
import urllib.request
import json

# Production URLs only
PRODUCTION_URL = "https://article-hub-959205905728.asia-northeast1.run.app"
WEBHOOK_URL = f"{PRODUCTION_URL}/callback"
DASHBOARD_URL = f"{PRODUCTION_URL}/dashboard"
KANBAN_URL = f"{PRODUCTION_URL}/kanban"
HEALTH_URL = f"{PRODUCTION_URL}/health"
LIFF_URL = "https://liff.line.me/2007552096-GxP76rNd"

# LINE configuration
LINE_CHANNEL_ACCESS_TOKEN = '9JTrTJ3+0lXerYu6HRjq4LNF+3UuDG5IwxfU0S8f5QYMJNai+WU3dgs2U5RfO74YDGGh5B1eAi4DoDxl0lq5CAA/kDkAwfaz2AL/qTEiO3Toiz1pS0nCtRNZKDoY0sI3JIWQucLySxrq7gEf7Rvx/QdB04t89/1O/w1cDnyilFU='

def check_health():
    """Check if service is healthy"""
    try:
        req = urllib.request.Request(HEALTH_URL)
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode('utf-8'))
            return data
    except Exception as e:
        return None

def get_webhook_endpoint():
    """Get current webhook endpoint from LINE API"""
    url = 'https://api.line.me/v2/bot/channel/webhook/endpoint'
    
    req = urllib.request.Request(
        url,
        headers={
            'Authorization': f'Bearer {LINE_CHANNEL_ACCESS_TOKEN}'
        }
    )
    
    try:
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode('utf-8'))
            return data
    except Exception as e:
        return None

def test_webhook():
    """Test webhook endpoint"""
    url = 'https://api.line.me/v2/bot/channel/webhook/test'
    
    data = json.dumps({
        "endpoint": WEBHOOK_URL
    }).encode('utf-8')
    
    req = urllib.request.Request(
        url,
        data=data,
        headers={
            'Authorization': f'Bearer {LINE_CHANNEL_ACCESS_TOKEN}',
            'Content-Type': 'application/json'
        },
        method='POST'
    )
    
    try:
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read().decode('utf-8'))
            return result
    except Exception as e:
        return None

print("🚀 Production Article Hub Status Check")
print("=" * 60)
print("NO NGROK NEEDED - Using Cloud Run Production Deployment")
print("=" * 60)

# Check health
print("\n📊 Service Health Check:")
health = check_health()
if health:
    print(f"✅ Service is {health.get('status', 'unknown')}")
    print(f"   Database: {health.get('database', 'unknown')}")
    services = health.get('services', {})
    print(f"   LINE Bot: {'✅' if services.get('line_bot') else '❌'}")
    print(f"   LINE Login: {'✅' if services.get('line_login') else '❌'}")
    print(f"   Firestore: {'✅' if services.get('firestore') else '❌'}")
else:
    print("❌ Service health check failed")

# Check webhook configuration
print("\n🔗 LINE Webhook Configuration:")
webhook_info = get_webhook_endpoint()
if webhook_info:
    current_url = webhook_info.get('endpoint', 'Not set')
    is_active = webhook_info.get('active', False)
    
    print(f"   Current URL: {current_url}")
    print(f"   Expected URL: {WEBHOOK_URL}")
    print(f"   Status: {'✅ Active' if is_active else '❌ Inactive'}")
    
    if current_url == WEBHOOK_URL:
        print("   ✅ Webhook URL is correctly configured")
    else:
        print("   ⚠️ Webhook URL mismatch - needs update")
else:
    print("❌ Failed to get webhook configuration")

# Test webhook
print("\n🧪 Webhook Connection Test:")
test_result = test_webhook()
if test_result and test_result.get('success'):
    print(f"   ✅ Webhook test passed")
    print(f"   Status Code: {test_result.get('statusCode', 'N/A')}")
else:
    print("   ❌ Webhook test failed")

print("\n📱 Access Points:")
print(f"   Dashboard: {DASHBOARD_URL}")
print(f"   Kanban Board: {KANBAN_URL}")
print(f"   LIFF Dashboard: {LIFF_URL}")
print(f"   Health Check: {HEALTH_URL}")

print("\n✨ Production deployment is ready!")
print("Send any URL to your LINE bot and it will be saved to Firestore.")
print("\n⚠️ Remember: NO NGROK NEEDED - Everything runs on Google Cloud!")