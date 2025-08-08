#!/usr/bin/env python3
"""
Create a beautiful rich menu with text and icons
Using HTML/CSS to SVG to PNG approach
"""

import json
import os
import urllib.request
import urllib.error
import base64

LINE_CHANNEL_ACCESS_TOKEN = '9JTrTJ3+0lXerYu6HRjq4LNF+3UuDG5IwxfU0S8f5QYMJNai+WU3dgs2U5RfO74YDGGh5B1eAi4DoDxl0lq5CAA/kDkAwfaz2AL/qTEiO3Toiz1pS0nCtRNZKDoY0sI3JIWQucLySxrq7gEf7Rvx/QdB04t89/1O/w1cDnyilFU='

def create_svg_rich_menu():
    """Create an SVG image with text and icons"""
    
    svg_content = '''<?xml version="1.0" encoding="UTF-8"?>
<svg width="2500" height="1686" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <!-- Gradients for each section -->
    <linearGradient id="grad1" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" style="stop-color:#667eea;stop-opacity:1" />
      <stop offset="100%" style="stop-color:#8b7ee8;stop-opacity:1" />
    </linearGradient>
    <linearGradient id="grad2" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" style="stop-color:#764ba2;stop-opacity:1" />
      <stop offset="100%" style="stop-color:#965bc2;stop-opacity:1" />
    </linearGradient>
    <!-- Drop shadow filter -->
    <filter id="shadow" x="-50%" y="-50%" width="200%" height="200%">
      <feDropShadow dx="0" dy="4" stdDeviation="10" flood-opacity="0.2"/>
    </filter>
  </defs>
  
  <!-- Background -->
  <rect width="2500" height="1686" fill="#f0f0ff"/>
  
  <!-- Grid sections with gradients -->
  <!-- Top row -->
  <g id="section1">
    <rect x="10" y="10" width="813" height="823" rx="20" fill="url(#grad1)" filter="url(#shadow)"/>
    <text x="416" y="350" font-family="Arial, sans-serif" font-size="120" fill="white" text-anchor="middle">🌐</text>
    <text x="416" y="470" font-family="Arial, sans-serif" font-size="55" font-weight="bold" fill="white" text-anchor="middle">Open</text>
    <text x="416" y="540" font-family="Arial, sans-serif" font-size="55" font-weight="bold" fill="white" text-anchor="middle">Web App</text>
  </g>
  
  <g id="section2">
    <rect x="843" y="10" width="814" height="823" rx="20" fill="url(#grad2)" filter="url(#shadow)"/>
    <text x="1250" y="350" font-family="Arial, sans-serif" font-size="120" fill="white" text-anchor="middle">📋</text>
    <text x="1250" y="470" font-family="Arial, sans-serif" font-size="55" font-weight="bold" fill="white" text-anchor="middle">My</text>
    <text x="1250" y="540" font-family="Arial, sans-serif" font-size="55" font-weight="bold" fill="white" text-anchor="middle">Articles</text>
  </g>
  
  <g id="section3">
    <rect x="1677" y="10" width="813" height="823" rx="20" fill="url(#grad1)" filter="url(#shadow)"/>
    <text x="2083" y="350" font-family="Arial, sans-serif" font-size="120" fill="white" text-anchor="middle">📊</text>
    <text x="2083" y="470" font-family="Arial, sans-serif" font-size="55" font-weight="bold" fill="white" text-anchor="middle">View</text>
    <text x="2083" y="540" font-family="Arial, sans-serif" font-size="55" font-weight="bold" fill="white" text-anchor="middle">Stats</text>
  </g>
  
  <!-- Bottom row -->
  <g id="section4">
    <rect x="10" y="853" width="813" height="823" rx="20" fill="url(#grad2)" filter="url(#shadow)"/>
    <text x="416" y="1193" font-family="Arial, sans-serif" font-size="120" fill="white" text-anchor="middle">➕</text>
    <text x="416" y="1313" font-family="Arial, sans-serif" font-size="55" font-weight="bold" fill="white" text-anchor="middle">Add New</text>
    <text x="416" y="1383" font-family="Arial, sans-serif" font-size="55" font-weight="bold" fill="white" text-anchor="middle">Article</text>
  </g>
  
  <g id="section5">
    <rect x="843" y="853" width="814" height="823" rx="20" fill="url(#grad1)" filter="url(#shadow)"/>
    <text x="1250" y="1193" font-family="Arial, sans-serif" font-size="120" fill="white" text-anchor="middle">📱</text>
    <text x="1250" y="1313" font-family="Arial, sans-serif" font-size="55" font-weight="bold" fill="white" text-anchor="middle">Open</text>
    <text x="1250" y="1383" font-family="Arial, sans-serif" font-size="55" font-weight="bold" fill="white" text-anchor="middle">LIFF App</text>
  </g>
  
  <g id="section6">
    <rect x="1677" y="853" width="813" height="823" rx="20" fill="url(#grad2)" filter="url(#shadow)"/>
    <text x="2083" y="1193" font-family="Arial, sans-serif" font-size="120" fill="white" text-anchor="middle">❓</text>
    <text x="2083" y="1313" font-family="Arial, sans-serif" font-size="55" font-weight="bold" fill="white" text-anchor="middle">Get</text>
    <text x="2083" y="1383" font-family="Arial, sans-serif" font-size="55" font-weight="bold" fill="white" text-anchor="middle">Help</text>
  </g>
  
  <!-- Decorative elements -->
  <text x="1250" y="60" font-family="Arial, sans-serif" font-size="36" font-weight="bold" fill="#667eea" text-anchor="middle">📚 Article Intelligence Hub</text>
</svg>'''
    
    # Save SVG file
    with open('rich_menu_beautiful.svg', 'w') as f:
        f.write(svg_content)
    
    print("✅ Created beautiful SVG rich menu: rich_menu_beautiful.svg")
    
    # Convert to data URL for web preview
    svg_base64 = base64.b64encode(svg_content.encode()).decode()
    data_url = f"data:image/svg+xml;base64,{svg_base64}"
    
    # Create HTML preview
    html_preview = f'''<!DOCTYPE html>
<html>
<head>
    <title>Rich Menu Preview</title>
    <style>
        body {{
            margin: 0;
            padding: 20px;
            background: #f0f0f0;
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
        }}
        .preview {{
            max-width: 800px;
            background: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.1);
        }}
        img {{
            width: 100%;
            height: auto;
            border-radius: 8px;
        }}
        h2 {{
            color: #667eea;
            text-align: center;
        }}
        .info {{
            margin-top: 20px;
            padding: 15px;
            background: #f8f9fa;
            border-radius: 8px;
        }}
    </style>
</head>
<body>
    <div class="preview">
        <h2>📱 Rich Menu Preview</h2>
        <img src="{data_url}" alt="Rich Menu">
        <div class="info">
            <h3>Next Steps:</h3>
            <ol>
                <li>Convert this SVG to PNG (2500x1686 pixels)</li>
                <li>Use online converter: <a href="https://cloudconvert.com/svg-to-png">cloudconvert.com/svg-to-png</a></li>
                <li>Or use command: <code>convert rich_menu_beautiful.svg -resize 2500x1686 rich_menu_final.png</code></li>
                <li>Upload the PNG via LINE Developers Console</li>
            </ol>
        </div>
    </div>
</body>
</html>'''
    
    with open('rich_menu_preview.html', 'w') as f:
        f.write(html_preview)
    
    print("✅ Created preview: rich_menu_preview.html")
    
    return svg_content

def update_rich_menu_with_better_image():
    """Update the existing rich menu with a better image"""
    
    print("\n🎨 Updating Rich Menu with Beautiful Design")
    print("="*50)
    
    # Create the SVG
    svg_content = create_svg_rich_menu()
    
    # Get current rich menu ID
    try:
        url = 'https://api.line.me/v2/bot/user/all/richmenu'
        headers = {'Authorization': f'Bearer {LINE_CHANNEL_ACCESS_TOKEN}'}
        
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read())
            rich_menu_id = result.get('richMenuId')
            
            if rich_menu_id:
                print(f"\n✅ Current rich menu ID: {rich_menu_id}")
                print("\n📌 To update the image:")
                print("1. Open rich_menu_preview.html in your browser")
                print("2. Take a screenshot or convert SVG to PNG")
                print("3. Go to LINE Developers Console")
                print("4. Navigate to your channel → Messaging API → Rich Menu")
                print("5. Click on the rich menu to edit")
                print("6. Upload the new image")
                print("7. Save changes")
                
                print("\n🎨 Or use this command to convert (requires ImageMagick):")
                print("   convert rich_menu_beautiful.svg -resize 2500x1686 rich_menu_final.png")
                
            else:
                print("⚠️ No active rich menu found")
                
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    update_rich_menu_with_better_image()
    
    print("\n✨ Files created:")
    print("  • rich_menu_beautiful.svg - The SVG design")
    print("  • rich_menu_preview.html - Preview in browser")
    
    # Try to open preview in browser
    try:
        import webbrowser
        webbrowser.open('rich_menu_preview.html')
        print("\n🌐 Opening preview in browser...")
    except:
        print("\n👉 Open rich_menu_preview.html in your browser to see the design")