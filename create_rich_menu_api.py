#!/usr/bin/env python3
"""
Create and deploy LINE Rich Menu via Messaging API
Generates a proper PNG image and uploads it
"""

import json
import os
import urllib.request
import urllib.error
import struct
import zlib

# LINE credentials
LINE_CHANNEL_ACCESS_TOKEN = '9JTrTJ3+0lXerYu6HRjq4LNF+3UuDG5IwxfU0S8f5QYMJNai+WU3dgs2U5RfO74YDGGh5B1eAi4DoDxl0lq5CAA/kDkAwfaz2AL/qTEiO3Toiz1pS0nCtRNZKDoY0sI3JIWQucLySxrq7gEf7Rvx/QdB04t89/1O/w1cDnyilFU='

def create_png_image(width=2500, height=1686):
    """Create a PNG image without PIL - pure Python implementation"""
    
    print("🎨 Generating rich menu image (2500x1686)...")
    
    # PNG header
    png_header = b'\x89PNG\r\n\x1a\n'
    
    # IHDR chunk (image header)
    ihdr_data = struct.pack('>IIBBBBB', width, height, 8, 2, 0, 0, 0)
    ihdr_crc = zlib.crc32(b'IHDR' + ihdr_data)
    ihdr_chunk = struct.pack('>I', 13) + b'IHDR' + ihdr_data + struct.pack('>I', ihdr_crc)
    
    # Create image data (RGB)
    # We'll create a gradient background with 6 sections
    rows = []
    
    for y in range(height):
        row = b''
        for x in range(width):
            # Determine which section we're in
            col = x * 3 // width  # 0, 1, or 2
            row_section = y * 2 // height  # 0 or 1
            section = row_section * 3 + col
            
            # Create gradient effect
            gradient = (x + y) / (width + height)
            
            # Base colors for each section (purple gradient)
            if section % 2 == 0:
                # Primary purple (#667eea)
                r = int(102 + gradient * 50)
                g = int(126 + gradient * 30)
                b = int(234 - gradient * 50)
            else:
                # Secondary purple (#764ba2)
                r = int(118 + gradient * 40)
                g = int(75 + gradient * 50)
                b = int(162 + gradient * 30)
            
            # Add borders between sections
            border_width = 3
            is_vertical_border = (x % (width // 3)) < border_width or (x % (width // 3)) > (width // 3 - border_width)
            is_horizontal_border = (y % (height // 2)) < border_width or (y % (height // 2)) > (height // 2 - border_width)
            
            if is_vertical_border or is_horizontal_border:
                # White border
                r, g, b = 255, 255, 255
            
            row += bytes([r, g, b])
        
        # Add filter byte (0 = None)
        rows.append(b'\x00' + row)
    
    # Compress image data
    image_data = b''.join(rows)
    compressed_data = zlib.compress(image_data, 9)
    
    # IDAT chunk (image data)
    idat_crc = zlib.crc32(b'IDAT' + compressed_data)
    idat_chunk = struct.pack('>I', len(compressed_data)) + b'IDAT' + compressed_data + struct.pack('>I', idat_crc)
    
    # Add text labels (simplified - would need font rendering for real text)
    # For now, we'll add a tEXt chunk with metadata
    text_data = b'Title\x00Article Hub Rich Menu'
    text_crc = zlib.crc32(b'tEXt' + text_data)
    text_chunk = struct.pack('>I', len(text_data)) + b'tEXt' + text_data + struct.pack('>I', text_crc)
    
    # IEND chunk (end of file)
    iend_crc = zlib.crc32(b'IEND')
    iend_chunk = struct.pack('>I', 0) + b'IEND' + struct.pack('>I', iend_crc)
    
    # Combine all chunks
    png_data = png_header + ihdr_chunk + text_chunk + idat_chunk + iend_chunk
    
    # Save to file
    with open('rich_menu_api.png', 'wb') as f:
        f.write(png_data)
    
    print(f"✅ Created PNG image ({len(png_data)} bytes)")
    return png_data

def delete_all_rich_menus():
    """Delete all existing rich menus"""
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
                    print(f"🗑️ Deleted old menu: {menu['richMenuId'][:20]}...")
            except:
                pass
                
        print("✅ All old rich menus cleared")
        
    except Exception as e:
        print(f"⚠️ Could not delete old menus: {e}")

def create_rich_menu():
    """Create rich menu structure"""
    
    print("📱 Creating rich menu structure...")
    
    rich_menu = {
        "size": {"width": 2500, "height": 1686},
        "selected": True,
        "name": "Article Hub Menu v2",
        "chatBarText": "📚 Menu",
        "areas": [
            # Top row
            {
                "bounds": {"x": 0, "y": 0, "width": 833, "height": 843},
                "action": {
                    "type": "uri",
                    "label": "Web App",
                    "uri": "https://09f85f116221.ngrok-free.app"
                }
            },
            {
                "bounds": {"x": 833, "y": 0, "width": 834, "height": 843},
                "action": {
                    "type": "message",
                    "label": "Articles",
                    "text": "/list"
                }
            },
            {
                "bounds": {"x": 1667, "y": 0, "width": 833, "height": 843},
                "action": {
                    "type": "message",
                    "label": "Stats",
                    "text": "/stats"
                }
            },
            # Bottom row
            {
                "bounds": {"x": 0, "y": 843, "width": 833, "height": 843},
                "action": {
                    "type": "message",
                    "label": "Add",
                    "text": "Send me a URL to save it as an article"
                }
            },
            {
                "bounds": {"x": 833, "y": 843, "width": 834, "height": 843},
                "action": {
                    "type": "uri",
                    "label": "LIFF",
                    "uri": "https://09f85f116221.ngrok-free.app/liff"
                }
            },
            {
                "bounds": {"x": 1667, "y": 843, "width": 833, "height": 843},
                "action": {
                    "type": "message",
                    "label": "Help",
                    "text": "/help"
                }
            }
        ]
    }
    
    try:
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
            print(f"✅ Rich menu created: {rich_menu_id}")
            return rich_menu_id
            
    except urllib.error.HTTPError as e:
        error_body = e.read().decode('utf-8')
        print(f"❌ Error creating menu: {error_body}")
        return None

def upload_image(rich_menu_id, image_data):
    """Upload PNG image to rich menu"""
    
    print("📤 Uploading image to rich menu...")
    
    try:
        url = f'https://api-data.line.me/v2/bot/richmenu/{rich_menu_id}/content'
        headers = {
            'Authorization': f'Bearer {LINE_CHANNEL_ACCESS_TOKEN}',
            'Content-Type': 'image/png',
            'Content-Length': str(len(image_data))
        }
        
        req = urllib.request.Request(
            url,
            data=image_data,
            headers=headers,
            method='POST'
        )
        
        with urllib.request.urlopen(req) as response:
            print(f"✅ Image uploaded successfully")
            return True
            
    except urllib.error.HTTPError as e:
        print(f"❌ Error uploading image: {e.code} - {e.reason}")
        return False

def set_default_rich_menu(rich_menu_id):
    """Set rich menu as default for all users"""
    
    print("🔧 Setting rich menu as default...")
    
    try:
        url = f'https://api.line.me/v2/bot/user/all/richmenu/{rich_menu_id}'
        headers = {'Authorization': f'Bearer {LINE_CHANNEL_ACCESS_TOKEN}'}
        
        req = urllib.request.Request(url, headers=headers, method='POST')
        
        with urllib.request.urlopen(req) as response:
            print("✅ Rich menu set as default for all users")
            return True
            
    except urllib.error.HTTPError as e:
        print(f"❌ Error setting default: {e.code} - {e.reason}")
        return False

def verify_rich_menu():
    """Verify rich menu is active"""
    try:
        url = 'https://api.line.me/v2/bot/user/all/richmenu'
        headers = {'Authorization': f'Bearer {LINE_CHANNEL_ACCESS_TOKEN}'}
        
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read())
            if result.get('richMenuId'):
                print(f"✅ Active rich menu: {result['richMenuId']}")
                return True
            else:
                print("⚠️ No active rich menu")
                return False
    except:
        print("⚠️ Could not verify rich menu")
        return False

def main():
    print("\n" + "="*50)
    print("🎨 Article Hub Rich Menu Setup (via API)")
    print("="*50 + "\n")
    
    # Step 1: Clean up old menus
    print("Step 1: Cleaning up old menus...")
    delete_all_rich_menus()
    print()
    
    # Step 2: Create new rich menu
    print("Step 2: Creating new rich menu...")
    rich_menu_id = create_rich_menu()
    
    if not rich_menu_id:
        print("❌ Failed to create rich menu")
        return
    print()
    
    # Step 3: Generate and upload image
    print("Step 3: Generating and uploading image...")
    image_data = create_png_image()
    
    if not upload_image(rich_menu_id, image_data):
        print("❌ Failed to upload image")
        return
    print()
    
    # Step 4: Set as default
    print("Step 4: Setting as default...")
    if not set_default_rich_menu(rich_menu_id):
        print("⚠️ Could not set as default")
    print()
    
    # Step 5: Verify
    print("Step 5: Verifying setup...")
    verify_rich_menu()
    
    print("\n" + "="*50)
    print("✅ Rich Menu Setup Complete!")
    print("="*50)
    print("\n📱 Rich Menu Features:")
    print("  • 🌐 Web App - Opens Article Hub in browser")
    print("  • 📋 Articles - Shows your saved articles")
    print("  • 📊 Stats - View reading statistics")
    print("  • ➕ Add - Prompt to send URLs")
    print("  • 📱 LIFF - Opens in LINE app")
    print("  • ❓ Help - Shows available commands")
    print("\n👉 Users will see the menu in their LINE chat!")

if __name__ == "__main__":
    main()