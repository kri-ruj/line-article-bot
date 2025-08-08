import requests
import json
import hmac
import hashlib
import base64
import os
from dotenv import load_dotenv

load_dotenv()

# Test webhook locally
url = "http://localhost:5005/callback"
channel_secret = os.getenv('LINE_CHANNEL_SECRET')

# Create test payload
payload = {
    "events": [{
        "type": "message",
        "replyToken": "test_reply_token_12345",
        "source": {
            "userId": "test_user_123",
            "type": "user"
        },
        "message": {
            "type": "text",
            "id": "test_message_id",
            "text": "/help"
        }
    }]
}

body = json.dumps(payload)

# Generate signature
hash = hmac.new(channel_secret.encode('utf-8'),
                body.encode('utf-8'), 
                hashlib.sha256).digest()
signature = base64.b64encode(hash).decode('utf-8')

# Send request
headers = {
    'Content-Type': 'application/json',
    'X-Line-Signature': signature
}

response = requests.post(url, headers=headers, data=body)
print(f"Status: {response.status_code}")
print(f"Response: {response.text}")
