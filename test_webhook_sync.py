#!/usr/bin/env python3
"""
Test webhook and data synchronization issues
"""

import os
import json
import hmac
import hashlib
import base64
import urllib.request
import urllib.error
from datetime import datetime

# Configuration
WEBHOOK_URL = "https://article-hub-959205905728.asia-northeast1.run.app/callback"
LINE_CHANNEL_SECRET = "85fa3bc67d3b99f12c1e92a32dd3ee17"
LINE_CHANNEL_ACCESS_TOKEN = "9JTrTJ3+0lXerYu6HRjq4LNF+3UuDG5IwxfU0S8f5QYMJNai+WU3dgs2U5RfO74YDGGh5B1eAi4DoDxl0lq5CAA/kDkAwfaz2AL/qTEiO3Toiz1pS0nCtRNZKDoY0sI3JIWQucLySxrq7gEf7Rvx/QdB04t89/1O/w1cDnyilFU="

def create_signature(body, channel_secret):
    """Create LINE webhook signature"""
    hash_obj = hmac.new(
        channel_secret.encode('utf-8'),
        body.encode('utf-8'),
        hashlib.sha256
    )
    return base64.b64encode(hash_obj.digest()).decode('utf-8')

def test_webhook():
    """Test webhook with proper signature"""
    print("Testing LINE Webhook Synchronization")
    print("=" * 50)
    
    # Create test event
    test_event = {
        "destination": "U1234567890abcdef1234567890abcdef",
        "events": [
            {
                "type": "message",
                "message": {
                    "type": "text",
                    "id": "test_message_id",
                    "text": "https://example.com/test-article"
                },
                "timestamp": int(datetime.now().timestamp() * 1000),
                "source": {
                    "type": "user",
                    "userId": "Utest_user_123456789"
                },
                "replyToken": "test_reply_token_123",
                "mode": "active"
            }
        ]
    }
    
    # Convert to JSON
    body = json.dumps(test_event)
    
    # Create signature
    signature = create_signature(body, LINE_CHANNEL_SECRET)
    
    print(f"Webhook URL: {WEBHOOK_URL}")
    print(f"Test User ID: Utest_user_123456789")
    print(f"Test Message: https://example.com/test-article")
    print(f"Signature: {signature[:20]}...")
    print()
    
    # Send request
    try:
        req = urllib.request.Request(WEBHOOK_URL)
        req.add_header('Content-Type', 'application/json')
        req.add_header('X-Line-Signature', signature)
        req.add_header('User-Agent', 'LineBotWebhook/2.0')
        
        response = urllib.request.urlopen(req, body.encode())
        result = response.read().decode()
        
        print("SUCCESS - Webhook Response:", response.code)
        print("Response Body:", result)
        
    except urllib.error.HTTPError as e:
        print("HTTP Error:", e.code)
        print("Error Body:", e.read().decode())
    except Exception as e:
        print("Error:", str(e))

def check_user_data():
    """Check if user data is properly stored"""
    print("\nChecking User Data Storage")
    print("=" * 50)
    
    # Test health endpoint
    try:
        health_url = "https://article-hub-959205905728.asia-northeast1.run.app/health"
        response = urllib.request.urlopen(health_url)
        data = json.loads(response.read().decode())
        
        print("System Status:")
        print(f"  - Status: {data.get('status', 'unknown')}")
        print(f"  - Database: {data.get('database', 'unknown')}")
        print(f"  - LINE Bot: {data.get('services', {}).get('line_bot', False)}")
        print(f"  - Firestore: {data.get('services', {}).get('firestore', False)}")
        
    except Exception as e:
        print(f"Could not check health: {e}")

def test_line_api():
    """Test LINE API connectivity"""
    print("\nTesting LINE API Connectivity")
    print("=" * 50)
    
    try:
        # Test getting webhook endpoint
        url = "https://api.line.me/v2/bot/channel/webhook/endpoint"
        req = urllib.request.Request(url)
        req.add_header('Authorization', f'Bearer {LINE_CHANNEL_ACCESS_TOKEN}')
        
        response = urllib.request.urlopen(req)
        data = json.loads(response.read().decode())
        
        print("LINE Webhook Configuration:")
        print(f"  - Endpoint: {data.get('endpoint', 'Not set')}")
        print(f"  - Active: {data.get('active', False)}")
        
    except urllib.error.HTTPError as e:
        if e.code == 401:
            print("Invalid LINE channel access token")
        else:
            print(f"LINE API Error: {e.code}")
    except Exception as e:
        print(f"Error: {e}")

def diagnose_issues():
    """Diagnose common issues"""
    print("\nDiagnosing Common Issues")
    print("=" * 50)
    
    issues = []
    
    # Check 1: Webhook URL mismatch
    print("1. Checking webhook configuration...")
    try:
        url = "https://api.line.me/v2/bot/channel/webhook/endpoint"
        req = urllib.request.Request(url)
        req.add_header('Authorization', f'Bearer {LINE_CHANNEL_ACCESS_TOKEN}')
        response = urllib.request.urlopen(req)
        data = json.loads(response.read().decode())
        
        configured_url = data.get('endpoint', '')
        if WEBHOOK_URL not in configured_url:
            issues.append(f"Webhook URL mismatch! LINE has: {configured_url}")
        else:
            print("   OK - Webhook URL matches")
    except:
        issues.append("Could not verify webhook URL")
    
    # Check 2: User ID format
    print("2. Checking user ID format...")
    print("   LINE User IDs should start with 'U' and be 33 characters")
    print("   Example: U1234567890abcdef1234567890abcdef")
    
    # Check 3: Database connectivity
    print("3. Checking database...")
    import sqlite3
    try:
        conn = sqlite3.connect('articles_kanban.db')
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM articles_kanban")
        count = cursor.fetchone()[0]
        print(f"   OK - Local database has {count} articles")
        
        # Check for user-specific data
        cursor.execute("SELECT DISTINCT user_id FROM articles_kanban WHERE user_id IS NOT NULL")
        users = cursor.fetchall()
        if users:
            print(f"   OK - Found {len(users)} unique users in database")
            for user in users[:3]:  # Show first 3
                print(f"     - {user[0][:10]}...")
        else:
            print("   ! No user IDs found in database")
            issues.append("No user-specific data in database")
        
        conn.close()
    except Exception as e:
        issues.append(f"Database error: {e}")
    
    # Summary
    print("\nIssues Found:")
    if issues:
        for issue in issues:
            print(f"  - {issue}")
    else:
        print("  - No major issues detected")
    
    print("\nRecommendations:")
    print("1. Verify webhook URL in LINE Developers Console")
    print("2. Check if user_id field is being saved with articles")
    print("3. Ensure LINE signature validation is working")
    print("4. Check if Firestore is properly configured for production")

if __name__ == "__main__":
    test_webhook()
    check_user_data()
    test_line_api()
    diagnose_issues()