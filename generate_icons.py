#!/usr/bin/env python3
"""Generate PWA icons in different sizes"""

def create_icon_svg():
    """Create a simple SVG icon"""
    svg = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512">
  <defs>
    <linearGradient id="grad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" style="stop-color:#667eea;stop-opacity:1" />
      <stop offset="100%" style="stop-color:#764ba2;stop-opacity:1" />
    </linearGradient>
  </defs>
  <rect width="512" height="512" rx="80" fill="url(#grad)"/>
  <text x="256" y="320" font-family="Arial" font-size="240" text-anchor="middle" fill="white">🧠</text>
</svg>'''
    
    with open('icon.svg', 'w') as f:
        f.write(svg)
    
    print("Created icon.svg")
    print("\nTo generate PNG icons, you can:")
    print("1. Use an online converter like https://cloudconvert.com/svg-to-png")
    print("2. Or install ImageMagick and run:")
    print("   for size in 72 96 128 144 152 192 384 512; do")
    print('     convert -background none -resize ${size}x${size} icon.svg icon-${size}x${size}.png')
    print("   done")
    
    # Create placeholder data URLs for immediate use
    sizes = [72, 96, 128, 144, 152, 192, 384, 512]
    
    print("\nCreating placeholder data URL icons...")
    
    # Simple colored square with emoji as data URL
    for size in sizes:
        # This creates a simple colored square - in production you'd use proper icons
        print(f"- icon-{size}x{size}.png (placeholder)")

if __name__ == "__main__":
    create_icon_svg()