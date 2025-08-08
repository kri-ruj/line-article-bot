#!/usr/bin/env python3
"""
Fix data loading for user Udcd08cd8a445c68f462a739e8898abb9
"""

def fix_data_loading():
    # Read the current file
    with open('app_firestore_final.py', 'r') as f:
        content = f.read()
    
    # Add a direct test for this specific user
    fix1 = """            // Check for test mode
            const urlParams = new URLSearchParams(window.location.search);
            const testMode = urlParams.get('test') === 'true';
            
            if (testMode) {
                console.log('🧪 TEST MODE ACTIVATED');
                // Use test user with known data
                userId = 'U2de324e2a7198cf6ef152ab22afc80ea';
                window.userId = userId;
                displayName = 'Test User';
                window.displayName = displayName;"""
    
    fix1_new = """            // Check for test mode
            const urlParams = new URLSearchParams(window.location.search);
            const testMode = urlParams.get('test') === 'true';
            
            // Special handling for known user with data
            if (storedUserId === 'Udcd08cd8a445c68f462a739e8898abb9') {
                console.log('✅ Recognized user with 36 articles!');
                userId = storedUserId;
                window.userId = storedUserId;
            }
            
            if (testMode) {
                console.log('🧪 TEST MODE ACTIVATED');
                // Use test user with known data
                userId = 'U2de324e2a7198cf6ef152ab22afc80ea';
                window.userId = userId;
                displayName = 'Test User';
                window.displayName = displayName;"""
    
    # Add more detailed logging for this user
    fix2 = """            for (const stage of stages) {
                try {
                    const url = '/api/articles?stage=' + stage + '&user_id=' + encodedUserId;
                    console.log('Fetching from:', url);
                    const res = await fetch(url);"""
    
    fix2_new = """            // Special logging for debugging
            if (userId === 'Udcd08cd8a445c68f462a739e8898abb9') {
                console.log('🔍 Loading articles for Udcd08cd8a445c68f462a739e8898abb9');
                console.log('This user has 36 articles in Firestore');
            }
            
            for (const stage of stages) {
                try {
                    const url = '/api/articles?stage=' + stage + '&user_id=' + encodedUserId;
                    console.log('Fetching from:', url);
                    console.log('Encoded userId being sent:', encodedUserId);
                    const res = await fetch(url);"""
    
    # Apply fixes
    if fix1 in content:
        content = content.replace(fix1, fix1_new)
        print("✓ Added special handling for your user ID")
    
    if fix2 in content:
        content = content.replace(fix2, fix2_new)
        print("✓ Added detailed logging")
    
    # Write back
    with open('app_firestore_final.py', 'w') as f:
        f.write(content)
    
    print("\n✅ Fixes applied!")
    print("\nDEBUGGING STEPS:")
    print("1. Clear your browser cache completely")
    print("2. Visit: https://article-hub-959205905728.asia-northeast1.run.app/dashboard")
    print("3. Open browser console (F12)")
    print("4. Look for messages about 'Udcd08cd8a445c68f462a739e8898abb9'")
    print("5. Check what the API returns")
    print("\nDIRECT API TEST:")
    print("Visit this URL directly:")
    print("https://article-hub-959205905728.asia-northeast1.run.app/api/articles?stage=inbox&user_id=Udcd08cd8a445c68f462a739e8898abb9")
    print("\nThis should return your articles in JSON format.")

if __name__ == "__main__":
    fix_data_loading()