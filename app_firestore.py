#!/usr/bin/env python3
"""
LINE Article Intelligence Hub - Firestore Version
A comprehensive article management system with persistent Firestore storage
"""

import os
import sys
import json
import time
import hashlib
import traceback
import logging
import re
from datetime import datetime, timedelta
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs, unquote
from typing import Dict, List, Optional, Tuple, Any
import base64
import hmac
import secrets
import threading

# Import Firestore
from google.cloud import firestore
from google.api_core import exceptions

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Initialize Firestore client
db = firestore.Client(project='secondbrain-app-20250612')

# Configuration
PORT = int(os.environ.get('PORT', 8080))
HOST = '0.0.0.0'

# LINE Configuration from environment
LINE_CHANNEL_ACCESS_TOKEN = os.environ.get('LINE_CHANNEL_ACCESS_TOKEN', '').strip()
LINE_CHANNEL_SECRET = os.environ.get('LINE_CHANNEL_SECRET', '').strip()
LINE_LOGIN_CHANNEL_ID = os.environ.get('LINE_LOGIN_CHANNEL_ID', '2007870100')
LINE_LOGIN_CHANNEL_SECRET = os.environ.get('LINE_LOGIN_CHANNEL_SECRET', '')
LINE_LOGIN_REDIRECT_URI = os.environ.get('LINE_LOGIN_REDIRECT_URI', '')

# Load from .env.production if exists
if os.path.exists('.env.production'):
    logger.info("Loading environment from .env.production")
    with open('.env.production', 'r') as f:
        for line in f:
            if '=' in line and not line.strip().startswith('#'):
                key, value = line.strip().split('=', 1)
                if key == 'LINE_CHANNEL_ACCESS_TOKEN':
                    LINE_CHANNEL_ACCESS_TOKEN = value.strip()
                elif key == 'LINE_CHANNEL_SECRET':
                    LINE_CHANNEL_SECRET = value.strip()
                elif key == 'LINE_LOGIN_CHANNEL_ID':
                    LINE_LOGIN_CHANNEL_ID = value.strip()
                elif key == 'LINE_LOGIN_CHANNEL_SECRET':
                    LINE_LOGIN_CHANNEL_SECRET = value.strip()

# Validate configuration
if not LINE_CHANNEL_ACCESS_TOKEN or LINE_CHANNEL_ACCESS_TOKEN == 'your_channel_access_token_here':
    logger.error("LINE_CHANNEL_ACCESS_TOKEN not configured properly")
if not LINE_CHANNEL_SECRET or LINE_CHANNEL_SECRET == 'your_channel_secret_here':
    logger.error("LINE_CHANNEL_SECRET not configured properly")

logger.info(f"LINE_CHANNEL_ACCESS_TOKEN configured: {bool(LINE_CHANNEL_ACCESS_TOKEN and len(LINE_CHANNEL_ACCESS_TOKEN) > 20)}")
logger.info(f"LINE_CHANNEL_SECRET configured: {bool(LINE_CHANNEL_SECRET and len(LINE_CHANNEL_SECRET) > 20)}")

# LIFF URL for dashboard access
LIFF_URL = "https://liff.line.me/2007552096-GxP76rNd"

# URL Extraction Functions
def extract_urls(text: str) -> List[str]:
    """Extract all URLs from text"""
    urls = []
    
    # Pattern 1: Standard URLs with protocol
    pattern1 = r'https?://(?:[-\w.])+(?::\d+)?(?:[/\w\-._~:?#\[\]@!$&\'()*+,;=%.]*)?'
    urls.extend(re.findall(pattern1, text, re.IGNORECASE))
    
    # Pattern 2: URLs starting with www (add https://)
    pattern2 = r'(?:^|[\s])(?:www\.)(?:[-\w.])+(?::\d+)?(?:[/\w\-._~:?#\[\]@!$&\'()*+,;=%.]*)?'
    www_urls = re.findall(pattern2, text, re.IGNORECASE)
    for url in www_urls:
        clean_url = url.strip()
        if clean_url:
            urls.append(f"https://{clean_url}")
    
    # Pattern 3: Common short URL services
    short_patterns = [
        r'(?:bit\.ly|t\.co|tinyurl\.com|goo\.gl|ow\.ly|buff\.ly)/[\w\-]+',
        r'(?:youtu\.be)/[\w\-]+',
        r'(?:fb\.me|m\.me)/[\w\-]+'
    ]
    for pattern in short_patterns:
        short_urls = re.findall(pattern, text, re.IGNORECASE)
        for url in short_urls:
            if not url.startswith('http'):
                urls.append(f"https://{url}")
            else:
                urls.append(url)
    
    # Pattern 4: Domain names with common TLDs
    domain_pattern = r'(?:^|[\s])([a-zA-Z0-9](?:[a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?\.)+(?:com|org|net|edu|gov|io|co|uk|jp|cn|de|fr|au|us|ru|ch|it|nl|se|no|es|mil|info|biz|name|ly|tv|me)(?:[/\w\-._~:?#\[\]@!$&\'()*+,;=%.]*)?'
    domain_urls = re.findall(domain_pattern, text, re.IGNORECASE)
    for url in domain_urls:
        clean_url = url.strip()
        if clean_url and not any(clean_url in u for u in urls):
            urls.append(f"https://{clean_url}")
    
    # Clean and deduplicate URLs
    cleaned_urls = []
    seen = set()
    for url in urls:
        # Remove trailing punctuation
        url = re.sub(r'[.,;!?]+$', '', url)
        # Normalize
        if url and url not in seen:
            seen.add(url)
            cleaned_urls.append(url)
    
    return cleaned_urls

def is_url(text: str) -> bool:
    """Check if text is primarily a URL"""
    text = text.strip()
    # Check if starts with protocol
    if text.startswith(('http://', 'https://')):
        return True
    # Check if starts with www
    if text.startswith('www.'):
        return True
    # Check for domain pattern
    domain_pattern = r'^([a-zA-Z0-9](?:[a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}(?:[/\w\-._~:?#\[\]@!$&\'()*+,;=%.]*)?$'
    return bool(re.match(domain_pattern, text, re.IGNORECASE))

# Firestore Database Functions
class FirestoreDB:
    def __init__(self):
        self.db = db
        self.init_collections()
    
    def init_collections(self):
        """Initialize Firestore collections"""
        try:
            # Collections are created automatically when first document is added
            logger.info("Firestore collections ready")
        except Exception as e:
            logger.error(f"Error initializing Firestore: {e}")
    
    def save_user(self, user_id: str, display_name: str = None, picture_url: str = None, status_message: str = None) -> bool:
        """Save or update user information"""
        try:
            user_ref = self.db.collection('users').document(user_id)
            user_data = {
                'user_id': user_id,
                'updated_at': firestore.SERVER_TIMESTAMP
            }
            
            if display_name:
                user_data['display_name'] = display_name
            if picture_url:
                user_data['picture_url'] = picture_url
            if status_message:
                user_data['status_message'] = status_message
            
            # Check if user exists
            doc = user_ref.get()
            if doc.exists:
                # Update existing user
                user_data['message_count'] = firestore.Increment(1)
                user_ref.update(user_data)
            else:
                # Create new user
                user_data['created_at'] = firestore.SERVER_TIMESTAMP
                user_data['message_count'] = 1
                user_ref.set(user_data)
            
            logger.info(f"User saved: {user_id}")
            return True
        except Exception as e:
            logger.error(f"Error saving user: {e}")
            return False
    
    def save_article(self, url: str, title: str = None, user_id: str = None, 
                    category: str = None, priority: str = 'medium', 
                    stage: str = 'inbox', tags: str = None) -> str:
        """Save article to Firestore"""
        try:
            # Generate URL hash for deduplication
            url_hash = hashlib.md5(url.encode()).hexdigest()
            
            # Check if article already exists
            articles_ref = self.db.collection('articles')
            existing = articles_ref.where('url_hash', '==', url_hash).limit(1).get()
            
            if existing:
                article_id = existing[0].id
                logger.info(f"Article already exists: {article_id}")
                return article_id
            
            # Create new article
            article_data = {
                'url': url,
                'url_hash': url_hash,
                'title': title or 'Untitled',
                'category': category or 'uncategorized',
                'priority': priority,
                'stage': stage,
                'tags': tags or '',
                'user_id': user_id,
                'source': 'line',
                'created_at': firestore.SERVER_TIMESTAMP,
                'updated_at': firestore.SERVER_TIMESTAMP,
                'is_archived': False,
                'view_count': 0,
                'study_count': 0,
                'total_study_time': 0,
                'is_favorite': False,
                'completion_percentage': 0
            }
            
            # Add article
            doc_ref = articles_ref.add(article_data)
            article_id = doc_ref[1].id
            
            logger.info(f"Article saved: {article_id} - {url}")
            return article_id
            
        except Exception as e:
            logger.error(f"Error saving article: {e}")
            return None
    
    def get_article(self, article_id: str) -> Optional[Dict]:
        """Get article by ID"""
        try:
            doc = self.db.collection('articles').document(article_id).get()
            if doc.exists:
                return doc.to_dict()
            return None
        except Exception as e:
            logger.error(f"Error getting article: {e}")
            return None
    
    def get_articles_by_stage(self, stage: str) -> List[Dict]:
        """Get articles by stage"""
        try:
            articles = []
            docs = self.db.collection('articles').where('stage', '==', stage).stream()
            for doc in docs:
                article = doc.to_dict()
                article['id'] = doc.id
                articles.append(article)
            return articles
        except Exception as e:
            logger.error(f"Error getting articles by stage: {e}")
            return []
    
    def update_article_stage(self, article_id: str, stage: str) -> bool:
        """Update article stage"""
        try:
            self.db.collection('articles').document(article_id).update({
                'stage': stage,
                'updated_at': firestore.SERVER_TIMESTAMP
            })
            logger.info(f"Article {article_id} stage updated to {stage}")
            return True
        except Exception as e:
            logger.error(f"Error updating article stage: {e}")
            return False
    
    def get_user_stats(self, user_id: str) -> Dict:
        """Get user statistics"""
        try:
            # Get user's articles
            articles = self.db.collection('articles').where('user_id', '==', user_id).stream()
            
            stats = {
                'total_articles': 0,
                'by_stage': {'inbox': 0, 'reading': 0, 'reviewing': 0, 'completed': 0},
                'by_priority': {'high': 0, 'medium': 0, 'low': 0},
                'total_study_time': 0,
                'favorites': 0,
                'archived': 0
            }
            
            for doc in articles:
                article = doc.to_dict()
                stats['total_articles'] += 1
                
                stage = article.get('stage', 'inbox')
                if stage in stats['by_stage']:
                    stats['by_stage'][stage] += 1
                
                priority = article.get('priority', 'medium')
                if priority in stats['by_priority']:
                    stats['by_priority'][priority] += 1
                
                stats['total_study_time'] += article.get('total_study_time', 0)
                
                if article.get('is_favorite'):
                    stats['favorites'] += 1
                if article.get('is_archived'):
                    stats['archived'] += 1
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting user stats: {e}")
            return {}
    
    def create_session(self, user_id: str, access_token: str) -> str:
        """Create login session"""
        try:
            session_id = secrets.token_urlsafe(32)
            session_data = {
                'session_id': session_id,
                'user_id': user_id,
                'access_token': access_token,
                'created_at': firestore.SERVER_TIMESTAMP,
                'expires_at': datetime.now() + timedelta(days=30)
            }
            
            self.db.collection('sessions').document(session_id).set(session_data)
            logger.info(f"Session created for user {user_id}")
            return session_id
            
        except Exception as e:
            logger.error(f"Error creating session: {e}")
            return None
    
    def get_session(self, session_id: str) -> Optional[Dict]:
        """Get session by ID"""
        try:
            doc = self.db.collection('sessions').document(session_id).get()
            if doc.exists:
                session = doc.to_dict()
                # Check if expired
                if 'expires_at' in session and session['expires_at'] < datetime.now():
                    logger.info(f"Session expired: {session_id}")
                    return None
                return session
            return None
        except Exception as e:
            logger.error(f"Error getting session: {e}")
            return None

# Initialize database
database = FirestoreDB()

# LINE API Functions
def verify_line_signature(body: bytes, signature: str) -> bool:
    """Verify LINE webhook signature"""
    if not LINE_CHANNEL_SECRET:
        logger.warning("LINE_CHANNEL_SECRET not configured, skipping signature verification")
        return True
    
    hash = hmac.new(
        LINE_CHANNEL_SECRET.encode('utf-8'),
        body,
        hashlib.sha256
    ).digest()
    expected_signature = base64.b64encode(hash).decode('utf-8')
    return signature == expected_signature

def send_line_reply(reply_token: str, messages: List[Dict]) -> bool:
    """Send reply message via LINE API"""
    import urllib.request
    import urllib.error
    
    url = 'https://api.line.me/v2/bot/message/reply'
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {LINE_CHANNEL_ACCESS_TOKEN}'
    }
    
    data = {
        'replyToken': reply_token,
        'messages': messages
    }
    
    try:
        req = urllib.request.Request(
            url,
            data=json.dumps(data).encode('utf-8'),
            headers=headers,
            method='POST'
        )
        
        with urllib.request.urlopen(req) as response:
            result = response.read().decode('utf-8')
            logger.info(f"LINE reply sent successfully: {result}")
            return True
            
    except urllib.error.HTTPError as e:
        error_body = e.read().decode('utf-8')
        logger.error(f"Failed to send LINE reply: {e.code} - {error_body}")
        return False
    except Exception as e:
        logger.error(f"Error sending LINE reply: {e}")
        return False

def get_line_profile(user_id: str) -> Optional[Dict]:
    """Get LINE user profile"""
    import urllib.request
    import urllib.error
    
    url = f'https://api.line.me/v2/bot/profile/{user_id}'
    headers = {
        'Authorization': f'Bearer {LINE_CHANNEL_ACCESS_TOKEN}'
    }
    
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req) as response:
            return json.loads(response.read().decode('utf-8'))
    except Exception as e:
        logger.error(f"Error getting LINE profile: {e}")
        return None

def create_flex_message(article_id: str, url: str, title: str, stage: str) -> Dict:
    """Create a Flex Message for article saved confirmation"""
    return {
        "type": "flex",
        "altText": f"Article saved: {title}",
        "contents": {
            "type": "bubble",
            "header": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {
                        "type": "text",
                        "text": "📚 Article Saved!",
                        "weight": "bold",
                        "size": "lg",
                        "color": "#1DB446"
                    }
                ]
            },
            "body": {
                "type": "box",
                "layout": "vertical",
                "spacing": "md",
                "contents": [
                    {
                        "type": "text",
                        "text": title,
                        "weight": "bold",
                        "size": "md",
                        "wrap": True
                    },
                    {
                        "type": "text",
                        "text": url,
                        "size": "xs",
                        "color": "#888888",
                        "wrap": True,
                        "maxLines": 2
                    },
                    {
                        "type": "separator",
                        "margin": "md"
                    },
                    {
                        "type": "box",
                        "layout": "horizontal",
                        "spacing": "sm",
                        "contents": [
                            {
                                "type": "text",
                                "text": "Stage:",
                                "size": "sm",
                                "color": "#555555",
                                "flex": 0
                            },
                            {
                                "type": "text",
                                "text": stage.title(),
                                "size": "sm",
                                "weight": "bold",
                                "color": "#1DB446"
                            }
                        ]
                    }
                ]
            },
            "footer": {
                "type": "box",
                "layout": "vertical",
                "spacing": "sm",
                "contents": [
                    {
                        "type": "button",
                        "action": {
                            "type": "uri",
                            "label": "📊 Open Dashboard",
                            "uri": LIFF_URL
                        },
                        "style": "primary",
                        "height": "sm"
                    },
                    {
                        "type": "button",
                        "action": {
                            "type": "uri",
                            "label": "🔗 View Article",
                            "uri": url
                        },
                        "style": "link",
                        "height": "sm"
                    }
                ]
            }
        }
    }

# HTTP Request Handler
class ArticleHubHandler(BaseHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
    
    def do_GET(self):
        """Handle GET requests"""
        parsed_path = urlparse(self.path)
        path = parsed_path.path
        
        # CORS headers for all responses
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        
        if path == '/':
            self.serve_home()
        elif path == '/health':
            self.serve_health()
        elif path == '/dashboard':
            self.serve_dashboard()
        elif path == '/kanban':
            self.serve_kanban()
        elif path == '/login':
            self.serve_login()
        elif path == '/callback':
            self.handle_login_callback(parsed_path)
        elif path == '/api/stats':
            self.serve_api_stats()
        elif path.startswith('/api/articles'):
            self.serve_api_articles(parsed_path)
        else:
            self.send_error(404, "Page not found")
    
    def do_POST(self):
        """Handle POST requests"""
        if self.path == '/callback':
            self.handle_webhook()
        elif self.path.startswith('/api/articles'):
            self.handle_api_articles_post()
        else:
            self.send_error(404, "Endpoint not found")
    
    def do_OPTIONS(self):
        """Handle OPTIONS requests for CORS"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    def serve_home(self):
        """Serve the home page"""
        html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Article Intelligence Hub</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 20px;
        }
        .container {
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            max-width: 800px;
            width: 100%;
            padding: 40px;
        }
        h1 {
            color: #333;
            font-size: 2.5em;
            margin-bottom: 10px;
            text-align: center;
        }
        .subtitle {
            color: #666;
            text-align: center;
            margin-bottom: 30px;
        }
        .features {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin: 30px 0;
        }
        .feature {
            padding: 20px;
            background: #f8f9fa;
            border-radius: 10px;
            text-align: center;
        }
        .feature-icon {
            font-size: 2em;
            margin-bottom: 10px;
        }
        .buttons {
            display: flex;
            gap: 15px;
            justify-content: center;
            margin-top: 30px;
        }
        .btn {
            padding: 12px 30px;
            border-radius: 25px;
            text-decoration: none;
            font-weight: 600;
            transition: transform 0.2s;
            display: inline-block;
        }
        .btn:hover {
            transform: translateY(-2px);
        }
        .btn-primary {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }
        .btn-secondary {
            background: #f8f9fa;
            color: #333;
            border: 2px solid #ddd;
        }
        .status {
            text-align: center;
            margin-top: 30px;
            padding: 20px;
            background: #e8f5e9;
            border-radius: 10px;
            color: #2e7d32;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>📚 Article Intelligence Hub</h1>
        <p class="subtitle">Your Personal Knowledge Management System</p>
        
        <div class="features">
            <div class="feature">
                <div class="feature-icon">🤖</div>
                <h3>LINE Bot Integration</h3>
                <p>Save articles directly from LINE</p>
            </div>
            <div class="feature">
                <div class="feature-icon">📊</div>
                <h3>Smart Dashboard</h3>
                <p>Track your reading progress</p>
            </div>
            <div class="feature">
                <div class="feature-icon">📋</div>
                <h3>Kanban Board</h3>
                <p>Organize articles by stage</p>
            </div>
            <div class="feature">
                <div class="feature-icon">☁️</div>
                <h3>Cloud Storage</h3>
                <p>Powered by Google Firestore</p>
            </div>
        </div>
        
        <div class="buttons">
            <a href="/login" class="btn btn-primary">🔐 Login with LINE</a>
            <a href="https://liff.line.me/2007552096-GxP76rNd" class="btn btn-secondary">📱 Open in LINE</a>
        </div>
        
        <div class="status">
            <strong>System Status:</strong> ✅ All services operational<br>
            <small>Firestore Database Connected</small>
        </div>
    </div>
</body>
</html>"""
        
        self.send_header('Content-Type', 'text/html')
        self.end_headers()
        self.wfile.write(html.encode())
    
    def serve_health(self):
        """Serve health check endpoint"""
        health_data = {
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'database': 'firestore',
            'services': {
                'line_bot': bool(LINE_CHANNEL_ACCESS_TOKEN),
                'line_login': bool(LINE_LOGIN_CHANNEL_ID),
                'firestore': True
            }
        }
        
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(health_data).encode())
    
    def serve_dashboard(self):
        """Serve the main dashboard"""
        html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Article Dashboard</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #f5f5f5;
        }
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            text-align: center;
        }
        .container {
            max-width: 1200px;
            margin: 20px auto;
            padding: 0 20px;
        }
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        .stat-card {
            background: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        .stat-value {
            font-size: 2em;
            font-weight: bold;
            color: #667eea;
        }
        .stat-label {
            color: #666;
            margin-top: 5px;
        }
        .articles-section {
            background: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        .stage-tabs {
            display: flex;
            gap: 10px;
            margin-bottom: 20px;
            border-bottom: 2px solid #eee;
        }
        .stage-tab {
            padding: 10px 20px;
            cursor: pointer;
            border-bottom: 3px solid transparent;
            transition: all 0.3s;
        }
        .stage-tab.active {
            border-bottom-color: #667eea;
            color: #667eea;
        }
        .articles-list {
            max-height: 500px;
            overflow-y: auto;
        }
        .article-item {
            padding: 15px;
            border-bottom: 1px solid #eee;
            cursor: pointer;
            transition: background 0.2s;
        }
        .article-item:hover {
            background: #f8f9fa;
        }
        .article-title {
            font-weight: 600;
            margin-bottom: 5px;
        }
        .article-url {
            color: #666;
            font-size: 0.9em;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }
        .loading {
            text-align: center;
            padding: 40px;
            color: #666;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>📊 Article Dashboard</h1>
        <p>Track your reading progress</p>
    </div>
    
    <div class="container">
        <div class="stats-grid" id="stats">
            <div class="loading">Loading statistics...</div>
        </div>
        
        <div class="articles-section">
            <div class="stage-tabs">
                <div class="stage-tab active" data-stage="inbox">📥 Inbox</div>
                <div class="stage-tab" data-stage="reading">📖 Reading</div>
                <div class="stage-tab" data-stage="reviewing">🔍 Reviewing</div>
                <div class="stage-tab" data-stage="completed">✅ Completed</div>
            </div>
            <div class="articles-list" id="articles">
                <div class="loading">Loading articles...</div>
            </div>
        </div>
    </div>
    
    <script>
        let currentStage = 'inbox';
        
        // Load statistics
        async function loadStats() {
            try {
                const response = await fetch('/api/stats');
                const stats = await response.json();
                
                document.getElementById('stats').innerHTML = `
                    <div class="stat-card">
                        <div class="stat-value">${stats.total_articles || 0}</div>
                        <div class="stat-label">Total Articles</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-value">${stats.by_stage?.inbox || 0}</div>
                        <div class="stat-label">In Inbox</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-value">${stats.by_stage?.reading || 0}</div>
                        <div class="stat-label">Currently Reading</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-value">${stats.by_stage?.completed || 0}</div>
                        <div class="stat-label">Completed</div>
                    </div>
                `;
            } catch (error) {
                console.error('Error loading stats:', error);
            }
        }
        
        // Load articles for a stage
        async function loadArticles(stage) {
            try {
                const response = await fetch(`/api/articles?stage=${stage}`);
                const articles = await response.json();
                
                const container = document.getElementById('articles');
                if (articles.length === 0) {
                    container.innerHTML = '<div class="loading">No articles in this stage</div>';
                    return;
                }
                
                container.innerHTML = articles.map(article => `
                    <div class="article-item" onclick="window.open('${article.url}', '_blank')">
                        <div class="article-title">${article.title}</div>
                        <div class="article-url">${article.url}</div>
                    </div>
                `).join('');
            } catch (error) {
                console.error('Error loading articles:', error);
            }
        }
        
        // Tab switching
        document.querySelectorAll('.stage-tab').forEach(tab => {
            tab.addEventListener('click', () => {
                document.querySelectorAll('.stage-tab').forEach(t => t.classList.remove('active'));
                tab.classList.add('active');
                currentStage = tab.dataset.stage;
                loadArticles(currentStage);
            });
        });
        
        // Initial load
        loadStats();
        loadArticles(currentStage);
        
        // Refresh every 30 seconds
        setInterval(() => {
            loadStats();
            loadArticles(currentStage);
        }, 30000);
    </script>
</body>
</html>"""
        
        self.send_header('Content-Type', 'text/html')
        self.end_headers()
        self.wfile.write(html.encode())
    
    def serve_kanban(self):
        """Serve the Kanban board interface"""
        html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Article Kanban Board</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        .header {
            text-align: center;
            color: white;
            margin-bottom: 30px;
        }
        .kanban-board {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            max-width: 1400px;
            margin: 0 auto;
        }
        .kanban-column {
            background: white;
            border-radius: 10px;
            padding: 15px;
            min-height: 500px;
        }
        .column-header {
            font-weight: bold;
            padding: 10px;
            margin-bottom: 15px;
            border-radius: 5px;
            text-align: center;
        }
        .column-header.inbox { background: #e3f2fd; color: #1976d2; }
        .column-header.reading { background: #fff3e0; color: #f57c00; }
        .column-header.reviewing { background: #f3e5f5; color: #7b1fa2; }
        .column-header.completed { background: #e8f5e9; color: #388e3c; }
        .article-card {
            background: #f5f5f5;
            padding: 12px;
            margin-bottom: 10px;
            border-radius: 5px;
            cursor: move;
            transition: transform 0.2s;
        }
        .article-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        }
        .article-card.dragging {
            opacity: 0.5;
        }
        .article-title {
            font-weight: 600;
            margin-bottom: 5px;
            color: #333;
        }
        .article-url {
            font-size: 0.85em;
            color: #666;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }
        .article-meta {
            display: flex;
            justify-content: space-between;
            margin-top: 8px;
            font-size: 0.8em;
            color: #999;
        }
        .drop-zone {
            min-height: 100px;
            border: 2px dashed transparent;
            transition: all 0.3s;
        }
        .drop-zone.drag-over {
            border-color: #667eea;
            background: rgba(102, 126, 234, 0.1);
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>📋 Article Kanban Board</h1>
        <p>Organize your reading workflow</p>
    </div>
    
    <div class="kanban-board">
        <div class="kanban-column">
            <div class="column-header inbox">📥 Inbox</div>
            <div class="drop-zone" data-stage="inbox" id="inbox-articles"></div>
        </div>
        
        <div class="kanban-column">
            <div class="column-header reading">📖 Reading</div>
            <div class="drop-zone" data-stage="reading" id="reading-articles"></div>
        </div>
        
        <div class="kanban-column">
            <div class="column-header reviewing">🔍 Reviewing</div>
            <div class="drop-zone" data-stage="reviewing" id="reviewing-articles"></div>
        </div>
        
        <div class="kanban-column">
            <div class="column-header completed">✅ Completed</div>
            <div class="drop-zone" data-stage="completed" id="completed-articles"></div>
        </div>
    </div>
    
    <script>
        let draggedElement = null;
        
        // Load articles for all stages
        async function loadKanban() {
            const stages = ['inbox', 'reading', 'reviewing', 'completed'];
            
            for (const stage of stages) {
                try {
                    const response = await fetch(`/api/articles?stage=${stage}`);
                    const articles = await response.json();
                    
                    const container = document.getElementById(`${stage}-articles`);
                    container.innerHTML = articles.map(article => `
                        <div class="article-card" draggable="true" data-id="${article.id}" data-stage="${stage}">
                            <div class="article-title">${article.title}</div>
                            <div class="article-url">${article.url}</div>
                            <div class="article-meta">
                                <span>${article.priority || 'medium'}</span>
                                <span>${new Date(article.created_at).toLocaleDateString()}</span>
                            </div>
                        </div>
                    `).join('');
                } catch (error) {
                    console.error(`Error loading ${stage} articles:`, error);
                }
            }
            
            // Re-attach drag event listeners
            attachDragListeners();
        }
        
        // Attach drag and drop event listeners
        function attachDragListeners() {
            // Drag start
            document.querySelectorAll('.article-card').forEach(card => {
                card.addEventListener('dragstart', (e) => {
                    draggedElement = e.target;
                    e.target.classList.add('dragging');
                });
                
                card.addEventListener('dragend', (e) => {
                    e.target.classList.remove('dragging');
                });
            });
            
            // Drop zones
            document.querySelectorAll('.drop-zone').forEach(zone => {
                zone.addEventListener('dragover', (e) => {
                    e.preventDefault();
                    zone.classList.add('drag-over');
                });
                
                zone.addEventListener('dragleave', () => {
                    zone.classList.remove('drag-over');
                });
                
                zone.addEventListener('drop', async (e) => {
                    e.preventDefault();
                    zone.classList.remove('drag-over');
                    
                    if (draggedElement) {
                        const articleId = draggedElement.dataset.id;
                        const newStage = zone.dataset.stage;
                        const oldStage = draggedElement.dataset.stage;
                        
                        if (oldStage !== newStage) {
                            // Update stage in backend
                            try {
                                const response = await fetch(`/api/articles/${articleId}/stage`, {
                                    method: 'POST',
                                    headers: { 'Content-Type': 'application/json' },
                                    body: JSON.stringify({ stage: newStage })
                                });
                                
                                if (response.ok) {
                                    // Move card to new column
                                    zone.appendChild(draggedElement);
                                    draggedElement.dataset.stage = newStage;
                                }
                            } catch (error) {
                                console.error('Error updating article stage:', error);
                            }
                        }
                    }
                    draggedElement = null;
                });
            });
        }
        
        // Initial load
        loadKanban();
        
        // Refresh every 30 seconds
        setInterval(loadKanban, 30000);
    </script>
</body>
</html>"""
        
        self.send_header('Content-Type', 'text/html')
        self.end_headers()
        self.wfile.write(html.encode())
    
    def serve_login(self):
        """Serve LINE Login page"""
        state = secrets.token_urlsafe(32)
        nonce = secrets.token_urlsafe(32)
        
        # Build LINE Login URL
        redirect_uri = f"https://{self.headers.get('Host')}/callback"
        login_url = (
            f"https://access.line.me/oauth2/v2.1/authorize?"
            f"response_type=code&"
            f"client_id={LINE_LOGIN_CHANNEL_ID}&"
            f"redirect_uri={redirect_uri}&"
            f"state={state}&"
            f"scope=profile%20openid&"
            f"nonce={nonce}"
        )
        
        # Redirect to LINE Login
        self.send_response(302)
        self.send_header('Location', login_url)
        self.end_headers()
    
    def handle_login_callback(self, parsed_path):
        """Handle LINE Login callback"""
        query = parse_qs(parsed_path.query)
        code = query.get('code', [None])[0]
        state = query.get('state', [None])[0]
        
        if not code:
            self.send_error(400, "Missing authorization code")
            return
        
        # Exchange code for access token
        import urllib.request
        import urllib.parse
        
        redirect_uri = f"https://{self.headers.get('Host')}/callback"
        token_url = "https://api.line.me/oauth2/v2.1/token"
        
        data = urllib.parse.urlencode({
            'grant_type': 'authorization_code',
            'code': code,
            'redirect_uri': redirect_uri,
            'client_id': LINE_LOGIN_CHANNEL_ID,
            'client_secret': LINE_LOGIN_CHANNEL_SECRET or ''
        }).encode()
        
        try:
            req = urllib.request.Request(token_url, data=data, method='POST')
            req.add_header('Content-Type', 'application/x-www-form-urlencoded')
            
            with urllib.request.urlopen(req) as response:
                token_data = json.loads(response.read().decode())
                access_token = token_data.get('access_token')
                
                if access_token:
                    # Get user profile
                    profile_url = "https://api.line.me/v2/profile"
                    profile_req = urllib.request.Request(profile_url)
                    profile_req.add_header('Authorization', f'Bearer {access_token}')
                    
                    with urllib.request.urlopen(profile_req) as profile_response:
                        profile = json.loads(profile_response.read().decode())
                        
                        # Save user to database
                        database.save_user(
                            user_id=profile['userId'],
                            display_name=profile.get('displayName'),
                            picture_url=profile.get('pictureUrl'),
                            status_message=profile.get('statusMessage')
                        )
                        
                        # Create session
                        session_id = database.create_session(profile['userId'], access_token)
                        
                        # Redirect to dashboard
                        self.send_response(302)
                        self.send_header('Set-Cookie', f'session_id={session_id}; Path=/; HttpOnly')
                        self.send_header('Location', '/dashboard')
                        self.end_headers()
                        return
                        
        except Exception as e:
            logger.error(f"Login error: {e}")
            self.send_error(500, "Login failed")
    
    def handle_webhook(self):
        """Handle LINE webhook events"""
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length)
        
        # Verify signature
        signature = self.headers.get('X-Line-Signature', '')
        if not verify_line_signature(body, signature):
            logger.warning("Invalid LINE signature")
            self.send_error(403, "Invalid signature")
            return
        
        # Parse webhook data
        try:
            webhook_data = json.loads(body.decode('utf-8'))
            logger.info(f"Webhook received: {json.dumps(webhook_data, indent=2)}")
            
            # Process events
            for event in webhook_data.get('events', []):
                self.process_webhook_event(event)
            
            # Send success response
            self.send_response(200)
            self.send_header('Content-Type', 'text/plain')
            self.end_headers()
            self.wfile.write(b'OK')
            
        except Exception as e:
            logger.error(f"Webhook processing error: {e}")
            self.send_error(500, "Internal server error")
    
    def process_webhook_event(self, event: Dict):
        """Process individual webhook event"""
        try:
            event_type = event.get('type')
            
            if event_type == 'message':
                message = event.get('message', {})
                message_type = message.get('type')
                
                if message_type == 'text':
                    text = message.get('text', '').strip()
                    user_id = event.get('source', {}).get('userId')
                    reply_token = event.get('replyToken')
                    
                    # Get user profile
                    profile = get_line_profile(user_id)
                    if profile:
                        database.save_user(
                            user_id=user_id,
                            display_name=profile.get('displayName'),
                            picture_url=profile.get('pictureUrl'),
                            status_message=profile.get('statusMessage')
                        )
                    
                    # Check if it's a URL or contains URLs
                    urls = extract_urls(text)
                    
                    if urls:
                        # Save each URL as an article
                        saved_count = 0
                        for url in urls:
                            article_id = database.save_article(
                                url=url,
                                title=f"Article from {url.split('/')[2] if '/' in url else url}",
                                user_id=user_id,
                                stage='inbox'
                            )
                            if article_id:
                                saved_count += 1
                        
                        # Send confirmation
                        if saved_count > 0:
                            if saved_count == 1:
                                # Single article - send flex message
                                flex_msg = create_flex_message(
                                    article_id=article_id,
                                    url=urls[0],
                                    title=f"Article from {urls[0].split('/')[2] if '/' in urls[0] else urls[0]}",
                                    stage='inbox'
                                )
                                send_line_reply(reply_token, [flex_msg])
                            else:
                                # Multiple articles - send summary
                                messages = [{
                                    "type": "text",
                                    "text": f"✅ Saved {saved_count} articles to your inbox!\n\n📊 View your dashboard:\n{LIFF_URL}"
                                }]
                                send_line_reply(reply_token, messages)
                    else:
                        # Not a URL - send help message
                        messages = [{
                            "type": "text",
                            "text": "📚 Send me a URL to save it to your reading list!\n\nExample:\nhttps://example.com/article\n\n📊 View dashboard:\n" + LIFF_URL
                        }]
                        send_line_reply(reply_token, messages)
                        
        except Exception as e:
            logger.error(f"Error processing webhook event: {e}")
    
    def serve_api_stats(self):
        """Serve API statistics endpoint"""
        # Get session or use default
        cookie = self.headers.get('Cookie', '')
        session_id = None
        user_id = None
        
        if 'session_id=' in cookie:
            session_id = cookie.split('session_id=')[1].split(';')[0]
            session = database.get_session(session_id)
            if session:
                user_id = session.get('user_id')
        
        # Get stats (global if no user)
        stats = database.get_user_stats(user_id) if user_id else {
            'total_articles': 0,
            'by_stage': {'inbox': 0, 'reading': 0, 'reviewing': 0, 'completed': 0},
            'by_priority': {'high': 0, 'medium': 0, 'low': 0}
        }
        
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(stats).encode())
    
    def serve_api_articles(self, parsed_path):
        """Serve API articles endpoint"""
        query = parse_qs(parsed_path.query)
        stage = query.get('stage', ['inbox'])[0]
        
        articles = database.get_articles_by_stage(stage)
        
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(articles).encode())
    
    def handle_api_articles_post(self):
        """Handle POST requests to articles API"""
        # Parse article ID from path
        path_parts = self.path.split('/')
        if len(path_parts) >= 4 and path_parts[3] == 'stage':
            article_id = path_parts[2]
            
            # Read request body
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length)
            data = json.loads(body.decode())
            
            # Update stage
            new_stage = data.get('stage')
            if new_stage and database.update_article_stage(article_id, new_stage):
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'success': True}).encode())
            else:
                self.send_error(400, "Failed to update stage")
        else:
            self.send_error(404, "Invalid endpoint")

def run_server():
    """Run the HTTP server"""
    server = HTTPServer((HOST, PORT), ArticleHubHandler)
    logger.info(f"🚀 Article Hub server running on http://{HOST}:{PORT}")
    logger.info(f"📱 LINE Bot webhook configured at: /callback")
    logger.info(f"🔥 Using Firestore for persistent storage")
    logger.info(f"☁️ Project: secondbrain-app-20250612")
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        logger.info("\n⏹️ Server stopped")
        server.shutdown()

if __name__ == "__main__":
    run_server()