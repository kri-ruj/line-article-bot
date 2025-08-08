#!/usr/bin/env python3
"""Update rich menu with production URLs"""

import json
import urllib.request
import struct
import zlib

LINE_CHANNEL_ACCESS_TOKEN = '9JTrTJ3+0lXerYu6HRjq4LNF+3UuDG5IwxfU0S8f5QYMJNai+WU3dgs2U5RfO74YDGGh5B1eAi4DoDxl0lq5CAA/kDkAwfaz2AL/qTEiO3Toiz1pS0nCtRNZKDoY0sI3JIWQucLySxrq7gEf7Rvx/QdB04t89/1O/w1cDnyilFU='
LIFF_ID = '2007552096-GxP76rNd'
PROD_URL = 'https://article-hub-959205905728.asia-northeast1.run.app'

def update_rich_menu():
    """Update rich menu with production URLs"""
    
    # First, delete all existing rich menus
    print("🗑️ Deleting old rich menus...")
    try:
        url = 'https://api.line.me/v2/bot/richmenu/list'
        headers = {'Authorization': f'Bearer {LINE_CHANNEL_ACCESS_TOKEN}'}
        
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read())
            
        for menu in data.get('richmenus', []):
            delete_url = f'https://api.line.me/v2/bot/richmenu/{menu["richMenuId"]}'
            delete_req = urllib.request.Request(delete_url, headers=headers, method='DELETE')
            try:
                with urllib.request.urlopen(delete_req):
                    print(f"  Deleted menu: {menu['richMenuId'][:20]}...")
            except:
                pass
    except:
        pass
    
    print("✅ Old menus cleared\n")
    
    # Create new rich menu with production URLs
    print("📱 Creating new rich menu...")
    rich_menu = {
        "size": {"width": 2500, "height": 1686},
        "selected": True,
        "name": "Article Hub Production Menu",
        "chatBarText": "📚 Menu",
        "areas": [
            # Top row
            {
                "bounds": {"x": 0, "y": 0, "width": 833, "height": 843},
                "action": {
                    "type": "uri",
                    "label": "📊 Kanban",
                    "uri": f"https://liff.line.me/{LIFF_ID}"
                }
            },
            {
                "bounds": {"x": 833, "y": 0, "width": 834, "height": 843},
                "action": {
                    "type": "message",
                    "label": "📚 Articles",
                    "text": "/list"
                }
            },
            {
                "bounds": {"x": 1667, "y": 0, "width": 833, "height": 843},
                "action": {
                    "type": "message",
                    "label": "📈 Stats",
                    "text": "/stats"
                }
            },
            # Bottom row
            {
                "bounds": {"x": 0, "y": 843, "width": 833, "height": 843},
                "action": {
                    "type": "message",
                    "label": "➕ Add",
                    "text": "Send me a URL to save it!"
                }
            },
            {
                "bounds": {"x": 833, "y": 843, "width": 834, "height": 843},
                "action": {
                    "type": "uri",
                    "label": "🚀 LIFF App",
                    "uri": f"https://liff.line.me/{LIFF_ID}"
                }
            },
            {
                "bounds": {"x": 1667, "y": 843, "width": 833, "height": 843},
                "action": {
                    "type": "message",
                    "label": "❓ Help",
                    "text": "/help"
                }
            }
        ]
    }
    
    try:
        # Create rich menu
        url = 'https://api.line.me/v2/bot/richmenu'
        headers = {
            'Authorization': f'Bearer {LINE_CHANNEL_ACCESS_TOKEN}',
            'Content-Type': 'application/json'
        }
        
        req = urllib.request.Request(
            url,
            data=json.dumps(rich_menu).encode('utf-8'),
            headers=headers,
            method='POST'
        )
        
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read())
            rich_menu_id = result['richMenuId']
            print(f"✅ Created menu: {rich_menu_id}")
            
            # Create and upload image
            print("🎨 Creating menu image...")
            width, height = 2500, 1686
            png_header = b'\x89PNG\r\n\x1a\n'
            
            # IHDR chunk
            ihdr_data = struct.pack('>IIBBBBB', width, height, 8, 2, 0, 0, 0)
            ihdr_crc = zlib.crc32(b'IHDR' + ihdr_data)
            ihdr_chunk = struct.pack('>I', 13) + b'IHDR' + ihdr_data + struct.pack('>I', ihdr_crc)
            
            # Create image with gradient and labels
            rows = []
            for y in range(height):
                row = b''
                for x in range(width):
                    col = x * 3 // width
                    row_section = y * 2 // height
                    
                    # Base colors
                    if row_section == 0:  # Top row
                        if col == 0:  # Kanban
                            r, g, b = 102, 126, 234
                        elif col == 1:  # Articles
                            r, g, b = 118, 75, 162
                        else:  # Stats
                            r, g, b = 236, 72, 153
                    else:  # Bottom row
                        if col == 0:  # Add
                            r, g, b = 34, 197, 94
                        elif col == 1:  # LIFF
                            r, g, b = 59, 130, 246
                        else:  # Help
                            r, g, b = 251, 146, 60
                    
                    # Add borders
                    if (x % (width // 3)) < 3 or (y % (height // 2)) < 3:
                        r, g, b = 255, 255, 255
                    
                    # Add center text area (lighter)
                    center_x = (col * 2 + 1) * width // 6
                    center_y = (row_section * 2 + 1) * height // 4
                    if abs(x - center_x) < 100 and abs(y - center_y) < 50:
                        r = min(255, r + 50)
                        g = min(255, g + 50)
                        b = min(255, b + 50)
                    
                    row += bytes([r, g, b])
                rows.append(b'\x00' + row)
            
            image_data = b''.join(rows)
            compressed_data = zlib.compress(image_data, 9)
            
            # IDAT chunk
            idat_crc = zlib.crc32(b'IDAT' + compressed_data)
            idat_chunk = struct.pack('>I', len(compressed_data)) + b'IDAT' + compressed_data + struct.pack('>I', idat_crc)
            
            # IEND chunk
            iend_crc = zlib.crc32(b'IEND')
            iend_chunk = struct.pack('>I', 0) + b'IEND' + struct.pack('>I', iend_crc)
            
            png_data = png_header + ihdr_chunk + idat_chunk + iend_chunk
            
            # Upload image
            print("📤 Uploading image...")
            upload_url = f'https://api-data.line.me/v2/bot/richmenu/{rich_menu_id}/content'
            upload_headers = {
                'Authorization': f'Bearer {LINE_CHANNEL_ACCESS_TOKEN}',
                'Content-Type': 'image/png',
                'Content-Length': str(len(png_data))
            }
            
            upload_req = urllib.request.Request(
                upload_url,
                data=png_data,
                headers=upload_headers,
                method='POST'
            )
            
            with urllib.request.urlopen(upload_req):
                print("✅ Image uploaded")
            
            # Set as default
            print("🎯 Setting as default menu...")
            default_url = f'https://api.line.me/v2/bot/user/all/richmenu/{rich_menu_id}'
            default_req = urllib.request.Request(
                default_url,
                headers={'Authorization': f'Bearer {LINE_CHANNEL_ACCESS_TOKEN}'},
                method='POST'
            )
            
            with urllib.request.urlopen(default_req):
                print("✅ Set as default")
                
            print(f"\n✨ Rich menu updated with production URLs!")
            print(f"\n📱 Menu Actions:")
            print(f"  Top Row:")
            print(f"    📊 Kanban → https://liff.line.me/{LIFF_ID}")
            print(f"    📚 Articles → /list command")
            print(f"    📈 Stats → /stats command")
            print(f"  Bottom Row:")
            print(f"    ➕ Add → Instructions message")
            print(f"    🚀 LIFF → https://liff.line.me/{LIFF_ID}")
            print(f"    ❓ Help → /help command")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    update_rich_menu()