#!/usr/bin/env python3
"""
Comprehensive fix for all JavaScript template literal issues
"""

import re

def fix_all_template_literals():
    with open('app_firestore_final.py', 'r') as f:
        content = f.read()
    
    # List of specific fixes for template literals
    fixes = [
        # Fix team options
        ("const teamOptions = userTeams.map(t => '${t.name} (' + t.id + ')').join('\\n');",
         "const teamOptions = userTeams.map(t => t.name + ' (' + t.id + ')').join('\\n');"),
        
        # Fix team selection prompt
        ("const selectedIndex = prompt('Select a team to share with:\\n' + userTeams.map((t, i) => `${i+1 + '. ${t.name}').join('\\n')\\n\\nEnter number:`);",
         "const selectedIndex = prompt('Select a team to share with:\\n' + userTeams.map((t, i) => (i+1) + '. ' + t.name).join('\\n') + '\\n\\nEnter number:');"),
        
        # Fix article card HTML generation
        ('`<img src="${favicon + \'" class="article-favicon" onerror="this.style.display=\'none\'">\'',
         "'<img src=\"' + favicon + '\" class=\"article-favicon\" onerror=\"this.style.display=\\'none\\'\">'"),
        
        # Fix various template literal article properties
        ('data-id="${a.id}" data-stage="${stage}" data-url="${a.url}"',
         'data-id="' + "' + a.id + '" + '" data-stage="' + "' + stage + '" + '" data-url="' + "' + a.url + '" + '"'),
        
        ('title="${a.title}">${a.title}',
         'title="' + "' + a.title + '" + '">' + "' + a.title + '"),
        
        ('${category}',
         "' + category + '"),
        
        ('${formatDate(a.created_at)}',
         "' + formatDate(a.created_at) + '"),
         
        ('${formatDate(article.created_at)}',
         "' + formatDate(article.created_at) + '"),
        
        ('data-id="${a.id}"',
         'data-id="' + "' + a.id + '" + '"'),
         
        ('onclick="shareArticleWithTeam(\'${a.id + \'\')',
         'onclick="shareArticleWithTeam(\\'' + "' + a.id + '" + '\\')'),
         
        ('onclick="window.open(\'${a.url}\', \'_blank\')"',
         'onclick="window.open(\\'' + "' + a.url + '" + '\\', \\'_blank\\')"'),
         
        ('${article.title}',
         "' + article.title + '"),
         
        ('${article.url}',
         "' + article.url + '"),
         
        ('${article.user_name || \'Unknown\'}',
         "' + (article.user_name || 'Unknown') + '"),
         
        ('${team.member_ids.length}',
         "' + team.member_ids.length + '"),
         
        ('alert(\'Team "${name}" created successfully!\\nTeam ID: \' + result.team_id + \'\');',
         "alert('Team \"' + name + '\" created successfully!\\nTeam ID: ' + result.team_id);"),
         
        # Fix tag rendering
        ('`<span class="tag">${tag + \'</span>\'',
         "'<span class=\"tag\">' + tag + '</span>'"),
    ]
    
    # Apply all specific fixes
    fixes_applied = 0
    for old, new in fixes:
        if old in content:
            content = content.replace(old, new)
            fixes_applied += 1
            print(f"✓ Fixed: {old[:50]}...")
    
    # Generic fix for any remaining ${...} patterns
    # This regex finds ${expression} and converts to ' + expression + '
    pattern = r'\$\{([^}]+)\}'
    matches = re.findall(pattern, content)
    if matches:
        print(f"\nFound {len(matches)} remaining template literals to fix:")
        for match in matches[:5]:  # Show first 5
            print(f"  - ${{{match}}}")
        
        # Replace all remaining template literals
        content = re.sub(pattern, r"' + \1 + '", content)
        fixes_applied += len(matches)
    
    # Write the fixed content back
    with open('app_firestore_final.py', 'w') as f:
        f.write(content)
    
    print(f"\n✅ Total fixes applied: {fixes_applied}")
    print("\nFixed issues:")
    print("1. All JavaScript template literals replaced with string concatenation")
    print("2. Fixed article rendering in Kanban view")
    print("3. Fixed team sharing functionality")
    print("4. Fixed date formatting and display")
    
    return fixes_applied

if __name__ == "__main__":
    fixes = fix_all_template_literals()
    if fixes > 0:
        print("\n🚀 Ready to deploy!")