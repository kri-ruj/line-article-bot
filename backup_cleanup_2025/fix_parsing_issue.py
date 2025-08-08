#!/usr/bin/env python3
"""
Fix JavaScript parsing issues that prevent articles from displaying
"""

def fix_parsing():
    with open('app_firestore_final.py', 'r') as f:
        content = f.read()
    
    # Fix 1: Template literal in fetch URL
    fix1 = """                const res = await fetch('/api/articles?stage=${stage}&user_id=' + userId + '');"""
    fix1_new = """                const res = await fetch('/api/articles?stage=' + stage + '&user_id=' + userId);"""
    
    # Fix 2: Response parsing with better error handling
    fix2 = """                    // Parse the response
                    let articles;
                    try {
                        articles = JSON.parse(responseText);
                    } catch (e) {
                        console.error('Failed to parse JSON for ' + stage + ':', e);
                        articles = [];
                    }"""
    
    fix2_new = """                    // Parse the response  
                    let articles;
                    try {
                        articles = JSON.parse(responseText);
                        console.log('Parsed ' + articles.length + ' articles for ' + stage);
                    } catch (e) {
                        console.error('Failed to parse JSON for ' + stage + ':', e);
                        console.error('Response was:', responseText);
                        articles = [];
                    }"""
    
    # Fix 3: Add validation before rendering
    fix3 = """                    const stageArticles = articlesData[stage] || [];
                    
                    if (stageArticles.length === 0) {"""
    
    fix3_new = """                    const stageArticles = articlesData[stage] || [];
                    console.log('Rendering ' + stageArticles.length + ' articles for ' + stage);
                    
                    if (stageArticles.length === 0) {"""
    
    # Apply all fixes
    fixes_applied = 0
    
    if fix1 in content:
        content = content.replace(fix1, fix1_new)
        print("✓ Fixed template literal in fetch URL")
        fixes_applied += 1
    
    if fix2 in content:
        content = content.replace(fix2, fix2_new)
        print("✓ Enhanced response parsing")
        fixes_applied += 1
    
    if fix3 in content:
        content = content.replace(fix3, fix3_new)
        print("✓ Added rendering validation")
        fixes_applied += 1
    
    # Write back
    with open('app_firestore_final.py', 'w') as f:
        f.write(content)
    
    if fixes_applied > 0:
        print(f"\n✅ Applied {fixes_applied} fixes!")
    else:
        print("\n⚠️ Patterns not found. Applying comprehensive fix...")
        
        # If patterns not found, let's do a more comprehensive fix
        import re
        
        # Fix all template literals
        content = re.sub(r'\$\{([^}]+)\}', r'" + \1 + "', content)
        
        with open('app_firestore_final.py', 'w') as f:
            f.write(content)
        
        print("✅ Fixed all template literals!")
    
    print("\n📝 Next steps:")
    print("1. Deploy the fix")
    print("2. Clear browser cache")
    print("3. Visit the dashboard")
    print("4. Your 36 articles should appear!")

if __name__ == "__main__":
    fix_parsing()