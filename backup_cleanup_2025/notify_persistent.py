#!/usr/bin/env python3
"""Notify user about persistent storage"""

import urllib.request
import json

LINE_CHANNEL_ACCESS_TOKEN = '9JTrTJ3+0lXerYu6HRjq4LNF+3UuDG5IwxfU0S8f5QYMJNai+WU3dgs2U5RfO74YDGGh5B1eAi4DoDxl0lq5CAA/kDkAwfaz2AL/qTEiO3Toiz1pS0nCtRNZKDoY0sI3JIWQucLySxrq7gEf7Rvx/QdB04t89/1O/w1cDnyilFU='
USER_ID = 'Udcd08cd8a445c68f462a739e8898abb9'

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
            'text': '''✅ Persistent storage is now active!

💾 Your data is automatically backed up to Google Cloud Storage every 30 seconds.

🔄 Data persists across all updates and deployments!

Try /backup to see storage status.''',
            'quickReply': {
                'items': [
                    {
                        'type': 'action',
                        'action': {
                            'type': 'message',
                            'label': '💾 Backup Status',
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
                    },
                    {
                        'type': 'action',
                        'action': {
                            'type': 'uri',
                            'label': '📊 Kanban',
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
    print(f"✅ Message sent! Status: {response.status}")