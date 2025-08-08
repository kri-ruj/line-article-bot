#!/usr/bin/env python3
"""
Apply targeted fixes to resolve data loading issues
"""

import re

def apply_targeted_fixes():
    # Read the current file
    with open('app_firestore_final.py', 'r') as f:
        content = f.read()
    
    # Fix 1: Add DEBUG flag and test mode
    fix1 = """        // Initialize global variables
        let articlesData = {};
        let userId = null;
        let displayName = null;
        let currentView = 'kanban';
        let currentTeamId = null;"""
    
    fix1_new = """        // Initialize global variables
        let articlesData = {};
        let userId = null;
        let displayName = null;
        let currentView = 'kanban';
        let currentTeamId = null;
        const DEBUG = true; // Enable debug logging"""
    
    if fix1 in content:
        content = content.replace(fix1, fix1_new)
        print("✓ Added DEBUG flag")
    
    # Fix 2: Add test mode detection
    fix2 = """            // Check for existing session in localStorage
            const storedUserId = localStorage.getItem('lineUserId');
            const storedDisplayName = localStorage.getItem('lineDisplayName');
            
            if (storedUserId) {"""
    
    fix2_new = """            // Check for existing session in localStorage
            const storedUserId = localStorage.getItem('lineUserId');
            const storedDisplayName = localStorage.getItem('lineDisplayName');
            
            // Check for test mode
            const urlParams = new URLSearchParams(window.location.search);
            const testMode = urlParams.get('test') === 'true';
            
            if (testMode) {
                console.log('🧪 TEST MODE ACTIVATED');
                // Use test user with known data
                userId = 'U2de324e2a7198cf6ef152ab22afc80ea';
                displayName = 'Test User';
                localStorage.setItem('lineUserId', userId);
                localStorage.setItem('lineDisplayName', displayName);
                document.getElementById('userInfo').innerHTML = '🧪 TEST MODE | ';
                console.log('Test userId:', userId);
                
                // Load data immediately in test mode
                setTimeout(() => {
                    loadKanbanData();
                }, 100);
            } else if (storedUserId) {"""
    
    if fix2 in content:
        content = content.replace(fix2, fix2_new)
        print("✓ Added test mode")
    
    # Fix 3: Improve loadKanbanData error handling
    fix3 = """            console.log('Loading data for user:', userId);
            const stages = ['inbox', 'reading', 'reviewing', 'completed'];
            articlesData = {};
            
            // Ensure userId is URL encoded
            const encodedUserId = encodeURIComponent(userId);
            
            for (const stage of stages) {
                try {
                    console.log('Fetching ' + stage + ' articles for user: ' + userId);
                    const res = await fetch('/api/articles?stage=' + stage + '&user_id=' + encodedUserId);"""
    
    fix3_new = """            console.log('Loading data for user:', userId);
            const stages = ['inbox', 'reading', 'reviewing', 'completed'];
            articlesData = {};
            
            // Ensure userId is URL encoded
            const encodedUserId = encodeURIComponent(userId);
            console.log('Encoded userId:', encodedUserId);
            
            for (const stage of stages) {
                try {
                    const url = '/api/articles?stage=' + stage + '&user_id=' + encodedUserId;
                    console.log('Fetching from:', url);
                    const res = await fetch(url);"""
    
    if fix3 in content:
        content = content.replace(fix3, fix3_new)
        print("✓ Improved API logging")
    
    # Fix 4: Better empty state display
    fix4 = """                    if (stageArticles.length === 0) {
                        dropZone.innerHTML = '<p style="color: #999; text-align: center; font-size: 12px;">No articles</p>';
                    } else {"""
    
    fix4_new = """                    if (stageArticles.length === 0) {
                        const debugInfo = window.DEBUG ? '<br><small style="font-size: 10px;">User: ' + (userId ? userId.substring(0, 8) + '...' : 'none') + '</small>' : '';
                        dropZone.innerHTML = '<p style="color: #999; text-align: center; font-size: 12px;">No articles' + debugInfo + '</p>';
                    } else {"""
    
    if fix4 in content:
        content = content.replace(fix4, fix4_new)
        print("✓ Enhanced empty state")
    
    # Fix 5: Add URL decoding in API handler
    fix5 = """    def handle_get_articles(self, params):
        \"\"\"Get articles for a specific stage and user\"\"\"
        stage = params.get('stage', [''])[0]
        user_id = params.get('user_id', [''])[0]
        team_id = params.get('team_id', [''])[0]
        
        logger.info(f"Getting articles - stage: {stage}, user_id: {user_id}, team_id: {team_id}")"""
    
    fix5_new = """    def handle_get_articles(self, params):
        \"\"\"Get articles for a specific stage and user\"\"\"
        from urllib.parse import unquote
        
        stage = params.get('stage', [''])[0]
        user_id = unquote(params.get('user_id', [''])[0])  # URL decode
        team_id = params.get('team_id', [''])[0]
        
        logger.info(f"API Request - stage: {stage}, user_id: {user_id}, team_id: {team_id}")"""
    
    if fix5 in content:
        content = content.replace(fix5, fix5_new)
        print("✓ Added URL decoding in API")
    
    # Write the fixed content back
    with open('app_firestore_final.py', 'w') as f:
        f.write(content)
    
    print("\n✅ Targeted fixes applied!")
    print("\n📝 To test:")
    print("1. Deploy the updated app")
    print("2. Visit /dashboard?test=true to use test mode")
    print("3. Or check /debug to see available users and test with them")

if __name__ == "__main__":
    apply_targeted_fixes()