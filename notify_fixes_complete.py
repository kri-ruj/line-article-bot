#!/usr/bin/env python3
"""Notify user about completed fixes"""

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
            'text': '''✅ All issues fixed!

1️⃣ Kanban board now shows properly after login
2️⃣ All links now use LIFF URLs
3️⃣ Persistent storage is active
4️⃣ Data syncs every 30 seconds

📱 Access your dashboard through LIFF:
https://liff.line.me/2007552096-GxP76rNd

💾 Your data is safe and persists across all updates!''',
            'quickReply': {
                'items': [
                    {
                        'type': 'action',
                        'action': {
                            'type': 'uri',
                            'label': '📊 Open LIFF App',
                            'uri': f'https://liff.line.me/{LIFF_ID}'
                        }
                    },
                    {
                        'type': 'action',
                        'action': {
                            'type': 'message',
                            'label': '💾 Backup',
                            'text': '/backup'
                        }
                    },
                    {
                        'type': 'action',
                        'action': {
                            'type': 'message',
                            'label': '📊 Stats',
                            'text': '/stats'
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