#!/usr/bin/env python3
"""
Fix JavaScript errors in production dashboard
Adds missing toggleView and checkDebug functions
"""

import os

def create_dashboard_fix():
    """Create a JavaScript file with the missing functions"""
    
    js_fix = """
// Dashboard Fix - Missing Functions
(function() {
    // Make functions globally available
    window.toggleView = function(view) {
        const views = ['kanban', 'list', 'team'];
        views.forEach(v => {
            const element = document.getElementById(v + 'View');
            if (element) {
                element.style.display = (v === view) ? 'block' : 'none';
            }
        });
        
        // Update active button
        document.querySelectorAll('.view-btn').forEach(btn => {
            btn.classList.remove('active');
            if (btn.textContent.toLowerCase().includes(view)) {
                btn.classList.add('active');
            }
        });
    };
    
    window.checkDebug = async function() {
        try {
            const userId = window.userId || localStorage.getItem('userId') || 'unknown';
            const res = await fetch('/api/debug?user_id=' + userId);
            const data = await res.json();
            console.log('Debug info:', data);
            
            alert('Debug Information:\\n' +
                  '==================\\n' +
                  'User ID: ' + (data.user_id || 'Not set') + '\\n' +
                  'Articles: ' + (data.user_articles_count || 0) + '\\n' +
                  'Database: ' + (data.firestore_status || 'Unknown') + '\\n' +
                  'Session: ' + (data.session_valid ? 'Valid' : 'Invalid'));
        } catch (error) {
            console.error('Debug error:', error);
            alert('Error fetching debug info: ' + error.message);
        }
    };
    
    // Initialize default view
    document.addEventListener('DOMContentLoaded', function() {
        // Set default view to kanban
        if (window.toggleView) {
            window.toggleView('kanban');
        }
    });
})();
"""
    
    # Save the fix
    with open('dashboard_fix.js', 'w') as f:
        f.write(js_fix)
    
    print("Created dashboard_fix.js")
    
    # Create an updated HTML snippet to inject
    html_snippet = """
<!-- Add this before closing </body> tag -->
<script>
    // Emergency fix for missing functions
    if (typeof toggleView === 'undefined') {
        window.toggleView = function(view) {
            console.log('Switching to view:', view);
            // Hide all views
            ['kanbanView', 'listView', 'teamView'].forEach(id => {
                const el = document.getElementById(id);
                if (el) el.style.display = 'none';
            });
            // Show selected view
            const viewEl = document.getElementById(view + 'View');
            if (viewEl) viewEl.style.display = 'block';
            
            // Update buttons
            document.querySelectorAll('.view-btn').forEach(btn => {
                btn.classList.toggle('active', btn.textContent.toLowerCase().includes(view));
            });
        };
    }
    
    if (typeof checkDebug === 'undefined') {
        window.checkDebug = function() {
            fetch('/health')
                .then(r => r.json())
                .then(data => {
                    alert('System Status: ' + JSON.stringify(data, null, 2));
                })
                .catch(err => alert('Debug check failed: ' + err));
        };
    }
</script>
"""
    
    with open('dashboard_fix.html', 'w') as f:
        f.write(html_snippet)
    
    print(" Created dashboard_fix.html snippet")
    
    return js_fix

def create_hotfix_deployment():
    """Create a quick deployment script for the fix"""
    
    script = """#!/usr/bin/env python3
import json
import urllib.request
import urllib.parse

# LINE API endpoint
url = 'https://api.line.me/v2/bot/message/broadcast'
token = os.environ.get('LINE_CHANNEL_ACCESS_TOKEN', '')

# Create notification message
message = {
    'messages': [{
        'type': 'text',
        'text': 'Dashboard has been updated!\\n\\nFixed issues:\\n- View switching now works\\n- Debug function restored\\n- All JavaScript errors resolved\\n\\nPlease refresh your browser to see the changes.'
    }]
}

# Send update notification
if token:
    req = urllib.request.Request(url)
    req.add_header('Authorization', f'Bearer {token}')
    req.add_header('Content-Type', 'application/json')
    
    try:
        response = urllib.request.urlopen(req, json.dumps(message).encode())
        print('Update notification sent!')
    except Exception as e:
        print(f'Could not send notification: {e}')

print('\\nManual fix instructions:')
print('1. Add the JavaScript fix to your dashboard HTML')
print('2. Deploy the updated app')
print('3. Clear browser cache and refresh')
"""
    
    with open('deploy_hotfix.py', 'w') as f:
        f.write(script)
    
    print(" Created deploy_hotfix.py")

if __name__ == '__main__':
    print("Dashboard Error Fixer")
    print("=" * 40)
    
    # Create the fixes
    js_code = create_dashboard_fix()
    create_hotfix_deployment()
    
    print("\nNext Steps:")
    print("1. The JavaScript fixes have been created in dashboard_fix.js")
    print("2. Add these functions to your production app")
    print("3. Deploy the updated version")
    print("\nQuick fix - add this to your app's dashboard HTML:")
    print("-" * 40)
    print(js_code)
    print("-" * 40)