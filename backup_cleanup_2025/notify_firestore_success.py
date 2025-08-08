#!/usr/bin/env python3
"""
Notify success of Firestore migration
"""
import urllib.request
import json
import os

# LINE configuration
CHANNEL_ACCESS_TOKEN = '9JTrTJ3+0lXerYu6HRjq4LNF+3UuDG5IwxfU0S8f5QYMJNai+WU3dgs2U5RfO74YDGGh5B1eAi4DoDxl0lq5CAA/kDkAwfaz2AL/qTEiO3Toiz1pS0nCtRNZKDoY0sI3JIWQucLySxrq7gEf7Rvx/QdB04t89/1O/w1cDnyilFU='
USER_ID = 'U4e61eb9b003d63f8dc30bb98ae91b859'

def send_push_message(user_id: str, messages: list):
    """Send push message via LINE API"""
    url = 'https://api.line.me/v2/bot/message/push'
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {CHANNEL_ACCESS_TOKEN}'
    }
    
    data = {
        'to': user_id,
        'messages': messages
    }
    
    req = urllib.request.Request(
        url,
        data=json.dumps(data).encode('utf-8'),
        headers=headers,
        method='POST'
    )
    
    try:
        with urllib.request.urlopen(req) as response:
            print(f"✅ Message sent successfully: {response.read().decode()}")
            return True
    except Exception as e:
        print(f"❌ Failed to send message: {e}")
        return False

# Create success message
messages = [
    {
        "type": "text",
        "text": "🎉 Great news! Your Article Hub has been successfully migrated to Firestore!\n\n✅ Benefits:\n• Permanent data storage\n• No more data loss on redeploy\n• Automatic backups\n• Scalable NoSQL database\n\n🔥 Powered by Google Firestore\n\n📊 Access your dashboard:\nhttps://liff.line.me/2007552096-GxP76rNd\n\nYour articles are now safe and persistent! 🚀"
    },
    {
        "type": "flex",
        "altText": "Migration Complete",
        "contents": {
            "type": "bubble",
            "header": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {
                        "type": "text",
                        "text": "🔥 Firestore Migration Complete",
                        "weight": "bold",
                        "size": "lg",
                        "color": "#1DB446"
                    }
                ]
            },
            "body": {
                "type": "box",
                "layout": "vertical",
                "spacing": "md",
                "contents": [
                    {
                        "type": "text",
                        "text": "Your data is now permanently stored",
                        "weight": "bold",
                        "size": "md",
                        "wrap": True
                    },
                    {
                        "type": "separator",
                        "margin": "md"
                    },
                    {
                        "type": "box",
                        "layout": "vertical",
                        "spacing": "sm",
                        "contents": [
                            {
                                "type": "box",
                                "layout": "horizontal",
                                "contents": [
                                    {
                                        "type": "text",
                                        "text": "✅",
                                        "flex": 0
                                    },
                                    {
                                        "type": "text",
                                        "text": "No more data loss",
                                        "margin": "sm"
                                    }
                                ]
                            },
                            {
                                "type": "box",
                                "layout": "horizontal",
                                "contents": [
                                    {
                                        "type": "text",
                                        "text": "✅",
                                        "flex": 0
                                    },
                                    {
                                        "type": "text",
                                        "text": "Real-time sync",
                                        "margin": "sm"
                                    }
                                ]
                            },
                            {
                                "type": "box",
                                "layout": "horizontal",
                                "contents": [
                                    {
                                        "type": "text",
                                        "text": "✅",
                                        "flex": 0
                                    },
                                    {
                                        "type": "text",
                                        "text": "Automatic backups",
                                        "margin": "sm"
                                    }
                                ]
                            },
                            {
                                "type": "box",
                                "layout": "horizontal",
                                "contents": [
                                    {
                                        "type": "text",
                                        "text": "✅",
                                        "flex": 0
                                    },
                                    {
                                        "type": "text",
                                        "text": "99.99% availability",
                                        "margin": "sm"
                                    }
                                ]
                            }
                        ]
                    }
                ]
            },
            "footer": {
                "type": "box",
                "layout": "vertical",
                "spacing": "sm",
                "contents": [
                    {
                        "type": "button",
                        "action": {
                            "type": "uri",
                            "label": "📊 Open Dashboard",
                            "uri": "https://liff.line.me/2007552096-GxP76rNd"
                        },
                        "style": "primary",
                        "height": "sm"
                    },
                    {
                        "type": "button",
                        "action": {
                            "type": "uri",
                            "label": "🔥 View in Firestore Console",
                            "uri": "https://console.firebase.google.com/project/secondbrain-app-20250612/firestore"
                        },
                        "style": "link",
                        "height": "sm"
                    }
                ]
            }
        }
    }
]

# Send notification
print("📤 Sending Firestore migration success notification...")
send_push_message(USER_ID, messages)