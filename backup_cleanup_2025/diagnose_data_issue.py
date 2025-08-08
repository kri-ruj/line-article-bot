#!/usr/bin/env python3
"""
Diagnose why data isn't showing in the Kanban board
"""

print("""
DIAGNOSTIC CHECKLIST
====================

1. Check your User ID:
   - Click "Debug" link on the dashboard
   - Note your User ID shown in the popup
   
2. Known users with data in Firestore:
   - U4e61eb9b003d63f8dc30bb98ae91b859 (has articles)
   - U2de324e2a7198cf6ef152ab22afc80ea (26 articles)  
   - Udcd08cd8a445c68f462a739e8898abb9 (has articles)
   - test123 (test user)

3. If your User ID doesn't match any above:
   - Your LINE account has no saved articles yet
   - You need to save articles via LINE bot first
   - OR we can migrate data from another user

4. Quick test with existing data:
   https://article-hub-959205905728.asia-northeast1.run.app/dashboard?test=true
   
   This will use test user ID: U2de324e2a7198cf6ef152ab22afc80ea
   which has 26 articles in the database.

5. To save a test article via LINE bot:
   - Open LINE app
   - Send any URL to the bot
   - The article will appear in Inbox

6. Check browser console for errors:
   - Press F12 to open Developer Tools
   - Go to Console tab
   - Look for any red error messages
   - Check for messages starting with "Loading data for user:"

7. Direct API test:
   After getting your User ID from Debug, visit:
   https://article-hub-959205905728.asia-northeast1.run.app/api/articles?stage=inbox&user_id=YOUR_USER_ID_HERE
   
   This should return JSON data of your articles.

POSSIBLE ISSUES:
================
1. Your LINE User ID has no articles saved yet
2. Data exists but under different User ID
3. API calls failing (check browser console)
4. Firestore permission issues (unlikely on Cloud Run)

SOLUTIONS:
==========
1. Save articles via LINE bot first
2. Use test mode: add ?test=true to URL
3. Request data migration from test user
4. Clear browser cache and cookies, then login again
""")