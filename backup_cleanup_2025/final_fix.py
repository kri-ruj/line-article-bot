#!/usr/bin/env python3
"""
Final comprehensive fix for all JavaScript issues
"""

import re

def apply_final_fixes():
    with open('app_firestore_final.py', 'r') as f:
        content = f.read()
    
    print("Fixing JavaScript template literals...")
    
    # Count initial template literals
    initial_count = len(re.findall(r'\$\{[^}]+\}', content))
    print(f"Found {initial_count} template literals to fix")
    
    # Fix all ${...} patterns with proper string concatenation
    # This handles all cases generically
    content = re.sub(r'\$\{([^}]+)\}', r"' + \1 + '", content)
    
    # Additional specific fixes for common patterns
    replacements = [
        # Fix backticks to quotes
        (r'`([^`]*)\' \+ ([^`]+) \+ \'([^`]*)`', r"'\1' + \2 + '\3'"),
        
        # Fix double concatenation issues
        (r"' \+ '", ""),
        (r'" \+ "', ''),
        
        # Fix empty concatenations
        (r" \+ ''", ""),
        (r"'' \+ ", ""),
    ]
    
    for pattern, replacement in replacements:
        content = re.sub(pattern, replacement, content)
    
    # Count remaining template literals
    final_count = len(re.findall(r'\$\{[^}]+\}', content))
    
    # Write the fixed content
    with open('app_firestore_final.py', 'w') as f:
        f.write(content)
    
    print(f"\n✅ Fixed {initial_count - final_count} template literals!")
    print(f"   Remaining: {final_count}")
    
    if final_count == 0:
        print("\n🎉 All template literals have been fixed!")
    
    return initial_count - final_count

if __name__ == "__main__":
    fixed = apply_final_fixes()
    print("\n📝 Next steps:")
    print("1. Build and deploy")
    print("2. Push to GitHub")
    print("3. Test the application")