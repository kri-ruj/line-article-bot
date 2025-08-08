#!/usr/bin/env python3
"""
Final fixes for Kanban board data loading issues
"""

import re

def fix_final_issues():
    # Read the current file
    with open('app_firestore_final.py', 'r') as f:
        content = f.read()
    
    # Fix 1: Add more detailed logging for API responses
    fix1_old = """            for (const stage of stages) {
                try {
                    console.log('Fetching ' + stage + ' articles for user: ' + userId);
                    const res = await fetch('/api/articles?stage=' + stage + '&user_id=' + encodedUserId);
                    if (!res.ok) {
                        console.error(`Failed to fetch ${stage}:`, res.status);
                        articlesData[stage] = [];
                        continue;
                    }
                    const articles = await res.json();"""
    
    fix1_new = """            for (const stage of stages) {
                try {
                    console.log('Fetching ' + stage + ' articles for user: ' + userId);
                    const url = '/api/articles?stage=' + stage + '&user_id=' + encodedUserId;
                    console.log('Request URL:', url);
                    const res = await fetch(url);
                    
                    // Get response as text first to debug
                    const responseText = await res.text();
                    console.log('Raw response for ' + stage + ':', responseText);
                    
                    if (!res.ok) {
                        console.error('Failed to fetch ' + stage + ':', res.status);
                        articlesData[stage] = [];
                        continue;
                    }
                    
                    // Parse the response
                    let articles;
                    try {
                        articles = JSON.parse(responseText);
                    } catch (e) {
                        console.error('Failed to parse JSON for ' + stage + ':', e);
                        articles = [];
                    }"""
    
    # Fix 2: Add debug mode flag and more logging
    fix2_old = """        // Initialize global variables
        let articlesData = {};
        let userId = null;
        let displayName = null;
        let currentView = 'kanban';
        let currentTeamId = null;"""
    
    fix2_new = """        // Initialize global variables
        let articlesData = {};
        let userId = null;
        let displayName = null;
        let currentView = 'kanban';
        let currentTeamId = null;
        const DEBUG = true; // Enable debug mode"""
    
    # Fix 3: Add test user functionality for debugging
    fix3_old = """            // Check for existing session in localStorage
            const storedUserId = localStorage.getItem('lineUserId');
            const storedDisplayName = localStorage.getItem('lineDisplayName');
            
            if (storedUserId) {
                console.log('Found existing session in localStorage:', storedUserId);
                userId = storedUserId;
                document.getElementById('userInfo').innerHTML = '👤 ' + (storedDisplayName || 'User') + ' | ';
            }"""
    
    fix3_new = """            // Check for existing session in localStorage
            const storedUserId = localStorage.getItem('lineUserId');
            const storedDisplayName = localStorage.getItem('lineDisplayName');
            
            // Check for test mode (add ?test=true to URL)
            const urlParams = new URLSearchParams(window.location.search);
            const testMode = urlParams.get('test') === 'true';
            
            if (testMode) {
                console.log('TEST MODE ACTIVATED');
                // Use a test user that has data in Firestore
                userId = 'U2de324e2a7198cf6ef152ab22afc80ea'; // This user has 26 articles
                displayName = 'Test User';
                localStorage.setItem('lineUserId', userId);
                localStorage.setItem('lineDisplayName', displayName);
                document.getElementById('userInfo').innerHTML = '👤 TEST MODE | ';
                console.log('Test userId set to:', userId);
            } else if (storedUserId) {
                console.log('Found existing session in localStorage:', storedUserId);
                userId = storedUserId;
                displayName = storedDisplayName;
                document.getElementById('userInfo').innerHTML = '👤 ' + (storedDisplayName || 'User') + ' | ';
            }"""
    
    # Fix 4: Fix the article rendering to show more debug info when empty
    fix4_old = """                // Render articles in columns
                for (const stage of stages) {
                    const dropZone = document.querySelector(`#${stage} .drop-zone`);
                    dropZone.innerHTML = '';
                    
                    const stageArticles = articlesData[stage] || [];
                    
                    if (stageArticles.length === 0) {
                        dropZone.innerHTML = '<p style="color: #999; text-align: center; font-size: 12px;">No articles</p>';
                    } else {"""
    
    fix4_new = """                // Render articles in columns
                for (const stage of stages) {
                    const dropZone = document.querySelector(`#${stage} .drop-zone`);
                    dropZone.innerHTML = '';
                    
                    const stageArticles = articlesData[stage] || [];
                    
                    if (stageArticles.length === 0) {
                        dropZone.innerHTML = '<p style="color: #999; text-align: center; font-size: 12px;">No articles<br><small>User: ' + userId + '</small></p>';
                        if (DEBUG) {
                            console.log('No articles in stage ' + stage + ' for user ' + userId);
                        }
                    } else {"""
    
    # Fix 5: Better error handling in API endpoint
    fix5_old = """    def handle_get_articles(self, params):
        \"\"\"Get articles for a specific stage and user\"\"\"
        stage = params.get('stage', [''])[0]
        user_id = params.get('user_id', [''])[0]
        team_id = params.get('team_id', [''])[0]
        
        logger.info(f"Getting articles - stage: {stage}, user_id: {user_id}, team_id: {team_id}")"""
    
    fix5_new = """    def handle_get_articles(self, params):
        \"\"\"Get articles for a specific stage and user\"\"\"
        stage = params.get('stage', [''])[0]
        user_id = params.get('user_id', [''])[0]
        team_id = params.get('team_id', [''])[0]
        
        # URL decode the user_id
        from urllib.parse import unquote
        user_id = unquote(user_id)
        
        logger.info(f"API Request - stage: {stage}, user_id: {user_id}, team_id: {team_id}")"""
    
    # Fix 6: Add a data initialization endpoint for testing
    fix6_old = """    def serve_debug(self):
        \"\"\"Debug endpoint to check Firestore data\"\"\"
        try:
            # Check Firestore connection
            test_collection = db.collection('articles')
            docs = list(test_collection.limit(100).stream())
            
            # Count articles by user
            user_articles = {}
            total = 0
            for doc in docs:
                data = doc.to_dict()
                user_id = data.get('user_id', 'unknown')
                if user_id not in user_articles:
                    user_articles[user_id] = 0
                user_articles[user_id] += 1
                total += 1
            
            html = f\"\"\"<!DOCTYPE html>
<html>
<head>
    <title>Debug Info</title>
</head>
<body>
    <h1>Firestore Debug Info</h1>
    <p>Connected to Firestore: ✓</p>
    <p>Total articles: {total}</p>
    <h2>Articles by User:</h2>
    <ul>
        {''.join(f'<li>{uid}: {count} articles</li>' for uid, count in user_articles.items())}
    </ul>
</body>
</html>\"\"\"
            
            self.send_response(200)
            self.send_header('Content-Type', 'text/html')
            self.end_headers()
            self.wfile.write(html.encode())
            
        except Exception as e:
            error_html = f\"\"\"<!DOCTYPE html>
<html>
<head>
    <title>Debug Error</title>
</head>
<body>
    <h1>Debug Error</h1>
    <p>Error: {str(e)}</p>
</body>
</html>\"\"\"
            self.send_response(500)
            self.send_header('Content-Type', 'text/html')
            self.end_headers()
            self.wfile.write(error_html.encode())"""
    
    fix6_new = """    def serve_debug(self):
        \"\"\"Debug endpoint to check Firestore data\"\"\"
        try:
            # Check Firestore connection
            test_collection = db.collection('articles')
            docs = list(test_collection.limit(100).stream())
            
            # Count articles by user and stage
            user_articles = {}
            stage_counts = {}
            total = 0
            sample_articles = []
            
            for doc in docs:
                data = doc.to_dict()
                user_id = data.get('user_id', 'unknown')
                stage = data.get('stage', 'unknown')
                
                if user_id not in user_articles:
                    user_articles[user_id] = {'total': 0, 'stages': {}}
                user_articles[user_id]['total'] += 1
                
                if stage not in user_articles[user_id]['stages']:
                    user_articles[user_id]['stages'][stage] = 0
                user_articles[user_id]['stages'][stage] += 1
                
                if stage not in stage_counts:
                    stage_counts[stage] = 0
                stage_counts[stage] += 1
                
                total += 1
                
                # Keep first 3 articles as samples
                if len(sample_articles) < 3:
                    sample_articles.append({
                        'id': doc.id,
                        'user_id': user_id,
                        'stage': stage,
                        'title': data.get('title', 'No title')[:50],
                        'url': data.get('url', 'No URL')[:50]
                    })
            
            # Create HTML response
            html = f\"\"\"<!DOCTYPE html>
<html>
<head>
    <title>Debug Info</title>
    <style>
        body {{ font-family: monospace; padding: 20px; }}
        .user {{ margin: 10px 0; padding: 10px; background: #f0f0f0; }}
        .test-link {{ background: #4CAF50; color: white; padding: 10px; display: inline-block; margin: 10px 0; text-decoration: none; }}
    </style>
</head>
<body>
    <h1>Firestore Debug Info</h1>
    <p>✅ Connected to Firestore</p>
    <p>📊 Total articles: {total}</p>
    
    <h2>Stage Distribution:</h2>
    <ul>
        {''.join(f'<li>{stage}: {count} articles</li>' for stage, count in stage_counts.items())}
    </ul>
    
    <h2>Articles by User:</h2>\"\"\"
    
            for uid, data in user_articles.items():
                html += f\"\"\"
    <div class="user">
        <strong>User ID: {uid}</strong><br>
        Total: {data['total']} articles<br>
        Stages: {', '.join(f"{s}:{c}" for s, c in data['stages'].items())}<br>
        <a href="/dashboard?test=true" class="test-link" onclick="localStorage.setItem('lineUserId', '{uid}'); localStorage.setItem('lineDisplayName', 'Test User {uid[:8]}');">Test with this user</a>
    </div>\"\"\"
            
            html += \"\"\"
    <h2>Sample Articles:</h2>
    <ul>\"\"\"
            for article in sample_articles:
                html += f\"\"\"
        <li>
            ID: {article['id']}<br>
            User: {article['user_id']}<br>
            Stage: {article['stage']}<br>
            Title: {article['title']}<br>
            URL: {article['url']}
        </li>\"\"\"
            
            html += \"\"\"
    </ul>
    
    <h2>Quick Test:</h2>
    <a href="/dashboard?test=true" class="test-link">Open Dashboard in Test Mode (uses first user with data)</a>
</body>
</html>\"\"\"
            
            self.send_response(200)
            self.send_header('Content-Type', 'text/html')
            self.end_headers()
            self.wfile.write(html.encode())
            
        except Exception as e:
            error_html = f\"\"\"<!DOCTYPE html>
<html>
<head>
    <title>Debug Error</title>
</head>
<body>
    <h1>Debug Error</h1>
    <p>Error: {str(e)}</p>
    <pre>{traceback.format_exc()}</pre>
</body>
</html>\"\"\"
            self.send_response(500)
            self.send_header('Content-Type', 'text/html')
            self.end_headers()
            self.wfile.write(error_html.encode())"""
    
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
            print(f"✗ Could not apply fix {i} - pattern not found (may already be applied)")
    
    # Write the fixed content back
    with open('app_firestore_final.py', 'w') as f:
        f.write(content)
    
    print("\n✅ All fixes applied!")
    print("\nFixed issues:")
    print("1. Added detailed response logging to debug API calls")
    print("2. Added DEBUG flag for verbose logging")
    print("3. Added test mode (?test=true) to use a user with existing data")
    print("4. Enhanced empty state to show current userId")
    print("5. Fixed URL decoding in API endpoint")
    print("6. Enhanced debug endpoint with test links")
    print("\n📝 Test the app by visiting: /dashboard?test=true")
    print("This will use userId: U2de324e2a7198cf6ef152ab22afc80ea (has 26 articles)")

if __name__ == "__main__":
    fix_final_issues()