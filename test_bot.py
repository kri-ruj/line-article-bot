#!/usr/bin/env python3
"""Test the bot locally"""

import requests
import json
import time

# Test saving an article
def test_save_article():
    print("Testing article save...")
    
    webhook_data = {
        "events": [{
            "type": "message",
            "replyToken": "test-token-" + str(int(time.time())),
            "source": {"userId": "test-user"},
            "message": {
                "type": "text",
                "text": "https://www.bbc.com/news/technology"
            }
        }]
    }
    
    response = requests.post(
        "http://localhost:5001/callback",
        json=webhook_data
    )
    
    print(f"Response: {response.status_code}")
    print(f"Content: {response.text}")
    
    # Check database
    stats = requests.get("http://localhost:5001/stats").json()
    print(f"Total articles: {stats.get('total_articles', 0)}")
    
    # Check logs
    logs = requests.get("http://localhost:5001/logs").json()
    if logs:
        print(f"Recent log: {logs[0]}")

# Test commands
def test_commands():
    commands = ["/help", "/list", "/stats", "/summary"]
    
    for cmd in commands:
        print(f"\nTesting command: {cmd}")
        webhook_data = {
            "events": [{
                "type": "message",
                "replyToken": f"test-token-{cmd}-{int(time.time())}",
                "source": {"userId": "test-user"},
                "message": {"type": "text", "text": cmd}
            }]
        }
        
        response = requests.post(
            "http://localhost:5001/callback",
            json=webhook_data
        )
        print(f"  Response: {response.status_code}")

if __name__ == "__main__":
    print("="*50)
    print("TESTING ARTICLE BOT")
    print("="*50)
    
    # Test article saving
    test_save_article()
    
    # Wait a bit
    time.sleep(2)
    
    # Test commands
    test_commands()
    
    print("\n" + "="*50)
    print("TESTS COMPLETE")
    print("Check dashboard at: http://localhost:5001/")
    print("="*50)