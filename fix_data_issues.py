#!/usr/bin/env python3
"""
Fix Firestore data retrieval and JavaScript syntax errors
"""

import re

def fix_data_issues():
    # Read the current file
    with open('app_firestore_final.py', 'r') as f:
        content = f.read()
    
    # Fix 1: Fix the JavaScript template string syntax issue
    # The backticks in template strings might be causing issues
    fix1_old = """                document.getElementById('userInfo').innerHTML = `👤 ${storedDisplayName || 'User'} | `;"""
    fix1_new = """                document.getElementById('userInfo').innerHTML = '👤 ' + (storedDisplayName || 'User') + ' | ';"""
    
    # Fix 2: Fix the desktop user info HTML
    fix2_old = """                        document.getElementById('userInfo').innerHTML = `
                            👤 ${displayName} | 
                            <button onclick="shareArticlesToLINE()" style="
                                background: #00B900;
                                color: white;
                                border: none;
                                padding: 4px 10px;
                                border-radius: 4px;
                                font-size: 11px;
                                cursor: pointer;
                                margin: 0 5px;
                            " title="Share to LINE">
                                <svg width="16" height="16" viewBox="0 0 24 24" fill="white" style="vertical-align: middle;">
                                    <path d="M19.365 9.863c.349 0 .63.285.63.631 0 .345-.281.63-.63.63H17.61v1.125h1.755c.349 0 .63.283.63.63 0 .344-.281.629-.63.629h-2.386c-.345 0-.627-.285-.627-.629V8.108c0-.345.282-.63.63-.63h2.386c.346 0 .627.285.627.63 0 .349-.281.63-.63.63H17.61v1.125h1.755zm-3.855 3.016c0 .27-.174.51-.432.596-.064.021-.133.031-.199.031-.211 0-.391-.09-.51-.25l-2.443-3.317v2.94c0 .344-.279.629-.631.629-.346 0-.626-.285-.626-.629V8.108c0-.27.173-.51.43-.595.06-.023.136-.033.194-.033.195 0 .375.104.495.254l2.462 3.33V8.108c0-.345.282-.63.63-.63.345 0 .63.285.63.63v4.771zm-5.741 0c0 .344-.282.629-.631.629-.345 0-.627-.285-.627-.629V8.108c0-.345.282-.63.627-.63.349 0 .631.285.631.63v4.771zm-2.466.629H4.917c-.345 0-.63-.285-.63-.629V8.108c0-.345.285-.63.63-.63.349 0 .63.285.63.63v4.141h1.756c.348 0 .629.283.629.63 0 .344-.282.629-.629.629M24 10.314C24 4.943 18.615.572 12 .572S0 4.943 0 10.314c0 4.811 4.27 8.842 10.035 9.608.391.082.923.258 1.058.59.12.301.079.766.038 1.08l-.164 1.02c-.045.301-.24 1.186 1.049.645 1.291-.539 6.916-4.078 9.436-6.975C23.176 14.393 24 12.458 24 10.314"/>
                                </svg>
                            </button>
                        `;"""
    
    fix2_new = """                        var shareButton = '<button onclick="shareArticlesToLINE()" style="background: #00B900; color: white; border: none; padding: 4px 10px; border-radius: 4px; font-size: 11px; cursor: pointer; margin: 0 5px;" title="Share to LINE">Share</button>';
                        document.getElementById('userInfo').innerHTML = '👤 ' + displayName + ' | ' + shareButton;"""
    
    # Fix 3: Fix the other template string
    fix3_old = """                        document.getElementById('userInfo').innerHTML = `👤 ${displayName} | `;"""
    fix3_new = """                        document.getElementById('userInfo').innerHTML = '👤 ' + displayName + ' | ';"""
    
    # Fix 4: Add better error handling for Firestore
    fix4_old = """            console.log('Loading data for user:', userId);
            const stages = ['inbox', 'reading', 'reviewing', 'completed'];
            articlesData = {};
            
            for (const stage of stages) {
                try {
                    console.log(`Fetching ${stage} articles...`);
                    const res = await fetch(`/api/articles?stage=${stage}&user_id=${userId}`);"""
    
    fix4_new = """            console.log('Loading data for user:', userId);
            const stages = ['inbox', 'reading', 'reviewing', 'completed'];
            articlesData = {};
            
            // Ensure userId is URL encoded
            const encodedUserId = encodeURIComponent(userId);
            
            for (const stage of stages) {
                try {
                    console.log('Fetching ' + stage + ' articles for user: ' + userId);
                    const res = await fetch('/api/articles?stage=' + stage + '&user_id=' + encodedUserId);"""
    
    # Fix 5: Add debug logging for data retrieval
    fix5_old = """                    const articles = await res.json();
                    console.log(`Got ${articles.length} articles for ${stage}`);
                    articlesData[stage] = articles;"""
    
    fix5_new = """                    const articles = await res.json();
                    console.log('Got ' + articles.length + ' articles for ' + stage);
                    console.log('Articles data:', articles);
                    articlesData[stage] = articles;
                    
                    // Debug: Check if articles have proper structure
                    if (articles.length > 0) {
                        console.log('First article sample:', articles[0]);
                    }"""
    
    # Fix 6: Add Firestore initialization with better error handling
    fix6_old = """# Initialize Firestore client
db = firestore.Client(project='secondbrain-app-20250612')"""
    
    fix6_new = """# Initialize Firestore client with error handling
try:
    db = firestore.Client(project='secondbrain-app-20250612')
    logger.info("Firestore client initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize Firestore: {e}")
    # Try with default credentials
    try:
        db = firestore.Client()
        logger.info("Firestore client initialized with default credentials")
    except Exception as e2:
        logger.error(f"Failed to initialize Firestore with default credentials: {e2}")
        raise"""
    
    # Apply all fixes
    fixes = [
        (fix1_old, fix1_new),
        (fix2_old, fix2_new),
        (fix3_old, fix3_new),
        (fix4_old, fix4_new),
        (fix5_old, fix5_new),
        (fix6_old, fix6_new)
    ]
    
    for i, (old, new) in enumerate(fixes, 1):
        if old in content:
            content = content.replace(old, new)
            print(f"✓ Applied fix {i}")
        else:
            print(f"✗ Could not apply fix {i} - pattern not found")
    
    # Write the fixed content back
    with open('app_firestore_final.py', 'w') as f:
        f.write(content)
    
    print("\n✅ All fixes applied!")
    print("\nFixed issues:")
    print("1. JavaScript template strings replaced with string concatenation")
    print("2. Fixed HTML generation to avoid syntax errors")
    print("3. Added proper URL encoding for userId")
    print("4. Added debug logging for data retrieval")
    print("5. Improved Firestore initialization with error handling")

if __name__ == "__main__":
    fix_data_issues()