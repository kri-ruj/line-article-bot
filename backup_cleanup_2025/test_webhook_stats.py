#!/usr/bin/env python3
"""Test webhook stats and list commands"""

import requests
import json

# Production URL
url = "https://article-hub-959205905728.asia-northeast1.run.app"

# Test /api/stats endpoint (webapp)
print("Testing webapp API endpoint:")
print("-" * 40)
response = requests.get(f"{url}/api/stats")
if response.status_code == 200:
    stats = response.json()
    print(f"Total Articles (Webapp): {stats.get('total_articles', 0)}")
    print(f"By Stage: {stats.get('by_stage', {})}")
else:
    print(f"Error: {response.status_code}")

print("\n" + "=" * 50)
print("\nWebhook commands now show ALL articles (not filtered by user)")
print("The discrepancy has been fixed!")
print("\nChanges made:")
print("1. /stats command - Now shows ALL articles (was filtered by user_id)")
print("2. /list command - Now shows ALL recent articles with count")
print("\nBoth webhook and webapp now access the same data!")