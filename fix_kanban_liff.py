#!/usr/bin/env python3
"""
Fix to update app_production_persistent.py with:
1. Complete Kanban HTML
2. Use LIFF URLs instead of direct URLs
"""

import re

# Read the complete Kanban HTML from app_production_complete.py
with open('app_production_complete.py', 'r') as f:
    complete_content = f.read()

# Extract the serve_kanban method
match = re.search(r'def serve_kanban\(self\):.*?(?=\n    def \w+|\nclass |\n# |\Z)', complete_content, re.DOTALL)
if match:
    kanban_method = match.group(0)
    print(f"Found serve_kanban method: {len(kanban_method)} chars")
else:
    print("Could not find serve_kanban method")
    exit(1)

# Read the persistent version
with open('app_production_persistent.py', 'r') as f:
    persistent_content = f.read()

# Replace the incomplete serve_kanban with the complete one
pattern = r'def serve_kanban\(self\):.*?(?=\n    def \w+|\nclass |\n# |\Z)'
updated_content = re.sub(pattern, kanban_method, persistent_content, flags=re.DOTALL)

# Now update all response URLs to use LIFF
LIFF_ID = '2007552096-GxP76rNd'
BASE_URL = 'https://article-hub-959205905728.asia-northeast1.run.app'
LIFF_URL = f'https://liff.line.me/{LIFF_ID}'

# Update flex message buttons to use LIFF
updated_content = re.sub(
    r"'label': '📊 View Dashboard',\s*'uri': f'\{BASE_URL\}/kanban'",
    f"'label': '📊 View Dashboard',\n                                'uri': 'https://liff.line.me/{LIFF_ID}'",
    updated_content
)

# Update quick reply Dashboard button to use LIFF
updated_content = re.sub(
    r"'label': '🎯 Dashboard',\s*'uri': f'\{BASE_URL\}/kanban'",
    f"'label': '🎯 Dashboard',\n                            'uri': 'https://liff.line.me/{LIFF_ID}'",
    updated_content
)

# Update help message to use LIFF
updated_content = re.sub(
    r"Access dashboard: \{BASE_URL\}/kanban",
    f"Access dashboard: https://liff.line.me/{LIFF_ID}",
    updated_content
)

# Update rich menu references
updated_content = re.sub(
    r"f\"\{PROD_URL\}/kanban\"",
    f"'https://liff.line.me/{LIFF_ID}'",
    updated_content
)

# Save the updated file
with open('app_production_fixed.py', 'w') as f:
    f.write(updated_content)

print("✅ Created app_production_fixed.py with:")
print("  - Complete Kanban HTML")
print("  - LIFF URLs for all dashboard links")
print(f"  - LIFF URL: https://liff.line.me/{LIFF_ID}")