#!/usr/bin/env python3
"""
Update LIFF configuration to use the new service URL
"""

# The LIFF Endpoint URL needs to be updated in the LINE Developer Console
# Current: https://article-hub-959205905728.asia-northeast1.run.app
# New: https://article-hub-fixed-959205905728.asia-northeast1.run.app

print("""
IMPORTANT: LIFF Endpoint URL Configuration
==========================================

The LIFF endpoint URL needs to be updated in the LINE Developer Console.

1. Go to: https://developers.line.biz/console/
2. Select your channel: "Article Intelligence Hub - Prod"
3. Go to LIFF tab
4. Find LIFF app ID: 2007870100-ao8GpgRQ
5. Click on the LIFF app to edit
6. Update the Endpoint URL from:
   OLD: https://article-hub-959205905728.asia-northeast1.run.app
   NEW: https://article-hub-fixed-959205905728.asia-northeast1.run.app

7. Save the changes

This will ensure that:
- LIFF login redirects to the correct service
- The dashboard loads properly after login
- Data from Firestore is displayed correctly

Alternative Quick Test:
=======================
While the LIFF URL is being updated, you can test the app directly:

1. Test mode (with sample data):
   https://article-hub-fixed-959205905728.asia-northeast1.run.app/dashboard?test=true
   
2. Check debug info:
   https://article-hub-fixed-959205905728.asia-northeast1.run.app/debug

3. After updating LIFF endpoint URL:
   https://liff.line.me/2007870100-ao8GpgRQ
   (This will redirect to the new service)
""")