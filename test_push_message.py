#!/usr/bin/env python3
"""Test sending a push message"""

import urllib.request
import json

LINE_CHANNEL_ACCESS_TOKEN = '9JTrTJ3+0lXerYu6HRjq4LNF+3UuDG5IwxfU0S8f5QYMJNai+WU3dgs2U5RfO74YDGGh5B1eAi4DoDxl0lq5CAA/kDkAwfaz2AL/qTEiO3Toiz1pS0nCtRNZKDoY0sI3JIWQucLySxrq7gEf7Rvx/QdB04t89/1O/w1cDnyilFU='
USER_ID = 'Udcd08cd8a445c68f462a739e8898abb9'  # Your LINE user ID

def send_push_message():
    """Send a test push message"""
    
    print("📨 Sending test push message...")
    
    try:
        url = 'https://api.line.me/v2/bot/message/push'
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {LINE_CHANNEL_ACCESS_TOKEN}'
        }
        
        message = {
            'to': USER_ID,
            'messages': [
                {
                    'type': 'text',
                    'text': '✅ Webhook is working!\n\nProduction URL:\nhttps://article-hub-959205905728.asia-northeast1.run.app\n\nTry sending me a URL to save it!',
                    'quickReply': {
                        'items': [
                            {
                                'type': 'action',
                                'action': {
                                    'type': 'message',
                                    'label': '📊 Stats',
                                    'text': '/stats'
                                }
                            },
                            {
                                'type': 'action',
                                'action': {
                                    'type': 'message',
                                    'label': '📚 List',
                                    'text': '/list'
                                }
                            },
                            {
                                'type': 'action',
                                'action': {
                                    'type': 'uri',
                                    'label': '🎯 Open App',
                                    'uri': 'https://article-hub-959205905728.asia-northeast1.run.app/kanban'
                                }
                            }
                        ]
                    }
                }
            ]
        }
        
        req = urllib.request.Request(
            url,
            data=json.dumps(message).encode('utf-8'),
            headers=headers,
            method='POST'
        )
        
        with urllib.request.urlopen(req) as response:
            print(f"✅ Message sent successfully!")
            print(f"   Status: {response.status}")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    send_push_message()
    print("\n✅ Check your LINE app for the message!")
    print("\nTry sending:")
    print("1. Any URL to save it")
    print("2. /help for help")
    print("3. /stats for statistics")
    print("4. /list for recent articles")