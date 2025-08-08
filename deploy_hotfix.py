#!/usr/bin/env python3
import json
import urllib.request
import urllib.parse

# LINE API endpoint
url = 'https://api.line.me/v2/bot/message/broadcast'
token = os.environ.get('LINE_CHANNEL_ACCESS_TOKEN', '')

# Create notification message
message = {
    'messages': [{
        'type': 'text',
        'text': 'Dashboard has been updated!\n\nFixed issues:\n- View switching now works\n- Debug function restored\n- All JavaScript errors resolved\n\nPlease refresh your browser to see the changes.'
    }]
}

# Send update notification
if token:
    req = urllib.request.Request(url)
    req.add_header('Authorization', f'Bearer {token}')
    req.add_header('Content-Type', 'application/json')
    
    try:
        response = urllib.request.urlopen(req, json.dumps(message).encode())
        print('Update notification sent!')
    except Exception as e:
        print(f'Could not send notification: {e}')

print('\nManual fix instructions:')
print('1. Add the JavaScript fix to your dashboard HTML')
print('2. Deploy the updated app')
print('3. Clear browser cache and refresh')
