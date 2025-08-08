#!/usr/bin/env python3
"""Notify user about URL extraction feature"""

import urllib.request
import json

LINE_CHANNEL_ACCESS_TOKEN = '9JTrTJ3+0lXerYu6HRjq4LNF+3UuDG5IwxfU0S8f5QYMJNai+WU3dgs2U5RfO74YDGGh5B1eAi4DoDxl0lq5CAA/kDkAwfaz2AL/qTEiO3Toiz1pS0nCtRNZKDoY0sI3JIWQucLySxrq7gEf7Rvx/QdB04t89/1O/w1cDnyilFU='
USER_ID = 'Udcd08cd8a445c68f462a739e8898abb9'
LIFF_ID = '2007552096-GxP76rNd'

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
            'text': '''🎉 NEW FEATURE: Smart URL Extraction!

Now you can send messages with URLs anywhere in the text and I'll find them all!

Examples:
• "Check out github.com/facebook/react and npmjs.com/package/express"
• "Great articles: www.medium.com/article1 and bit.ly/xyz123"
• "I found these: https://dev.to/tutorial and youtube.com/watch?v=abc"

Try it now! Send me any text with URLs mixed in! 🚀''',
            'quickReply': {
                'items': [
                    {
                        'type': 'action',
                        'action': {
                            'type': 'message',
                            'label': '🧪 Test Example',
                            'text': 'Check these articles: medium.com/@user/post1 and github.com/awesome/project also www.dev.to/tutorial'
                        }
                    },
                    {
                        'type': 'action',
                        'action': {
                            'type': 'uri',
                            'label': '📊 Open LIFF',
                            'uri': f'https://liff.line.me/{LIFF_ID}'
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
    print(f"✅ Notification sent! Status: {response.status}")
    print("\nFeatures added:")
    print("  ✅ Extracts multiple URLs from any text")
    print("  ✅ Handles URLs with or without http://")
    print("  ✅ Supports short URLs (bit.ly, t.co, etc.)")
    print("  ✅ Saves all URLs as separate articles")
    print("  ✅ Shows summary when multiple URLs are saved")