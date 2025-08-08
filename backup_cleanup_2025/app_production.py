#!/usr/bin/env python3
"""
Production-ready Article Intelligence Hub
With LINE Login, user database, and Cloud Run support
"""

import os
import json
import sqlite3
import logging
import hashlib
import random
import re
import secrets
from datetime import datetime, timedelta
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs, unquote
import urllib.request
import urllib.error

# Configuration from environment variables
PORT = int(os.environ.get('PORT', 8080))  # Cloud Run uses PORT env var
DB_PATH = os.environ.get('DB_PATH', '/tmp/articles.db')  # Use /tmp for Cloud Run
LINE_CHANNEL_ACCESS_TOKEN = os.environ.get('LINE_CHANNEL_ACCESS_TOKEN', '')
LINE_CHANNEL_SECRET = os.environ.get('LINE_CHANNEL_SECRET', '')
LINE_LOGIN_CHANNEL_ID = os.environ.get('LINE_LOGIN_CHANNEL_ID', '')
LINE_LOGIN_CHANNEL_SECRET = os.environ.get('LINE_LOGIN_CHANNEL_SECRET', '')
LIFF_ID = os.environ.get('LIFF_ID', '2007552096-GxP76rNd')
BASE_URL = os.environ.get('BASE_URL', 'https://article-hub-2ndbrain.a.run.app')

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class RequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed_path = urlparse(self.path)
        
        routes = {
            '/': self.serve_homepage,
            '/login': self.handle_line_login,
            '/callback': self.handle_login_callback,
            '/api/articles': self.serve_articles,
            '/api/user': self.serve_user_info,
            '/manifest.json': self.serve_manifest,
            '/service-worker.js': self.serve_service_worker,
            '/health': self.health_check
        }
        
        handler = routes.get(parsed_path.path)
        if handler:
            handler()
        elif parsed_path.path.startswith('/icon-'):
            self.serve_icon()
        else:
            self.send_error(404)
    
    def do_POST(self):
        parsed_path = urlparse(self.path)
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        
        routes = {
            '/webhook': self.handle_line_webhook,  # LINE webhook endpoint
            '/api/articles': self.handle_add_article,
            '/api/articles/update': self.handle_update_article,
            '/api/logout': self.handle_logout
        }
        
        handler = routes.get(parsed_path.path)
        if handler:
            handler(post_data) if parsed_path.path != '/api/logout' else handler()
        else:
            self.send_error(404)
    
    def health_check(self):
        """Health check endpoint for Cloud Run"""
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps({'status': 'healthy'}).encode())
    
    def handle_line_login(self):
        """Redirect to LINE Login"""
        state = secrets.token_urlsafe(32)
        nonce = secrets.token_urlsafe(32)
        
        # Store state in session (in production, use proper session management)
        # For now, we'll use a simple cookie
        
        redirect_uri = f"{BASE_URL}/callback"
        auth_url = (
            f"https://access.line.me/oauth2/v2.1/authorize?"
            f"response_type=code&"
            f"client_id={LINE_LOGIN_CHANNEL_ID}&"
            f"redirect_uri={redirect_uri}&"
            f"state={state}&"
            f"scope=profile%20openid&"
            f"nonce={nonce}"
        )
        
        self.send_response(302)
        self.send_header('Location', auth_url)
        self.send_header('Set-Cookie', f'auth_state={state}; HttpOnly; Secure; SameSite=Lax')
        self.end_headers()
    
    def handle_login_callback(self):
        """Handle LINE Login callback"""
        parsed = urlparse(self.path)
        params = parse_qs(parsed.query)
        
        code = params.get('code', [None])[0]
        state = params.get('state', [None])[0]
        
        if not code:
            self.send_error(400, 'Missing authorization code')
            return
        
        try:
            # Exchange code for token
            token_url = 'https://api.line.me/oauth2/v2.1/token'
            token_data = urllib.parse.urlencode({
                'grant_type': 'authorization_code',
                'code': code,
                'redirect_uri': f"{BASE_URL}/callback",
                'client_id': LINE_LOGIN_CHANNEL_ID,
                'client_secret': LINE_LOGIN_CHANNEL_SECRET
            }).encode()
            
            req = urllib.request.Request(token_url, data=token_data, method='POST')
            req.add_header('Content-Type', 'application/x-www-form-urlencoded')
            
            with urllib.request.urlopen(req) as response:
                token_response = json.loads(response.read())
            
            access_token = token_response.get('access_token')
            id_token = token_response.get('id_token')
            
            # Get user profile
            profile_url = 'https://api.line.me/v2/profile'
            profile_req = urllib.request.Request(profile_url)
            profile_req.add_header('Authorization', f'Bearer {access_token}')
            
            with urllib.request.urlopen(profile_req) as response:
                profile = json.loads(response.read())
            
            # Save user to database
            user_id = profile['userId']
            display_name = profile.get('displayName', 'User')
            picture_url = profile.get('pictureUrl', '')
            
            save_user(user_id, display_name, picture_url)
            
            # Create session token
            session_token = secrets.token_urlsafe(32)
            save_session(session_token, user_id)
            
            # Redirect to main page with session
            self.send_response(302)
            self.send_header('Location', '/')
            self.send_header('Set-Cookie', f'session={session_token}; HttpOnly; Secure; SameSite=Lax; Max-Age=2592000')
            self.end_headers()
            
        except Exception as e:
            logging.error(f"Login error: {e}")
            self.send_error(500, 'Login failed')
    
    def serve_homepage(self):
        """Serve the main application page"""
        # Check if user is logged in
        cookie = self.headers.get('Cookie', '')
        session_token = None
        user = None
        
        if 'session=' in cookie:
            session_token = cookie.split('session=')[1].split(';')[0]
            user = get_user_by_session(session_token)
        
        # Build user section HTML
        if user:
            user_section_html = f'''
                <img src="{user['picture_url']}" alt="{user['display_name']}" class="user-avatar">
                <span class="user-name">{user['display_name']}</span>
                <button onclick="logout()" class="logout-btn">Logout</button>
            '''
            main_content_html = f'''
                <div class="welcome-message">
                    <h1>Welcome back, {user['display_name']}!</h1>
                    <p>Manage your articles and track your reading progress</p>
                </div>
                
                <div class="add-article-form">
                    <input type="url" class="url-input" id="urlInput" placeholder="Paste article URL here...">
                    <button class="add-btn" onclick="addArticle()">Add Article</button>
                </div>
                
                <div id="articlesContainer">
                    <!-- Articles will be loaded here -->
                </div>
            '''
        else:
            user_section_html = '<a href="/login" class="login-btn">Login with LINE</a>'
            main_content_html = '''
                <div class="login-prompt">
                    <h2>Welcome to Article Intelligence Hub</h2>
                    <p>Sign in with your LINE account to start managing your articles</p>
                    <a href="/login" class="line-login-btn">
                        <img src="data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjQiIGhlaWdodD0iMjQiIHZpZXdCb3g9IjAgMCAyNCAyNCIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPHBhdGggZD0iTTEyIDJDNi40OCwyIDIgNi40OCAyIDEyQzIgMTcuNTIgNi40OCAyMiAxMiAyMkMxNy41MiAyMiAyMiAxNy41MiAyMiAxMkMyMiA2LjQ4IDE3LjUyIDIgMTIgMiIgZmlsbD0iIzAwQjkwMCIvPgo8L3N2Zz4=" width="24" height="24">
                        Login with LINE
                    </a>
                </div>
            '''
        
        html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>📚 Article Intelligence Hub</title>
    
    <!-- PWA Meta Tags -->
    <meta name="theme-color" content="#667eea">
    <meta name="apple-mobile-web-app-capable" content="yes">
    <meta name="apple-mobile-web-app-status-bar-style" content="default">
    <meta name="apple-mobile-web-app-title" content="Article Hub">
    <link rel="manifest" href="/manifest.json">
    <link rel="apple-touch-icon" href="/icon-192x192.png">
    
    <!-- LINE LIFF SDK -->
    <script src="https://static.line-scdn.net/liff/edge/2/sdk.js"></script>
    
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            color: #333;
        }}
        
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }}
        
        /* Header with user info */
        .header {{
            background: rgba(255, 255, 255, 0.98);
            backdrop-filter: blur(20px);
            border-radius: 12px;
            padding: 15px 20px;
            margin-bottom: 20px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            box-shadow: 0 4px 20px rgba(0,0,0,0.1);
        }}
        
        .logo {{
            font-size: 24px;
            font-weight: bold;
            background: linear-gradient(135deg, #667eea, #764ba2);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }}
        
        .user-section {{
            display: flex;
            align-items: center;
            gap: 10px;
        }}
        
        .user-avatar {{
            width: 40px;
            height: 40px;
            border-radius: 50%;
            object-fit: cover;
        }}
        
        .user-name {{
            font-weight: 500;
        }}
        
        .login-btn, .logout-btn {{
            padding: 8px 20px;
            background: #00B900;
            color: white;
            border: none;
            border-radius: 20px;
            font-weight: 500;
            cursor: pointer;
            text-decoration: none;
            display: inline-block;
        }}
        
        .logout-btn {{
            background: #666;
        }}
        
        /* Main content */
        .main-content {{
            background: rgba(255, 255, 255, 0.98);
            border-radius: 12px;
            padding: 30px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.1);
        }}
        
        .welcome-message {{
            text-align: center;
            margin-bottom: 30px;
        }}
        
        .welcome-message h1 {{
            color: #333;
            margin-bottom: 10px;
        }}
        
        .welcome-message p {{
            color: #666;
        }}
        
        /* Articles section */
        .articles-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
            gap: 20px;
            margin-top: 30px;
        }}
        
        .article-card {{
            background: white;
            border-radius: 10px;
            padding: 20px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.08);
            transition: transform 0.3s;
        }}
        
        .article-card:hover {{
            transform: translateY(-5px);
            box-shadow: 0 4px 20px rgba(0,0,0,0.15);
        }}
        
        /* Login prompt */
        .login-prompt {{
            text-align: center;
            padding: 60px 20px;
        }}
        
        .login-prompt h2 {{
            margin-bottom: 20px;
            color: #333;
        }}
        
        .login-prompt p {{
            color: #666;
            margin-bottom: 30px;
        }}
        
        .line-login-btn {{
            display: inline-flex;
            align-items: center;
            gap: 10px;
            padding: 12px 30px;
            background: #00B900;
            color: white;
            border: none;
            border-radius: 8px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            text-decoration: none;
            transition: transform 0.2s;
        }}
        
        .line-login-btn:hover {{
            transform: scale(1.05);
        }}
        
        /* Add article form */
        .add-article-form {{
            display: flex;
            gap: 10px;
            margin-bottom: 30px;
        }}
        
        .url-input {{
            flex: 1;
            padding: 12px;
            border: 2px solid #e5e7eb;
            border-radius: 8px;
            font-size: 14px;
        }}
        
        .add-btn {{
            padding: 12px 30px;
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: white;
            border: none;
            border-radius: 8px;
            font-weight: 600;
            cursor: pointer;
        }}
        
        /* Mobile responsive */
        @media (max-width: 768px) {{
            .container {{
                padding: 10px;
            }}
            
            .header {{
                flex-direction: column;
                gap: 15px;
                text-align: center;
            }}
            
            .articles-grid {{
                grid-template-columns: 1fr;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="logo">📚 Article Intelligence Hub</div>
            <div class="user-section">
                {user_section_html}
            </div>
        </div>
        
        <div class="main-content">
            {main_content_html}
        </div>
    </div>
    
    <script>
        const userData = {json.dumps(user) if user else 'null'};
        
        async function loadArticles() {{
            if (!userData) return;
            
            try {{
                const response = await fetch('/api/articles');
                const data = await response.json();
                displayArticles(data.articles);
            }} catch (error) {{
                console.error('Error loading articles:', error);
            }}
        }}
        
        function displayArticles(articles) {{
            const container = document.getElementById('articlesContainer');
            if (!container) return;
            
            if (articles.length === 0) {{
                container.innerHTML = '<p style="text-align: center; color: #999;">No articles yet. Add your first article above!</p>';
                return;
            }}
            
            const grid = document.createElement('div');
            grid.className = 'articles-grid';
            
            articles.forEach(article => {{
                const card = document.createElement('div');
                card.className = 'article-card';
                card.innerHTML = `
                    <h3>${{article.title || 'Untitled'}}</h3>
                    <p style="color: #666; margin: 10px 0;">${{article.category || 'General'}}</p>
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <span style="background: #f3f4f6; padding: 4px 12px; border-radius: 20px; font-size: 14px;">
                            ${{article.stage || 'inbox'}}
                        </span>
                        <a href="${{article.url}}" target="_blank" style="color: #667eea; text-decoration: none;">
                            Open →
                        </a>
                    </div>
                `;
                grid.appendChild(card);
            }});
            
            container.innerHTML = '<h2 style="margin-bottom: 20px;">Your Articles</h2>';
            container.appendChild(grid);
        }}
        
        async function addArticle() {{
            const urlInput = document.getElementById('urlInput');
            const url = urlInput.value.trim();
            
            if (!url) {{
                alert('Please enter a URL');
                return;
            }}
            
            try {{
                const response = await fetch('/api/articles', {{
                    method: 'POST',
                    headers: {{ 'Content-Type': 'application/json' }},
                    body: JSON.stringify({{ url: url }})
                }});
                
                if (response.ok) {{
                    urlInput.value = '';
                    loadArticles();
                    alert('Article added successfully!');
                }}
            }} catch (error) {{
                alert('Failed to add article');
            }}
        }}
        
        async function logout() {{
            await fetch('/api/logout', {{ method: 'POST' }});
            window.location.href = '/';
        }}
        
        // Load articles on page load
        if (userData) {{
            loadArticles();
        }}
    </script>
</body>
</html>'''
        
        self.send_response(200)
        self.send_header('Content-Type', 'text/html')
        self.end_headers()
        self.wfile.write(html.encode())
    
    def serve_articles(self):
        """Serve user's articles"""
        # Get user from session
        cookie = self.headers.get('Cookie', '')
        session_token = None
        user = None
        
        if 'session=' in cookie:
            session_token = cookie.split('session=')[1].split(';')[0]
            user = get_user_by_session(session_token)
        
        if not user:
            self.send_response(401)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'error': 'Not authenticated'}).encode())
            return
        
        articles = get_user_articles(user['user_id'])
        
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps({'articles': articles}).encode())
    
    def handle_add_article(self, post_data):
        """Add article for authenticated user"""
        # Get user from session
        cookie = self.headers.get('Cookie', '')
        session_token = None
        user = None
        
        if 'session=' in cookie:
            session_token = cookie.split('session=')[1].split(';')[0]
            user = get_user_by_session(session_token)
        
        if not user:
            self.send_error(401, 'Not authenticated')
            return
        
        try:
            data = json.loads(post_data)
            url = data.get('url', '').strip()
            
            if not url:
                self.send_error(400, 'URL required')
                return
            
            # Extract metadata
            title = extract_title_from_url(url)
            category = detect_category(url)
            
            # Save article for user
            save_article(user['user_id'], url, title, category)
            
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'success': True}).encode())
            
        except Exception as e:
            logging.error(f'Error adding article: {e}')
            self.send_error(500, str(e))
    
    def handle_update_article(self, post_data):
        """Update article stage for authenticated user"""
        # Get user from session
        cookie = self.headers.get('Cookie', '')
        session_token = None
        user = None
        
        if 'session=' in cookie:
            session_token = cookie.split('session=')[1].split(';')[0]
            user = get_user_by_session(session_token)
        
        if not user:
            self.send_error(401, 'Not authenticated')
            return
        
        try:
            data = json.loads(post_data)
            article_id = data.get('id')
            stage = data.get('stage')
            
            if not article_id:
                self.send_error(400, 'Article ID required')
                return
            
            # Update article in database
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE articles 
                SET stage = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ? AND user_id = ?
            ''', (stage, article_id, user['user_id']))
            conn.commit()
            conn.close()
            
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'success': True}).encode())
            
        except Exception as e:
            logging.error(f'Error updating article: {e}')
            self.send_error(500, str(e))
    
    def handle_logout(self):
        """Handle logout"""
        self.send_response(200)
        self.send_header('Set-Cookie', 'session=; Max-Age=0; HttpOnly; Secure; SameSite=Lax')
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps({'success': True}).encode())
    
    def serve_manifest(self):
        """Serve PWA manifest"""
        manifest = {
            "name": "Article Intelligence Hub",
            "short_name": "ArticleHub",
            "description": "Manage your reading list",
            "start_url": "/",
            "display": "standalone",
            "background_color": "#667eea",
            "theme_color": "#667eea",
            "icons": [
                {"src": "/icon-192x192.png", "sizes": "192x192", "type": "image/png"},
                {"src": "/icon-512x512.png", "sizes": "512x512", "type": "image/png"}
            ]
        }
        
        self.send_response(200)
        self.send_header('Content-Type', 'application/manifest+json')
        self.end_headers()
        self.wfile.write(json.dumps(manifest).encode())
    
    def serve_service_worker(self):
        """Serve service worker"""
        sw = '''
self.addEventListener('install', e => self.skipWaiting());
self.addEventListener('activate', e => self.clients.claim());
self.addEventListener('fetch', e => {
  if (e.request.url.includes('/api/')) {
    e.respondWith(fetch(e.request));
  } else {
    e.respondWith(
      caches.match(e.request).then(r => r || fetch(e.request))
    );
  }
});'''
        
        self.send_response(200)
        self.send_header('Content-Type', 'application/javascript')
        self.end_headers()
        self.wfile.write(sw.encode())
    
    def serve_icon(self):
        """Serve app icon"""
        svg = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512">
  <rect width="512" height="512" rx="80" fill="#667eea"/>
  <text x="256" y="320" font-family="Arial" font-size="240" text-anchor="middle" fill="white">📚</text>
</svg>'''
        
        self.send_response(200)
        self.send_header('Content-Type', 'image/svg+xml')
        self.end_headers()
        self.wfile.write(svg.encode())
    
    def handle_line_webhook(self, post_data):
        """Handle LINE webhook events"""
        # Webhook handler code here (similar to previous implementation)
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps({'success': True}).encode())
    
    def serve_user_info(self):
        """Get current user info"""
        cookie = self.headers.get('Cookie', '')
        session_token = None
        user = None
        
        if 'session=' in cookie:
            session_token = cookie.split('session=')[1].split(';')[0]
            user = get_user_by_session(session_token)
        
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps({'user': user}).encode())

# Database functions
def initialize_database():
    """Initialize database with user tables"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id TEXT PRIMARY KEY,
            display_name TEXT,
            picture_url TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Sessions table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sessions (
            session_token TEXT PRIMARY KEY,
            user_id TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (user_id)
        )
    ''')
    
    # Articles table with user association
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS articles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT,
            url TEXT NOT NULL,
            url_hash TEXT,
            title TEXT,
            category TEXT,
            stage TEXT DEFAULT 'inbox',
            priority TEXT DEFAULT 'medium',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (user_id),
            UNIQUE(user_id, url_hash)
        )
    ''')
    
    conn.commit()
    conn.close()
    logging.info("Database initialized")

def save_user(user_id, display_name, picture_url):
    """Save or update user"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT OR REPLACE INTO users (user_id, display_name, picture_url, updated_at)
        VALUES (?, ?, ?, CURRENT_TIMESTAMP)
    ''', (user_id, display_name, picture_url))
    
    conn.commit()
    conn.close()

def save_session(session_token, user_id):
    """Save user session"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    expires_at = datetime.now() + timedelta(days=30)
    
    cursor.execute('''
        INSERT INTO sessions (session_token, user_id, expires_at)
        VALUES (?, ?, ?)
    ''', (session_token, user_id, expires_at))
    
    conn.commit()
    conn.close()

def get_user_by_session(session_token):
    """Get user by session token"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT u.* FROM users u
        JOIN sessions s ON u.user_id = s.user_id
        WHERE s.session_token = ? AND s.expires_at > CURRENT_TIMESTAMP
    ''', (session_token,))
    
    row = cursor.fetchone()
    conn.close()
    
    return dict(row) if row else None

def save_article(user_id, url, title, category):
    """Save article for user"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    url_hash = hashlib.md5(url.encode()).hexdigest()
    
    cursor.execute('''
        INSERT OR IGNORE INTO articles (user_id, url, url_hash, title, category)
        VALUES (?, ?, ?, ?, ?)
    ''', (user_id, url, url_hash, title, category))
    
    conn.commit()
    conn.close()

def get_user_articles(user_id):
    """Get articles for user"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT * FROM articles
        WHERE user_id = ?
        ORDER BY created_at DESC
        LIMIT 50
    ''', (user_id,))
    
    articles = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    return articles

def extract_title_from_url(url):
    """Extract title from URL"""
    title = re.sub(r'^https?://(www\.)?', '', url)
    title = title.split('?')[0].split('#')[0]
    parts = title.split('/')
    if len(parts) > 1 and parts[-1]:
        title = parts[-1].replace('-', ' ').replace('_', ' ').title()
    else:
        title = parts[0].split('.')[0].title()
    return title[:100]

def detect_category(url):
    """Detect category from URL"""
    url_lower = url.lower()
    if any(x in url_lower for x in ['github.com', 'gitlab.com']):
        return 'Development'
    elif any(x in url_lower for x in ['youtube.com', 'vimeo.com']):
        return 'Video'
    elif any(x in url_lower for x in ['medium.com', 'dev.to']):
        return 'Articles'
    else:
        return 'General'

def main():
    """Main entry point"""
    print(f"\n{'='*60}")
    print("🚀 Article Intelligence Hub - Production Server")
    print(f"{'='*60}")
    print(f"Port: {PORT}")
    print(f"Base URL: {BASE_URL}")
    print(f"Database: {DB_PATH}")
    print(f"LIFF ID: {LIFF_ID}")
    print(f"{'='*60}\n")
    
    # Initialize database
    initialize_database()
    
    # Start server
    server = HTTPServer(('0.0.0.0', PORT), RequestHandler)
    print(f"Server running on http://0.0.0.0:{PORT}")
    server.serve_forever()

if __name__ == '__main__':
    main()