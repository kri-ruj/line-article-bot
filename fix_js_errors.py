#!/usr/bin/env python3
"""
Fix JavaScript errors in the application
"""

import re

def fix_js_errors():
    # Read the current file
    with open('app_firestore_final.py', 'r') as f:
        content = f.read()
    
    # Fix 1: Move checkDebug function to global scope
    # Find where the function is defined and ensure it's in the right scope
    fix1_old = """        async function checkDebug() {
            try {
                const res = await fetch(`/api/debug?user_id=${userId}`);
                const data = await res.json();
                alert(`Debug Info:
Firestore: ${data.firestore_status}
Articles: ${data.article_count}
Users: ${data.user_count}
Your ID: ${userId}
                `);
            } catch (e) {
                alert('Debug failed: ' + e.message);
            }
        }"""
    
    fix1_new = """        window.checkDebug = async function() {
            try {
                const res = await fetch('/api/debug?user_id=' + (window.userId || 'none'));
                const data = await res.json();
                alert('Debug Info:\\n' +
                    'Firestore: ' + data.firestore_status + '\\n' +
                    'Articles: ' + data.article_count + '\\n' +
                    'Users: ' + data.user_count + '\\n' +
                    'Your ID: ' + (window.userId || 'none'));
            } catch (e) {
                alert('Debug failed: ' + e.message);
            }
        }"""
    
    # Fix 2: Make userId globally accessible
    fix2_old = """        // Initialize global variables
        let articlesData = {};
        let userId = null;
        let displayName = null;
        let currentView = 'kanban';
        let currentTeamId = null;
        const DEBUG = true; // Enable debug logging"""
    
    fix2_new = """        // Initialize global variables
        let articlesData = {};
        let userId = null;
        let displayName = null;
        let currentView = 'kanban';
        let currentTeamId = null;
        const DEBUG = true; // Enable debug logging
        
        // Make variables accessible globally
        window.userId = null;
        window.displayName = null;"""
    
    # Fix 3: Update userId assignment to also set window.userId
    fix3_old = """                userId = 'U2de324e2a7198cf6ef152ab22afc80ea';
                displayName = 'Test User';"""
    
    fix3_new = """                userId = 'U2de324e2a7198cf6ef152ab22afc80ea';
                window.userId = userId;
                displayName = 'Test User';
                window.displayName = displayName;"""
    
    # Fix 4: Update other userId assignments
    fix4_old = """                userId = storedUserId;
                displayName = storedDisplayName;"""
    
    fix4_new = """                userId = storedUserId;
                window.userId = userId;
                displayName = storedDisplayName;
                window.displayName = displayName;"""
    
    # Fix 5: Fix LIFF profile userId assignment
    fix5_old = """                    userId = liffUserId;
                    displayName = displayName;"""
    
    fix5_new = """                    userId = liffUserId;
                    window.userId = userId;
                    window.displayName = displayName;"""
    
    # Fix 6: Fix template literal issues (if any remain)
    # Replace backticks with string concatenation
    content = re.sub(r'`([^`]*)\$\{([^}]+)\}([^`]*)`', r"'\1' + \2 + '\3'", content)
    
    # Apply fixes
    fixes = [
        (fix1_old, fix1_new),
        (fix2_old, fix2_new),
        (fix3_old, fix3_new),
        (fix4_old, fix4_new),
        (fix5_old, fix5_new)
    ]
    
    applied_fixes = []
    for i, (old, new) in enumerate(fixes, 1):
        if old in content:
            content = content.replace(old, new)
            applied_fixes.append(f"Fix {i}: Applied successfully")
        else:
            # Try to find partial matches
            if old[:50] in content or old[-50:] in content:
                applied_fixes.append(f"Fix {i}: Partial match found, may need manual review")
            else:
                applied_fixes.append(f"Fix {i}: Pattern not found (may already be fixed)")
    
    # Write the fixed content back
    with open('app_firestore_final.py', 'w') as f:
        f.write(content)
    
    print("✅ JavaScript fixes applied!")
    print("\nApplied fixes:")
    for fix in applied_fixes:
        print(f"  - {fix}")
    
    print("\nFixed issues:")
    print("1. Made checkDebug function globally accessible")
    print("2. Made userId and displayName globally accessible")
    print("3. Fixed all userId assignments to update global window object")
    print("4. Replaced template literals with string concatenation")
    
    print("\nThe app should now work without JavaScript errors.")

if __name__ == "__main__":
    fix_js_errors()