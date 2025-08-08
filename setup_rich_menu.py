#!/usr/bin/env python3
"""
Setup LINE Rich Menu for Article Intelligence Hub
This will create a custom rich menu with 6 actions
"""

import json
import os
import urllib.request
import urllib.error
import io
import base64

# Get LINE credentials from environment
LINE_CHANNEL_ACCESS_TOKEN = os.getenv('LINE_CHANNEL_ACCESS_TOKEN', '9JTrTJ3+0lXerYu6HRjq4LNF+3UuDG5IwxfU0S8f5QYMJNai+WU3dgs2U5RfO74YDGGh5B1eAi4DoDxl0lq5CAA/kDkAwfaz2AL/qTEiO3Toiz1pS0nCtRNZKDoY0sI3JIWQucLySxrq7gEf7Rvx/QdB04t89/1O/w1cDnyilFU=')

def delete_all_rich_menus():
    """Delete all existing rich menus"""
    try:
        # Get list of rich menus
        url = 'https://api.line.me/v2/bot/richmenu/list'
        headers = {
            'Authorization': f'Bearer {LINE_CHANNEL_ACCESS_TOKEN}'
        }
        
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read())
            
        # Delete each rich menu
        for menu in data.get('richmenus', []):
            delete_url = f'https://api.line.me/v2/bot/richmenu/{menu["richMenuId"]}'
            delete_req = urllib.request.Request(delete_url, headers=headers, method='DELETE')
            try:
                with urllib.request.urlopen(delete_req) as response:
                    print(f"Deleted rich menu: {menu['richMenuId']}")
            except:
                pass
                
        print("✅ All old rich menus deleted")
        
    except Exception as e:
        print(f"Error deleting rich menus: {e}")

def create_rich_menu():
    """Create a new rich menu with 6 actions"""
    
    rich_menu_object = {
        "size": {
            "width": 2500,
            "height": 1686
        },
        "selected": True,
        "name": "Article Hub Menu",
        "chatBarText": "📚 Article Hub",
        "areas": [
            # Top row - 3 items
            {
                "bounds": {
                    "x": 0,
                    "y": 0,
                    "width": 833,
                    "height": 843
                },
                "action": {
                    "type": "uri",
                    "label": "Open Web App",
                    "uri": "https://09f85f116221.ngrok-free.app"
                }
            },
            {
                "bounds": {
                    "x": 833,
                    "y": 0,
                    "width": 834,
                    "height": 843
                },
                "action": {
                    "type": "message",
                    "label": "My Articles",
                    "text": "/list"
                }
            },
            {
                "bounds": {
                    "x": 1667,
                    "y": 0,
                    "width": 833,
                    "height": 843
                },
                "action": {
                    "type": "message",
                    "label": "Statistics",
                    "text": "/stats"
                }
            },
            # Bottom row - 3 items
            {
                "bounds": {
                    "x": 0,
                    "y": 843,
                    "width": 833,
                    "height": 843
                },
                "action": {
                    "type": "uri",
                    "label": "Add Article",
                    "uri": "https://line.me/R/oaMessage/U0f05288a76acf046a7f1d0af383c59b3/?Send%20me%20a%20URL%20to%20save"
                }
            },
            {
                "bounds": {
                    "x": 833,
                    "y": 843,
                    "width": 834,
                    "height": 843
                },
                "action": {
                    "type": "uri",
                    "label": "Open LIFF",
                    "uri": "https://liff.line.me/YOUR_LIFF_ID"
                }
            },
            {
                "bounds": {
                    "x": 1667,
                    "y": 843,
                    "width": 833,
                    "height": 843
                },
                "action": {
                    "type": "message",
                    "label": "Help",
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
        
        data = json.dumps(rich_menu_object).encode('utf-8')
        req = urllib.request.Request(url, data=data, headers=headers, method='POST')
        
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read())
            rich_menu_id = result['richMenuId']
            print(f"✅ Rich menu created: {rich_menu_id}")
            return rich_menu_id
            
    except urllib.error.HTTPError as e:
        error_body = e.read().decode('utf-8')
        print(f"❌ Error creating rich menu: {e.code} - {error_body}")
        return None
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def create_rich_menu_image():
    """Create a rich menu image with icons and text"""
    try:
        from PIL import Image, ImageDraw, ImageFont
        
        # Create image
        width, height = 2500, 1686
        img = Image.new('RGB', (width, height), color='white')
        draw = ImageDraw.Draw(img)
        
        # Define colors
        primary_color = (102, 126, 234)  # #667eea
        secondary_color = (118, 75, 162)  # #764ba2
        text_color = (255, 255, 255)
        border_color = (230, 230, 230)
        
        # Try to use a nice font, fallback to default
        try:
            font_large = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 60)
            font_small = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 40)
            font_emoji = ImageFont.truetype("/System/Library/Fonts/Apple Color Emoji.ttc", 80)
        except:
            font_large = ImageFont.load_default()
            font_small = ImageFont.load_default()
            font_emoji = ImageFont.load_default()
        
        # Menu items configuration
        items = [
            # Top row
            {"emoji": "🌐", "text": "Open\nWeb App", "bg": primary_color},
            {"emoji": "📋", "text": "My\nArticles", "bg": secondary_color},
            {"emoji": "📊", "text": "View\nStats", "bg": primary_color},
            # Bottom row
            {"emoji": "➕", "text": "Add\nArticle", "bg": secondary_color},
            {"emoji": "📱", "text": "Open\nLIFF", "bg": primary_color},
            {"emoji": "❓", "text": "Get\nHelp", "bg": secondary_color}
        ]
        
        # Draw grid
        cell_width = width // 3
        cell_height = height // 2
        
        for i, item in enumerate(items):
            # Calculate position
            row = i // 3
            col = i % 3
            x = col * cell_width
            y = row * cell_height
            
            # Draw background
            draw.rectangle([x, y, x + cell_width, y + cell_height], fill=item["bg"])
            
            # Draw border
            draw.rectangle([x, y, x + cell_width, y + cell_height], outline=border_color, width=2)
            
            # Draw emoji (centered)
            emoji_bbox = draw.textbbox((0, 0), item["emoji"], font=font_emoji)
            emoji_width = emoji_bbox[2] - emoji_bbox[0]
            emoji_height = emoji_bbox[3] - emoji_bbox[1]
            emoji_x = x + (cell_width - emoji_width) // 2
            emoji_y = y + (cell_height - emoji_height) // 2 - 40
            draw.text((emoji_x, emoji_y), item["emoji"], fill=text_color, font=font_emoji)
            
            # Draw text (centered below emoji)
            lines = item["text"].split('\n')
            text_y = emoji_y + emoji_height + 20
            for line in lines:
                text_bbox = draw.textbbox((0, 0), line, font=font_small)
                text_width = text_bbox[2] - text_bbox[0]
                text_x = x + (cell_width - text_width) // 2
                draw.text((text_x, text_y), line, fill=text_color, font=font_small)
                text_y += 50
        
        # Add gradient overlay at top
        for i in range(100):
            alpha = int(255 * (1 - i / 100))
            overlay_color = (*primary_color, alpha)
            draw.rectangle([0, i, width, i+1], fill=overlay_color)
        
        # Save image
        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format='PNG')
        img_byte_arr.seek(0)
        
        # Also save to file for preview
        img.save('rich_menu_image.png')
        print("✅ Rich menu image created: rich_menu_image.png")
        
        return img_byte_arr.getvalue()
        
    except ImportError:
        print("❌ PIL/Pillow not installed. Creating simple image...")
        # Create a simple colored rectangle as fallback
        return create_simple_image()

def create_simple_image():
    """Create a simple rich menu image without PIL"""
    # This creates a simple SVG and converts to PNG-like data
    # In production, you'd use a proper image
    svg = '''<?xml version="1.0" encoding="UTF-8"?>
<svg width="2500" height="1686" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <linearGradient id="grad1" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" style="stop-color:#667eea;stop-opacity:1" />
      <stop offset="100%" style="stop-color:#764ba2;stop-opacity:1" />
    </linearGradient>
  </defs>
  
  <!-- Background -->
  <rect width="2500" height="1686" fill="url(#grad1)"/>
  
  <!-- Grid lines -->
  <line x1="833" y1="0" x2="833" y2="1686" stroke="white" stroke-width="2"/>
  <line x1="1667" y1="0" x2="1667" y2="1686" stroke="white" stroke-width="2"/>
  <line x1="0" y1="843" x2="2500" y2="843" stroke="white" stroke-width="2"/>
  
  <!-- Text labels -->
  <text x="416" y="400" font-family="Arial" font-size="80" fill="white" text-anchor="middle">🌐</text>
  <text x="416" y="500" font-family="Arial" font-size="40" fill="white" text-anchor="middle">Web App</text>
  
  <text x="1250" y="400" font-family="Arial" font-size="80" fill="white" text-anchor="middle">📋</text>
  <text x="1250" y="500" font-family="Arial" font-size="40" fill="white" text-anchor="middle">Articles</text>
  
  <text x="2083" y="400" font-family="Arial" font-size="80" fill="white" text-anchor="middle">📊</text>
  <text x="2083" y="500" font-family="Arial" font-size="40" fill="white" text-anchor="middle">Stats</text>
  
  <text x="416" y="1243" font-family="Arial" font-size="80" fill="white" text-anchor="middle">➕</text>
  <text x="416" y="1343" font-family="Arial" font-size="40" fill="white" text-anchor="middle">Add</text>
  
  <text x="1250" y="1243" font-family="Arial" font-size="80" fill="white" text-anchor="middle">📱</text>
  <text x="1250" y="1343" font-family="Arial" font-size="40" fill="white" text-anchor="middle">LIFF</text>
  
  <text x="2083" y="1243" font-family="Arial" font-size="80" fill="white" text-anchor="middle">❓</text>
  <text x="2083" y="1343" font-family="Arial" font-size="40" fill="white" text-anchor="middle">Help</text>
</svg>'''
    
    # In a real scenario, you'd convert SVG to PNG
    # For now, return a placeholder
    print("✅ Simple rich menu image template created")
    return svg.encode('utf-8')

def upload_rich_menu_image(rich_menu_id, image_data):
    """Upload image to rich menu"""
    try:
        url = f'https://api-data.line.me/v2/bot/richmenu/{rich_menu_id}/content'
        headers = {
            'Authorization': f'Bearer {LINE_CHANNEL_ACCESS_TOKEN}',
            'Content-Type': 'image/png'
        }
        
        req = urllib.request.Request(url, data=image_data, headers=headers, method='POST')
        
        with urllib.request.urlopen(req) as response:
            print(f"✅ Image uploaded to rich menu")
            return True
            
    except Exception as e:
        print(f"❌ Error uploading image: {e}")
        return False

def set_default_rich_menu(rich_menu_id):
    """Set the rich menu as default for all users"""
    try:
        url = f'https://api.line.me/v2/bot/user/all/richmenu/{rich_menu_id}'
        headers = {
            'Authorization': f'Bearer {LINE_CHANNEL_ACCESS_TOKEN}'
        }
        
        req = urllib.request.Request(url, headers=headers, method='POST')
        
        with urllib.request.urlopen(req) as response:
            print(f"✅ Rich menu set as default for all users")
            return True
            
    except Exception as e:
        print(f"❌ Error setting default rich menu: {e}")
        return False

def remove_rich_menu():
    """Remove rich menu from all users"""
    try:
        url = 'https://api.line.me/v2/bot/user/all/richmenu'
        headers = {
            'Authorization': f'Bearer {LINE_CHANNEL_ACCESS_TOKEN}'
        }
        
        req = urllib.request.Request(url, headers=headers, method='DELETE')
        
        with urllib.request.urlopen(req) as response:
            print("✅ Rich menu removed from all users")
            return True
            
    except Exception as e:
        print(f"❌ Error removing rich menu: {e}")
        return False

def main():
    print("\n🎨 Article Hub Rich Menu Setup")
    print("=" * 40)
    
    while True:
        print("\nChoose an option:")
        print("1. Create new rich menu with custom design")
        print("2. Remove all rich menus")
        print("3. Exit")
        
        choice = input("\nEnter choice (1-3): ").strip()
        
        if choice == '1':
            print("\n📱 Creating custom rich menu...")
            
            # Delete old menus first
            delete_all_rich_menus()
            
            # Create new menu
            rich_menu_id = create_rich_menu()
            
            if rich_menu_id:
                # Create and upload image
                print("🎨 Creating rich menu image...")
                image_data = create_rich_menu_image()
                
                if image_data:
                    print("📤 Uploading image...")
                    if upload_rich_menu_image(rich_menu_id, image_data):
                        print("🔧 Setting as default...")
                        set_default_rich_menu(rich_menu_id)
                        print("\n✅ Rich menu setup complete!")
                        print(f"Rich Menu ID: {rich_menu_id}")
                        print("\n📱 Users will see the new menu in their LINE chat")
                        
        elif choice == '2':
            print("\n🗑️ Removing rich menu...")
            remove_rich_menu()
            delete_all_rich_menus()
            print("✅ All rich menus removed")
            
        elif choice == '3':
            print("\n👋 Goodbye!")
            break
        else:
            print("❌ Invalid choice")

if __name__ == "__main__":
    main()