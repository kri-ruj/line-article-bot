#!/usr/bin/env python3
"""
LINE Article Intelligence Hub - Firestore Version (Final Fixed)
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
from urllib.parse import urlparse, parse_qs, unquote, quote
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

# Initialize Firestore client with error handling
import os
# Clear any incorrect credential path
if 'GOOGLE_APPLICATION_CREDENTIALS' in os.environ:
    if not os.path.exists(os.environ['GOOGLE_APPLICATION_CREDENTIALS']):
        del os.environ['GOOGLE_APPLICATION_CREDENTIALS']
        logger.info("Cleared invalid GOOGLE_APPLICATION_CREDENTIALS path")

try:
    # Initialize with project ID
    db = firestore.Client(project='secondbrain-app-20250612')
    logger.info("Firestore client initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize Firestore: {e}")
    raise

# Configuration
PORT = int(os.environ.get('PORT', 8080))
HOST = '0.0.0.0'

# LINE Configuration from environment
LINE_CHANNEL_ACCESS_TOKEN = os.environ.get('LINE_CHANNEL_ACCESS_TOKEN', '').strip()
LINE_CHANNEL_SECRET = os.environ.get('LINE_CHANNEL_SECRET', '').strip()
LINE_LOGIN_CHANNEL_ID = os.environ.get('LINE_LOGIN_CHANNEL_ID', '2007870100')
LINE_LOGIN_CHANNEL_SECRET = os.environ.get('LINE_LOGIN_CHANNEL_SECRET', '')

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
LIFF_URL = "https://liff.line.me/2007870100-ao8GpgRQ"
LIFF_ID = "2007870100-ao8GpgRQ"

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

def categorize_url(url: str) -> Tuple[str, List[str]]:
    """Categorize URL and generate tags based on domain and path"""
    try:
        from urllib.parse import urlparse
        parsed = urlparse(url)
        domain = parsed.hostname.lower() if parsed.hostname else ''
        path = parsed.path.lower()
        
        # Category mapping
        category = 'general'
        tags = []
        
        # Tech sites
        if any(site in domain for site in ['github.com', 'stackoverflow.com', 'dev.to', 'medium.com', 'hackernews']):
            category = 'tech'
            tags.append('development')
            
        # News sites
        elif any(site in domain for site in ['bbc.com', 'cnn.com', 'reuters.com', 'bloomberg.com', 'nytimes.com']):
            category = 'news'
            tags.append('current-events')
            
        # Social media
        elif any(site in domain for site in ['twitter.com', 'x.com', 'facebook.com', 'linkedin.com', 'reddit.com']):
            category = 'social'
            tags.append('social-media')
            
        # Video
        elif any(site in domain for site in ['youtube.com', 'vimeo.com', 'twitch.tv']):
            category = 'video'
            tags.append('multimedia')
            
        # Documentation
        elif 'docs' in domain or '/docs' in path or '/documentation' in path:
            category = 'documentation'
            tags.append('reference')
            
        # Blog
        elif 'blog' in domain or '/blog' in path:
            category = 'blog'
            tags.append('article')
            
        # Shopping
        elif any(site in domain for site in ['amazon.com', 'ebay.com', 'shopify.com', 'aliexpress.com']):
            category = 'shopping'
            tags.append('e-commerce')
            
        # Add domain as tag
        if domain:
            clean_domain = domain.replace('www.', '').split('.')[0]
            tags.append(clean_domain)
            
        # Extract keywords from path
        path_parts = [p for p in path.split('/') if p and len(p) > 3]
        for part in path_parts[:3]:  # Limit to first 3 path segments
            if not any(char.isdigit() for char in part):  # Skip numeric IDs
                tags.append(part.replace('-', ' ').replace('_', ' '))
                
        # Remove duplicates and limit tags
        tags = list(set(tags))[:5]
        
        return category, tags
        
    except Exception as e:
        logger.error(f"Error categorizing URL: {e}")
        return 'general', []

# Firestore Database Functions
class FirestoreDB:
    def __init__(self):
        self.db = db
        self.init_collections()
    
    def init_collections(self):
        """Initialize Firestore collections"""
        try:
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
            
            # Check if article already exists for this user
            articles_ref = self.db.collection('articles')
            existing = articles_ref.where('url_hash', '==', url_hash).where('user_id', '==', user_id).limit(1).get()
            
            if existing:
                article_id = existing[0].id
                logger.info(f"Article already exists for user {user_id}: {article_id}")
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
    
    def get_articles_by_stage(self, stage: str) -> List[Dict]:
        """Get articles by stage"""
        try:
            articles = []
            if stage == 'all':
                # Return all articles for debugging
                docs = self.db.collection('articles').stream()
            else:
                # Return articles by specific stage
                docs = self.db.collection('articles').where('stage', '==', stage).stream()
            
            for doc in docs:
                article = doc.to_dict()
                article['id'] = doc.id
                articles.append(article)
                
            logger.info(f"Found {len(articles)} articles for stage '{stage}'")
            return articles
            
        except Exception as e:
            logger.error(f"Error getting articles by stage '{stage}': {e}")
            traceback.print_exc()
            return []
    
    def get_articles_by_stage_and_user(self, stage: str, user_id: str) -> List[Dict]:
        """Get articles by stage and user"""
        try:
            articles = []
            
            # Get all articles for the user first
            query = self.db.collection('articles')
            
            if user_id:
                query = query.where('user_id', '==', user_id)
            
            docs = query.stream()
            
            # Filter by stage in memory to avoid compound index issues
            for doc in docs:
                article = doc.to_dict()
                article['id'] = doc.id
                
                # Filter by stage if needed
                if stage == 'all' or article.get('stage') == stage:
                    articles.append(article)
            
            # Sort by created_at in memory
            articles.sort(key=lambda x: x.get('created_at', ''), reverse=True)
                
            logger.info(f"Found {len(articles)} articles for user '{user_id}' in stage '{stage}'")
            return articles
            
        except Exception as e:
            logger.error(f"Error getting articles for user '{user_id}' in stage '{stage}': {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def get_recent_articles(self, user_id: str = None, limit: int = 5) -> List[Dict]:
        """Get recent articles"""
        try:
            articles = []
            query = self.db.collection('articles')
            if user_id:
                query = query.where('user_id', '==', user_id)
            query = query.order_by('created_at', direction=firestore.Query.DESCENDING).limit(limit)
            
            docs = query.stream()
            for doc in docs:
                article = doc.to_dict()
                article['id'] = doc.id
                articles.append(article)
            return articles
        except Exception as e:
            logger.error(f"Error getting recent articles: {e}")
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
            articles_query = self.db.collection('articles')
            if user_id:
                articles_query = articles_query.where('user_id', '==', user_id)
            
            articles = articles_query.stream()
            
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
            
            logger.info(f"User stats for {user_id}: {stats}")
            return stats
            
        except Exception as e:
            logger.error(f"Error getting user stats for {user_id}: {e}")
            traceback.print_exc()
            # Return empty stats structure on error
            return {
                'total_articles': 0,
                'by_stage': {'inbox': 0, 'reading': 0, 'reviewing': 0, 'completed': 0},
                'by_priority': {'high': 0, 'medium': 0, 'low': 0},
                'total_study_time': 0,
                'favorites': 0,
                'archived': 0
            }
    
    # Team Mode Methods
    def create_team(self, name: str, owner_id: str, description: str = "") -> str:
        """Create a new team"""
        try:
            team_ref = self.db.collection('teams').document()
            team_data = {
                'name': name,
                'description': description,
                'owner_id': owner_id,
                'member_ids': [owner_id],
                'created_at': firestore.SERVER_TIMESTAMP,
                'updated_at': firestore.SERVER_TIMESTAMP,
                'invite_code': secrets.token_urlsafe(8)
            }
            team_ref.set(team_data)
            
            # Add team to user's teams (create user doc if doesn't exist)
            user_ref = self.db.collection('users').document(owner_id)
            user_doc = user_ref.get()
            
            if user_doc.exists:
                user_ref.update({
                    'team_ids': firestore.ArrayUnion([team_ref.id])
                })
            else:
                user_ref.set({
                    'user_id': owner_id,
                    'team_ids': [team_ref.id],
                    'created_at': firestore.SERVER_TIMESTAMP
                })
            
            logger.info(f"Team created: {team_ref.id}")
            return team_ref.id
        except Exception as e:
            logger.error(f"Error creating team: {e}")
            return None
    
    def join_team(self, user_id: str, invite_code: str) -> str:
        """Join a team using invite code"""
        try:
            # Find team by invite code
            teams_query = self.db.collection('teams').where('invite_code', '==', invite_code).limit(1)
            teams = list(teams_query.stream())
            
            if not teams:
                logger.error(f"No team found with invite code: {invite_code}")
                return None
            
            team_doc = teams[0]
            team_id = team_doc.id
            
            # Add user to team
            team_ref = self.db.collection('teams').document(team_id)
            team_ref.update({
                'member_ids': firestore.ArrayUnion([user_id]),
                'updated_at': firestore.SERVER_TIMESTAMP
            })
            
            # Add team to user's teams (create user doc if doesn't exist)
            user_ref = self.db.collection('users').document(user_id)
            user_doc = user_ref.get()
            
            if user_doc.exists:
                user_ref.update({
                    'team_ids': firestore.ArrayUnion([team_id])
                })
            else:
                user_ref.set({
                    'user_id': user_id,
                    'team_ids': [team_id],
                    'created_at': firestore.SERVER_TIMESTAMP
                })
            
            logger.info(f"User {user_id} joined team {team_id}")
            return team_id
        except Exception as e:
            logger.error(f"Error joining team: {e}")
            return None
    
    def get_user_teams(self, user_id: str) -> List[Dict]:
        """Get all teams for a user"""
        try:
            teams_query = self.db.collection('teams').where('member_ids', 'array_contains', user_id)
            teams = []
            
            for doc in teams_query.stream():
                team_data = doc.to_dict()
                team_data['id'] = doc.id
                teams.append(team_data)
            
            return teams
        except Exception as e:
            logger.error(f"Error getting user teams: {e}")
            return []
    
    def get_team_articles(self, team_id: str, stage: str = None) -> List[Dict]:
        """Get articles shared with a team"""
        try:
            query = self.db.collection('articles').where('team_id', '==', team_id)
            
            if stage:
                # Get all articles and filter in memory to avoid compound index
                articles = []
                for doc in query.stream():
                    article_data = doc.to_dict()
                    if article_data.get('stage') == stage:
                        article_data['id'] = doc.id
                        articles.append(article_data)
            else:
                articles = []
                for doc in query.stream():
                    article_data = doc.to_dict()
                    article_data['id'] = doc.id
                    articles.append(article_data)
            
            return articles
        except Exception as e:
            logger.error(f"Error getting team articles: {e}")
            return []
    
    def share_article_with_team(self, article_id: str, team_id: str) -> bool:
        """Share an article with a team"""
        try:
            article_ref = self.db.collection('articles').document(article_id)
            article_ref.update({
                'team_id': team_id,
                'is_team_shared': True,
                'updated_at': firestore.SERVER_TIMESTAMP
            })
            logger.info(f"Article {article_id} shared with team {team_id}")
            return True
        except Exception as e:
            logger.error(f"Error sharing article with team: {e}")
            return False

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
    protocol_version = 'HTTP/1.1'  # Force HTTP/1.1 to avoid HTTP/2 issues
    
    def do_GET(self):
        """Handle GET requests"""
        parsed_path = urlparse(self.path)
        path = parsed_path.path
        
        # Redirect root and old paths to login
        if path in ['/', '/home', '/kanban']:
            self.send_response(302)
            self.send_header('Location', '/login')
            self.send_header('Content-Length', '0')
            self.end_headers()
            return
            
        try:
            if path == '/health':
                self.serve_health()
            elif path == '/debug':
                self.serve_debug()
            elif path == '/login':
                self.serve_login()
            elif path == '/dashboard':
                self.serve_dashboard()
            elif path == '/api/stats':
                self.serve_api_stats()
            elif path.startswith('/api/articles'):
                self.serve_api_articles(parsed_path)
            elif path == '/api/debug':
                self.serve_api_debug()
            elif path == '/api/migrate':
                self.serve_api_migrate()
            elif path == '/api/auto-migrate':
                self.serve_api_auto_migrate()
            elif path == '/api/test-save':
                self.serve_api_test_save()
            elif path == '/api/teams':
                self.serve_api_teams()
            elif path.startswith('/api/teams/'):
                self.serve_api_team_details(parsed_path)
            elif path == '/logout':
                self.serve_logout()
            else:
                self.send_error(404, "Page not found")
        except Exception as e:
            logger.error(f"Error handling GET {path}: {e}")
            self.send_error(500, "Internal server error")
    
    def do_POST(self):
        """Handle POST requests"""
        try:
            if self.path == '/callback':
                self.handle_webhook()
            elif self.path.startswith('/api/articles'):
                self.handle_api_articles_post()
            elif self.path == '/api/auto-migrate':
                self.handle_api_auto_migrate()
            elif self.path == '/api/teams':
                self.handle_api_teams_post()
            elif self.path == '/api/teams/join':
                self.handle_api_teams_join()
            elif self.path.startswith('/api/articles/') and '/share' in self.path:
                self.handle_api_article_share()
            else:
                self.send_error(404, "Endpoint not found")
        except Exception as e:
            logger.error(f"Error handling POST {self.path}: {e}")
            self.send_error(500, "Internal server error")
    
    def do_OPTIONS(self):
        """Handle OPTIONS requests for CORS"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, X-User-Id')
        self.send_header('Content-Length', '0')
        self.end_headers()
    
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
        
        response = json.dumps(health_data).encode()
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(response)))
        self.end_headers()
        self.wfile.write(response)
    
    def serve_debug(self):
        """Debug endpoint to check Firestore data"""
        debug_data = {
            'timestamp': datetime.now().isoformat(),
            'firestore_status': 'unknown',
            'article_count': 0,
            'users': [],
            'errors': []
        }
        
        try:
            # Test Firestore connection
            test_doc = db.collection('_test').document('ping')
            test_doc.set({'timestamp': datetime.now().isoformat()})
            test_doc.delete()
            debug_data['firestore_status'] = 'connected'
            
            # Count articles
            articles = db.collection('articles').limit(100).stream()
            article_list = []
            users = set()
            
            for doc in articles:
                data = doc.to_dict()
                article_list.append({
                    'id': doc.id,
                    'user_id': data.get('user_id', 'none'),
                    'stage': data.get('stage', 'none'),
                    'title': data.get('title', 'untitled')[:50]
                })
                if data.get('user_id'):
                    users.add(data.get('user_id'))
            
            debug_data['article_count'] = len(article_list)
            debug_data['articles_sample'] = article_list[:5]
            debug_data['users'] = list(users)[:10]
            debug_data['user_count'] = len(users)
            
        except Exception as e:
            debug_data['firestore_status'] = 'error'
            debug_data['errors'].append(str(e))
            logger.error(f"Debug endpoint error: {e}")
        
        response = json.dumps(debug_data, indent=2).encode()
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(response)))
        self.end_headers()
        self.wfile.write(response)
    
    def serve_login(self):
        """Serve login page"""
        html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Login - Article Intelligence Hub</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            margin: 0;
            padding: 0;
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
        }}
        .login-container {{
            background: white;
            padding: 40px;
            border-radius: 20px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            text-align: center;
            max-width: 400px;
            width: 90%;
        }}
        h1 {{
            color: #333;
            margin: 0 0 10px;
            font-size: 28px;
        }}
        .subtitle {{
            color: #666;
            margin-bottom: 30px;
            font-size: 16px;
        }}
        .logo {{
            font-size: 64px;
            margin-bottom: 20px;
        }}
        .line-login-button {{
            background: #00B900;
            color: white;
            padding: 15px 30px;
            border: none;
            border-radius: 10px;
            font-size: 18px;
            font-weight: bold;
            cursor: pointer;
            display: inline-flex;
            align-items: center;
            gap: 10px;
            text-decoration: none;
            transition: background 0.3s;
        }}
        .line-login-button:hover {{
            background: #009900;
        }}
        .features {{
            margin-top: 40px;
            text-align: left;
        }}
        .feature {{
            margin: 15px 0;
            color: #555;
            display: flex;
            align-items: center;
            gap: 10px;
        }}
        .feature-icon {{
            font-size: 20px;
        }}
    </style>
</head>
<body>
    <div class="login-container">
        <div class="logo">📚</div>
        <h1>Article Intelligence Hub</h1>
        <p class="subtitle">Save and manage articles from LINE</p>
        
        <a href="#" id="liffLoginButton" class="line-login-button">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="white">
                <path d="M19.365 9.863c.349 0 .63.285.63.631 0 .345-.281.63-.63.63H17.61v1.125h1.755c.349 0 .63.283.63.63 0 .344-.281.629-.63.629h-2.386c-.345 0-.627-.285-.627-.629V8.108c0-.345.282-.63.63-.63h2.386c.346 0 .627.285.627.63 0 .349-.281.63-.63.63H17.61v1.125h1.755zm-3.855 3.016c0 .27-.174.51-.432.596-.064.021-.133.031-.199.031-.211 0-.391-.09-.51-.25l-2.443-3.317v2.94c0 .344-.279.629-.631.629-.346 0-.626-.285-.626-.629V8.108c0-.27.173-.51.43-.595.06-.023.136-.033.194-.033.195 0 .375.104.495.254l2.462 3.33V8.108c0-.345.282-.63.63-.63.345 0 .63.285.63.63v4.771zm-5.741 0c0 .344-.282.629-.631.629-.345 0-.627-.285-.627-.629V8.108c0-.345.282-.63.627-.63.349 0 .631.285.631.63v4.771zm-2.466.629H4.917c-.345 0-.63-.285-.63-.629V8.108c0-.345.285-.63.63-.63.349 0 .63.285.63.63v4.141h1.756c.348 0 .629.283.629.63 0 .344-.282.629-.629.629M24 10.314C24 4.943 18.615.572 12 .572S0 4.943 0 10.314c0 4.811 4.27 8.842 10.035 9.608.391.082.923.258 1.058.59.12.301.079.766.038 1.08l-.164 1.02c-.045.301-.24 1.186 1.049.645 1.291-.539 6.916-4.078 9.436-6.975C23.176 14.393 24 12.458 24 10.314"/>
            </svg>
            Login with LINE
        </a>
        
        <div class="features">
            <div class="feature">
                <span class="feature-icon">🔒</span>
                <span>Secure LINE authentication</span>
            </div>
            <div class="feature">
                <span class="feature-icon">📊</span>
                <span>Track your reading progress</span>
            </div>
            <div class="feature">
                <span class="feature-icon">🏷️</span>
                <span>Organize articles by stage</span>
            </div>
            <div class="feature">
                <span class="feature-icon">📱</span>
                <span>Access from LINE app</span>
            </div>
        </div>
    </div>
    
    <script src="https://static.line-scdn.net/liff/edge/2/sdk.js"></script>
    <script>
        document.addEventListener('DOMContentLoaded', async () => {{
            try {{
                await liff.init({{ liffId: '{LIFF_ID}' }});
                console.log('LIFF initialized');
                
                // Check if we're in LINE app or browser
                const isInClient = liff.isInClient();
                console.log('Is in LINE app:', isInClient);
                
                // If already logged in, redirect to dashboard
                if (liff.isLoggedIn()) {{
                    console.log('Already logged in, redirecting to dashboard');
                    window.location.href = '/dashboard';
                    return;
                }}
                
                document.getElementById('liffLoginButton').addEventListener('click', (e) => {{
                    e.preventDefault();
                    console.log('Login button clicked');
                    
                    if (!liff.isLoggedIn()) {{
                        // Use the LIFF URL if in browser
                        if (!isInClient) {{
                            window.location.href = '{LIFF_URL}';
                        }} else {{
                            liff.login({{ redirectUri: window.location.origin + '/dashboard' }});
                        }}
                    }} else {{
                        window.location.href = '/dashboard';
                    }}
                }});
                
            }} catch (error) {{
                console.error('LIFF initialization failed:', error);
                // Fallback: direct to LIFF URL
                document.getElementById('liffLoginButton').addEventListener('click', (e) => {{
                    e.preventDefault();
                    window.location.href = '{LIFF_URL}';
                }});
            }}
        }});
    </script>
</body>
</html>"""
        
        self.send_response(200)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.send_header('Content-Length', str(len(html.encode())))
        self.end_headers()
        self.wfile.write(html.encode())
    
    def serve_dashboard(self):
        """Serve responsive kanban dashboard"""
        html = """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>Article Hub Dashboard</title>
    <style>
        * {
            -webkit-tap-highlight-color: transparent;
            -webkit-touch-callout: none;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            background: #f5f5f5;
            margin: 0;
            padding: 10px;
            overflow-x: hidden;
            width: 100%;
            box-sizing: border-box;
            -webkit-user-select: none;
            user-select: none;
        }
        
        * {
            box-sizing: border-box;
        }
        .header {
            background: white;
            padding: 15px;
            border-radius: 10px;
            margin-bottom: 15px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }
        h1 {
            margin: 0 0 10px;
            color: #333;
            font-size: 24px;
        }
        .user-info {
            color: #666;
            font-size: 14px;
        }
        
        /* Kanban Board Styles */
        .kanban-container {
            margin-bottom: 20px;
        }
        .view-toggle {
            display: flex;
            gap: 10px;
            margin-bottom: 15px;
        }
        .view-btn {
            padding: 8px 16px;
            border: 1px solid #ddd;
            background: white;
            border-radius: 5px;
            cursor: pointer;
            transition: all 0.3s;
        }
        .view-btn.active {
            background: #667eea;
            color: white;
            border-color: #667eea;
        }
        
        /* Kanban Grid */
        .kanban-board {
            display: grid;
            grid-template-columns: repeat(4, minmax(0, 1fr));
            gap: 10px;
            margin-bottom: 20px;
            width: 100%;
            max-width: 100%;
        }
        
        @media (max-width: 768px) {
            .kanban-board {
                grid-template-columns: repeat(4, minmax(0, 1fr));
                gap: 4px;
                padding: 0;
            }
        }
        
        .kanban-column {
            background: white;
            border-radius: 10px;
            padding: 10px;
            min-height: 200px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }
        
        @media (max-width: 768px) {
            .kanban-column {
                min-height: 150px;
                padding: 5px;
                border-radius: 5px;
            }
        }
        
        .column-header {
            font-weight: bold;
            font-size: 14px;
            padding: 8px;
            margin-bottom: 10px;
            border-radius: 5px;
            text-align: center;
        }
        
        @media (max-width: 768px) {
            .column-header {
                font-size: 12px;
                padding: 5px;
                margin-bottom: 5px;
            }
        }
        
        .column-header.inbox { background: #e3f2fd; color: #1976d2; }
        .column-header.reading { background: #fff3e0; color: #f57c00; }
        .column-header.reviewing { background: #f3e5f5; color: #7b1fa2; }
        .column-header.completed { background: #e8f5e9; color: #388e3c; }
        
        .drop-zone {
            min-height: 150px;
            padding: 5px;
        }
        
        /* Article Cards */
        .article-card {
            background: #f8f9fa;
            border: 1px solid #e0e0e0;
            border-radius: 8px;
            padding: 10px;
            margin-bottom: 8px;
            cursor: pointer;
            transition: all 0.3s;
            font-size: 13px;
            position: relative;
            touch-action: pan-y; /* Allow vertical scroll but handle horizontal swipes */
            user-select: none; /* Prevent text selection during swipe */
        }
        
        /* Swipe hint on mobile */
        @media (max-width: 768px) {
            .article-card::after {
                content: '← Swipe →';
                position: absolute;
                bottom: 2px;
                right: 5px;
                font-size: 8px;
                color: #999;
                opacity: 0.5;
            }
        }
        
        .move-buttons {
            display: flex;
            gap: 2px;
            margin-top: 4px;
        }
        
        .move-btn {
            background: #e0e0e0;
            border: none;
            border-radius: 3px;
            padding: 4px 6px;
            cursor: pointer;
            font-size: 10px;
            flex: 1;
            transition: all 0.2s;
            -webkit-tap-highlight-color: transparent;
            touch-action: manipulation;
        }
        
        @media (max-width: 768px) {
            .move-btn {
                padding: 3px 4px;
                font-size: 9px;
            }
        }
        
        .move-btn:hover {
            background: #667eea;
            color: white;
        }
        
        .move-btn:disabled {
            opacity: 0.5;
            cursor: not-allowed;
        }
        
        .share-btn {
            background: #4CAF50;
            margin-left: 5px;
        }
        
        .share-btn:hover {
            background: #45a049;
        }
        
        /* Dark mode styles */
        @media (prefers-color-scheme: dark) {
            body {
                background: #1a1a1a;
                color: #e0e0e0;
            }
            
            .header {
                background: #2d2d2d;
                border-bottom-color: #444;
            }
            
            .view-toggle {
                background: #2d2d2d;
                border-color: #444;
            }
            
            .view-btn {
                background: #3d3d3d;
                color: #e0e0e0;
            }
            
            .view-btn.active {
                background: #667eea;
            }
            
            .kanban-column {
                background: #2d2d2d;
                border-color: #444;
            }
            
            .column-header {
                background: #3d3d3d;
                color: #e0e0e0;
            }
            
            .article-card {
                background: #3d3d3d;
                border-color: #555;
                color: #e0e0e0;
            }
            
            .article-card:hover {
                box-shadow: 0 3px 10px rgba(255,255,255,0.1);
            }
            
            .article-title {
                color: #e0e0e0;
            }
            
            .article-url {
                color: #999;
            }
            
            .move-btn {
                background: #3d3d3d;
                color: #e0e0e0;
                border: 1px solid #555;
            }
            
            .move-btn:hover {
                background: #667eea;
                border-color: #667eea;
            }
            
            .empty-state {
                color: #666;
            }
        }
        
        @media (max-width: 768px) {
            .article-card {
                padding: 6px;
                margin-bottom: 4px;
                font-size: 10px;
                border-radius: 4px;
            }
        }
        
        .article-card:hover {
            box-shadow: 0 3px 10px rgba(0,0,0,0.15);
            transform: translateY(-2px);
        }
        
        
        .article-header {
            display: flex;
            align-items: center;
            gap: 8px;
            margin-bottom: 5px;
        }
        
        .article-favicon {
            width: 16px;
            height: 16px;
            object-fit: contain;
        }
        
        .article-title {
            font-weight: 600;
            color: #333;
            flex: 1;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: normal;
            word-wrap: break-word;
            line-height: 1.2;
            max-height: 2.4em;
            display: -webkit-box;
            -webkit-line-clamp: 2;
            -webkit-box-orient: vertical;
        }
        
        @media (max-width: 768px) {
            .article-title {
                font-weight: 500;
                font-size: 10px;
            }
        }
        
        .article-url {
            color: #999;
            font-size: 11px;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }
        
        @media (max-width: 768px) {
            .article-url {
                font-size: 8px;
            }
        }
        
        .article-time {
            color: #666;
            font-size: 10px;
            margin-top: 3px;
        }
        
        @media (max-width: 768px) {
            .article-time {
                font-size: 7px;
                margin-top: 2px;
            }
        }
        
        .article-category {
            color: #667eea;
            font-size: 9px;
            font-weight: 500;
            text-transform: uppercase;
            margin-bottom: 2px;
        }
        
        @media (max-width: 768px) {
            .article-category {
                font-size: 7px;
            }
        }
        
        .article-tags {
            margin-top: 2px;
            display: flex;
            flex-wrap: wrap;
            gap: 2px;
        }
        
        .tag {
            background: #e3f2fd;
            color: #1976d2;
            font-size: 8px;
            padding: 1px 4px;
            border-radius: 8px;
            white-space: nowrap;
        }
        
        @media (max-width: 768px) {
            .tag {
                font-size: 7px;
                padding: 1px 3px;
                border-radius: 6px;
            }
        }
        
        /* List View */
        .list-view {
            display: none;
            background: white;
            border-radius: 10px;
            padding: 20px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }
        
        .tabs {
            display: flex;
            gap: 10px;
            margin-bottom: 20px;
            border-bottom: 2px solid #eee;
        }
        
        .tab {
            padding: 10px 20px;
            cursor: pointer;
            border-bottom: 3px solid transparent;
            transition: all 0.3s;
        }
        
        .tab.active {
            border-bottom-color: #667eea;
            color: #667eea;
        }
        
        .article-list-item {
            display: flex;
            align-items: center;
            gap: 10px;
            padding: 12px;
            border-bottom: 1px solid #eee;
            cursor: pointer;
            transition: background 0.3s;
        }
        
        .article-list-item:hover {
            background: #f8f9fa;
        }
        
        .empty-state {
            text-align: center;
            padding: 40px;
            color: #999;
        }
        
        /* Team View Styles */
        .team-view {
            display: none;
        }
        
        .team-container {
            background: white;
            border-radius: 10px;
            padding: 20px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }
        
        .team-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
        }
        
        .team-header h2 {
            margin: 0;
            color: #333;
        }
        
        .team-btn {
            background: #667eea;
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 5px;
            cursor: pointer;
            font-size: 14px;
            margin-left: 10px;
        }
        
        .team-btn:hover {
            background: #5a67d8;
        }
        
        /* Desktop Enhancements */
        @media (min-width: 1024px) {
            body {
                padding: 20px;
            }
            
            #kanbanView, #listView, #teamView {
                max-width: 1600px;
                margin: 0 auto;
            }
            
            .kanban-board {
                gap: 20px !important;
            }
            
            .kanban-column {
                min-width: 300px;
                padding: 15px;
            }
            
            .article-card {
                font-size: 13px !important;
                padding: 12px !important;
                cursor: grab;
            }
            
            .article-card:active {
                cursor: grabbing;
            }
            
            /* Hide mobile swipe hint on desktop */
            .article-card::after {
                display: none !important;
            }
            
            /* Enable text selection on desktop */
            .article-title, .article-url {
                -webkit-user-select: text;
                user-select: text;
            }
            
            /* Enhanced drop zones */
            .drop-zone.drag-over {
                background: rgba(103, 126, 234, 0.05);
                border: 2px dashed #667eea;
                border-radius: 8px;
            }
            
            /* Larger view buttons */
            .view-btn {
                padding: 12px 24px;
                font-size: 15px;
            }
        }
        
        /* Ultra-wide screens */
        @media (min-width: 1920px) {
            #kanbanView, #listView, #teamView {
                max-width: 1800px;
            }
            
            .kanban-column {
                min-width: 400px;
            }
        }
        
        .team-selector {
            margin-bottom: 20px;
            padding: 15px;
            background: #f8f9fa;
            border-radius: 8px;
        }
        
        .team-selector label {
            font-weight: 600;
            margin-right: 10px;
        }
        
        .team-selector select {
            padding: 8px 12px;
            border: 1px solid #ddd;
            border-radius: 5px;
            font-size: 14px;
            min-width: 200px;
        }
        
        .team-members {
            margin-bottom: 20px;
            padding: 15px;
            background: #f8f9fa;
            border-radius: 8px;
        }
        
        .team-members h3 {
            margin-top: 0;
        }
        
        .invite-section {
            margin-top: 15px;
            padding-top: 15px;
            border-top: 1px solid #e0e0e0;
        }
        
        .invite-code {
            font-family: monospace;
            background: #e3f2fd;
            padding: 4px 8px;
            border-radius: 4px;
            font-weight: 600;
            user-select: all;
        }
        
        .members-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(100px, 1fr));
            gap: 10px;
            margin: 15px 0;
        }
        
        .member-card {
            text-align: center;
            padding: 10px;
            background: white;
            border-radius: 8px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }
        
        .member-avatar {
            font-size: 30px;
            margin-bottom: 5px;
        }
        
        .member-name {
            font-size: 12px;
            color: #666;
        }
        
        .team-articles {
            margin-top: 20px;
        }
        
        .team-articles h3 {
            margin-bottom: 15px;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>📚 Article Hub</h1>
        <div class="user-info">
            <span id="userInfo"></span>
            <a href="#" onclick="checkDebug()" style="color: #667eea; font-size: 12px;">Debug</a>
            <a href="/logout" style="color: #ef4444; font-size: 12px; margin-left: 10px;">Logout</a>
        </div>
    </div>
    
    <div class="view-toggle">
        <button class="view-btn active" onclick="toggleView('kanban')">📋 Kanban</button>
        <button class="view-btn" onclick="toggleView('list')">📑 List</button>
        <button class="view-btn" onclick="toggleView('team')">👥 Team</button>
    </div>
    
    <!-- Kanban View -->
    <div id="kanbanView" class="kanban-container">
        <div class="kanban-board">
            <div class="kanban-column">
                <div class="column-header inbox">📥 Inbox (<span id="inbox-count">0</span>)</div>
                <div class="drop-zone" data-stage="inbox" id="inbox-articles"></div>
            </div>
            <div class="kanban-column">
                <div class="column-header reading">📖 Reading (<span id="reading-count">0</span>)</div>
                <div class="drop-zone" data-stage="reading" id="reading-articles"></div>
            </div>
            <div class="kanban-column">
                <div class="column-header reviewing">🔍 Reviewing (<span id="reviewing-count">0</span>)</div>
                <div class="drop-zone" data-stage="reviewing" id="reviewing-articles"></div>
            </div>
            <div class="kanban-column">
                <div class="column-header completed">✅ Completed (<span id="completed-count">0</span>)</div>
                <div class="drop-zone" data-stage="completed" id="completed-articles"></div>
            </div>
        </div>
    </div>
    
    <!-- List View -->
    <div id="listView" class="list-view">
        <div class="tabs">
            <div class="tab active" data-stage="inbox">Inbox</div>
            <div class="tab" data-stage="reading">Reading</div>
            <div class="tab" data-stage="reviewing">Reviewing</div>
            <div class="tab" data-stage="completed">Completed</div>
        </div>
        <div id="list-articles">Loading...</div>
    </div>
    
    <!-- Team View -->
    <div id="teamView" class="team-view" style="display: none;">
        <div class="team-container">
            <div class="team-header">
                <h2>👥 Team Mode</h2>
                <button class="team-btn" onclick="showCreateTeam()">Create Team</button>
                <button class="team-btn" onclick="showJoinTeam()">Join Team</button>
            </div>
            
            <div class="team-selector">
                <label>Select Team:</label>
                <select id="teamSelect" onchange="loadTeamArticles()">
                    <option value="">Personal Articles</option>
                </select>
            </div>
            
            <div id="teamMembers" class="team-members" style="display: none;">
                <h3>Team Members</h3>
                <div id="membersList"></div>
                <div class="invite-section">
                    <p>Invite Code: <span id="inviteCode" class="invite-code"></span></p>
                </div>
            </div>
            
            <div id="teamArticles" class="team-articles">
                <h3>Team Articles</h3>
                <div class="kanban-board" id="teamKanban">
                    <div class="kanban-column">
                        <div class="column-header inbox">📥 Inbox (<span id="team-inbox-count">0</span>)</div>
                        <div class="drop-zone" data-stage="inbox" id="team-inbox-articles"></div>
                    </div>
                    <div class="kanban-column">
                        <div class="column-header reading">📖 Reading (<span id="team-reading-count">0</span>)</div>
                        <div class="drop-zone" data-stage="reading" id="team-reading-articles"></div>
                    </div>
                    <div class="kanban-column">
                        <div class="column-header reviewing">🔍 Reviewing (<span id="team-reviewing-count">0</span>)</div>
                        <div class="drop-zone" data-stage="reviewing" id="team-reviewing-articles"></div>
                    </div>
                    <div class="kanban-column">
                        <div class="column-header completed">✅ Completed (<span id="team-completed-count">0</span>)</div>
                        <div class="drop-zone" data-stage="completed" id="team-completed-articles"></div>
                    </div>
                </div>
            </div>
        </div>
    </div>
    
    <script src="https://static.line-scdn.net/liff/edge/2/sdk.js"></script>
    <script>
        let currentStage = 'inbox';
        let userId = null;
        let currentView = 'kanban';
        let articlesData = {};
        let userTeams = [];
        
        // Make key variables globally accessible for debugging
        window.userId = null;
        window.currentView = 'kanban';
        window.articlesData = {};
        window.DEBUG = true;
        
        // Check environment
        const isDesktop = () => window.innerWidth >= 1024;
        const isInLINE = () => typeof liff !== 'undefined' && liff.isInClient && liff.isInClient();
        
        // Initialize LIFF with proper external browser support
        window.onload = async function() {
            // First check localStorage for existing session
            const storedUserId = localStorage.getItem('lineUserId');
            const storedDisplayName = localStorage.getItem('lineDisplayName');
            
            if (storedUserId) {
                console.log('Found existing session in localStorage:', storedUserId);
                userId = storedUserId;
                window.userId = storedUserId;  // Update global
                document.getElementById('userInfo').innerHTML = '👤 ' + (storedDisplayName || 'User') + ' | ';
            }
            
            try {
                await liff.init({ 
                    liffId: "2007870100-ao8GpgRQ",
                    withLoginOnExternalBrowser: true // Enable login on external browsers
                });
                console.log('LIFF initialized, isInClient:', liff.isInClient());
                
                if (liff.isLoggedIn()) {
                    const profile = await liff.getProfile();
                    const liffUserId = profile.userId;
                    const displayName = profile.displayName || 'User';
                    
                    // Update userId if different from stored
                    if (liffUserId && liffUserId !== userId) {
                        userId = liffUserId;
                        window.userId = liffUserId;  // Update global
                        localStorage.setItem('lineUserId', userId);
                        localStorage.setItem('lineDisplayName', displayName);
                        console.log('Updated user ID from LIFF:', userId);
                    }
                    
                    // Enhanced user info for desktop
                    if (isDesktop() && !isInLINE()) {
                        var shareButton = '<button onclick="shareArticlesToLINE()" style="background: #00B900; color: white; border: none; padding: 4px 10px; border-radius: 4px; font-size: 11px; cursor: pointer; margin: 0 5px;" title="Share to LINE">Share</button>';
                        document.getElementById('userInfo').innerHTML = '👤 ' + displayName + ' | ' + shareButton;
                        showDesktopFeatures();
                    } else {
                        document.getElementById('userInfo').innerHTML = '👤 ' + displayName + ' | ';
                    }
                    
                    // Auto-migrate articles on first load
                    console.log('=== LIFF LOGIN SUCCESS ===');
                    console.log('UserId from LIFF:', userId);
                    console.log('DisplayName:', displayName);
                    
                    await autoMigrateArticles();
                    
                    // Load user teams
                    await loadUserTeams();
                    
                    // Load data
                    console.log('Starting loadKanbanData with userId:', userId);
                    loadKanbanData();
                } else {
                    // Not logged in - handle based on platform
                    if (!isInLINE() && isDesktop()) {
                        // External browser on desktop - use LINE Login
                        showDesktopLoginOptions();
                    } else {
                        showLoginRequired();
                    }
                }
            } catch (error) {
                console.error('LIFF initialization failed:', error);
                
                // Continue with stored session if available
                if (userId) {
                    console.log('Continuing with stored session despite LIFF error');
                    
                    // Load data with stored userId
                    await autoMigrateArticles();
                    await loadUserTeams();
                    loadKanbanData();
                    
                    if (isDesktop() && !isInLINE()) {
                        showDesktopFeatures();
                    }
                } else if (isDesktop()) {
                    showDesktopLoginOptions();
                } else {
                    showLoginRequired();
                }
            }
        };
        
        function showDesktopLoginOptions() {
            document.body.innerHTML = `
                <div style="
                    display: flex;
                    flex-direction: column;
                    align-items: center;
                    justify-content: center;
                    min-height: 100vh;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    padding: 20px;
                ">
                    <div style="
                        background: white;
                        padding: 40px;
                        border-radius: 15px;
                        box-shadow: 0 10px 40px rgba(0,0,0,0.2);
                        max-width: 450px;
                        text-align: center;
                    ">
                        <h1 style="color: #333; margin-bottom: 10px;">📚 Article Intelligence Hub</h1>
                        <p style="color: #666; margin-bottom: 30px;">Access your articles from desktop</p>
                        
                        <button onclick="liff.login()" style="
                            background: #00B900;
                            color: white;
                            border: none;
                            padding: 15px 30px;
                            border-radius: 8px;
                            font-size: 16px;
                            cursor: pointer;
                            width: 100%;
                            margin-bottom: 15px;
                            display: flex;
                            align-items: center;
                            justify-content: center;
                            gap: 10px;
                        ">
                            <svg width="24" height="24" viewBox="0 0 24 24" fill="white">
                                <path d="M19.365 9.863c.349 0 .63.285.63.631 0 .345-.281.63-.63.63H17.61v1.125h1.755c.349 0 .63.283.63.63 0 .344-.281.629-.63.629h-2.386c-.345 0-.627-.285-.627-.629V8.108c0-.345.282-.63.63-.63h2.386c.346 0 .627.285.627.63 0 .349-.281.63-.63.63H17.61v1.125h1.755zm-3.855 3.016c0 .27-.174.51-.432.596-.064.021-.133.031-.199.031-.211 0-.391-.09-.51-.25l-2.443-3.317v2.94c0 .344-.279.629-.631.629-.346 0-.626-.285-.626-.629V8.108c0-.27.173-.51.43-.595.06-.023.136-.033.194-.033.195 0 .375.104.495.254l2.462 3.33V8.108c0-.345.282-.63.63-.63.345 0 .63.285.63.63v4.771zm-5.741 0c0 .344-.282.629-.631.629-.345 0-.627-.285-.627-.629V8.108c0-.345.282-.63.627-.63.349 0 .631.285.631.63v4.771zm-2.466.629H4.917c-.345 0-.63-.285-.63-.629V8.108c0-.345.285-.63.63-.63.349 0 .63.285.63.63v4.141h1.756c.348 0 .629.283.629.63 0 .344-.282.629-.629.629M24 10.314C24 4.943 18.615.572 12 .572S0 4.943 0 10.314c0 4.811 4.27 8.842 10.035 9.608.391.082.923.258 1.058.59.12.301.079.766.038 1.08l-.164 1.02c-.045.301-.24 1.186 1.049.645 1.291-.539 6.916-4.078 9.436-6.975C23.176 14.393 24 12.458 24 10.314"/>
                            </svg>
                            Login with LINE
                        </button>
                        
                        <div style="
                            border-top: 1px solid #e0e0e0;
                            margin: 20px 0;
                            padding-top: 20px;
                        ">
                            <p style="color: #999; font-size: 14px; margin-bottom: 15px;">Or access from LINE app for full features:</p>
                            <a href="https://line.me/R/ti/p/@YOUR_LINE_BOT_ID" style="
                                color: #00B900;
                                text-decoration: none;
                                font-weight: bold;
                            ">Open in LINE App →</a>
                        </div>
                    </div>
                </div>
            `;
        }
        
        function showDesktopFeatures() {
            if (!localStorage.getItem('desktopFeaturesShown')) {
                const notice = document.createElement('div');
                notice.style.cssText = `
                    position: fixed;
                    bottom: 20px;
                    right: 20px;
                    background: white;
                    padding: 20px;
                    border-radius: 10px;
                    box-shadow: 0 5px 20px rgba(0,0,0,0.15);
                    max-width: 350px;
                    z-index: 1000;
                    border-left: 4px solid #00B900;
                `;
                
                notice.innerHTML = `
                    <h4 style="margin: 0 0 10px 0; color: #333;">💻 Desktop Features Available</h4>
                    <ul style="margin: 10px 0; padding-left: 20px; color: #666; font-size: 14px;">
                        <li>Drag & drop articles between stages</li>
                        <li>Keyboard shortcuts (press ? for help)</li>
                        <li>Share articles to LINE friends</li>
                        <li>Full-screen kanban view</li>
                    </ul>
                    <button onclick="this.parentElement.remove(); localStorage.setItem('desktopFeaturesShown', 'true');" style="
                        background: #00B900;
                        color: white;
                        border: none;
                        padding: 8px 16px;
                        border-radius: 5px;
                        cursor: pointer;
                        width: 100%;
                    ">Got it!</button>
                ';
                
                document.body.appendChild(notice);
                
                setTimeout(() => {
                    if (notice.parentElement) {
                        notice.style.animation = 'fadeOut 0.5s ease';
                        setTimeout(() => notice.remove(), 500);
                    }
                }, 10000);
            }
        }
        
        // LINE Social Plugins integration
        function shareArticlesToLINE() {
            const selectedArticles = getSelectedArticles(); // You can implement article selection
            const message = 'Check out my reading list:\n' + window.location.href;
            
            if (liff.isApiAvailable('shareTargetPicker')) {
                liff.shareTargetPicker([{
                    type: 'text',
                    text: message
                }]).then(() => {
                    console.log('Shared successfully');
                }).catch(err => {
                    console.error('Share failed:', err);
                    // Fallback to LINE share URL
                    window.open('https://social-plugins.line.me/lineit/share?url=' + encodeURIComponent(window.location.href));
                });
            } else {
                // Use LINE social plugin for external browsers
                window.open('https://social-plugins.line.me/lineit/share?url=' + encodeURIComponent(window.location.href));
            }
        }
        
        function getSelectedArticles() {
            // Placeholder - implement article selection logic
            return articlesData.inbox || [];
        }
        
        async function autoMigrateArticles() {
            if (!userId) {
                console.log('No userId available for auto-migration');
                return;
            }
            
            try {
                // Silently migrate any unclaimed articles to current user
                const res = await fetch('/api/auto-migrate', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-User-Id': userId
                    },
                    body: JSON.stringify({ user_id: userId })
                });
                
                if (res.ok) {
                    const result = await res.json();
                    if (result.migrated > 0) {
                        console.log('Auto-migrated ' + result.migrated + ' articles');
                    }
                }
            } catch (e) {
                console.error('Auto-migration error:', e);
                // Silent fail - don't disrupt user experience
            }
        }
        
        async function loadUserTeams() {
            if (!userId) {
                console.warn('No userId available for loading teams');
                userTeams = [];
                return;
            }
            
            try {
                console.log('Loading teams for user:', userId);
                const res = await fetch('/api/teams?user_id=' + encodeURIComponent(userId));
                
                if (!res.ok) {
                    console.error('Failed to load teams: ' + res.status);
                    userTeams = [];
                    return;
                }
                
                userTeams = await res.json();
                console.log('User teams loaded:', userTeams.length, userTeams);
            } catch (error) {
                console.error('Error loading user teams:', error);
                userTeams = [];
            }
        }
        
        async function shareArticleWithTeam(articleId) {
            if (userTeams.length === 0) {
                alert('You are not a member of any teams yet.');
                return;
            }
            
            // Show team selection dialog
            const teamOptions = userTeams.map(t => t.name + ' (' + t.id + ')').join('\n');
            const selectedIndex = prompt('Select a team to share with:\n' + userTeams.map((t, i) => i+1 + '. ${t.name).join('\n')}\n\nEnter number:');
            
            if (selectedIndex && !isNaN(selectedIndex)) {
                const teamIndex = parseInt(selectedIndex) - 1;
                if (teamIndex >= 0 && teamIndex < userTeams.length) {
                    const team = userTeams[teamIndex];
                    try {
                        const res = await fetch('/api/articles/' + articleId + '/share', {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json',
                                'X-User-Id': userId
                            },
                            body: JSON.stringify({ team_id: team.id })
                        });
                        
                        if (res.ok) {
                            alert('Article shared with team: ' + team.name);
                        } else {
                            alert('Failed to share article');
                        }
                    } catch (error) {
                        console.error('Error sharing article:', error);
                        alert('Error sharing article');
                    }
                }
            }
        }
        
        window.checkDebug = async function() {
            try {
                const res = await fetch('/api/debug?user_id=' + (window.userId || userId || 'none'));
                const data = await res.json();
                console.log('Debug info:', data);
                const userArticles = data.user_articles_count || 0;
                alert('Debug Info:\n' +
                      'Total articles: ' + data.article_count + '\n' +
                      'Your articles: ' + userArticles + '\n' +
                      'Your ID: ' + (window.userId || userId || 'none') + '\n' +
                      'Check console for details');
            } catch (e) {
                console.error('Debug error:', e);
                alert('Debug failed: ' + e.message);
            }
        }
        
        function showLoginRequired() {
            window.location.href = '/login';
        }
        
        function toggleView(view) {
            currentView = view;
            document.querySelectorAll('.view-btn').forEach(btn => {
                btn.classList.toggle('active', btn.textContent.toLowerCase().includes(view));
            });
            document.getElementById('kanbanView').style.display = view === 'kanban' ? 'block' : 'none';
            document.getElementById('listView').style.display = view === 'list' ? 'block' : 'none';
            document.getElementById('teamView').style.display = view === 'team' ? 'block' : 'none';
            
            if (view === 'list') {
                loadListView(currentStage);
            } else if (view === 'team') {
                loadTeamView();
            }
        }
        
        function getFaviconUrl(url) {
            try {
                const domain = new URL(url).hostname;
                return 'https://www.google.com/s2/favicons?domain=' + domain + '&sz=16';
            } catch {
                return '';
            }
        }
        
        function formatDate(timestamp) {
            if (!timestamp) return '';
            const date = timestamp.toDate ? timestamp.toDate() : new Date(timestamp);
            const now = new Date();
            const diff = now - date;
            const days = Math.floor(diff / (1000 * 60 * 60 * 24));
            
            if (days === 0) return 'Today';
            if (days === 1) return 'Yesterday';
            if (days < 7) return days + ' days ago';
            return date.toLocaleDateString();
        }
        
        function showSwipeTutorial() {
            const tutorial = document.createElement('div');
            tutorial.style.cssText = '
                position: fixed;
                top: 50%;
                left: 50%;
                transform: translate(-50%, -50%);
                background: rgba(0, 0, 0, 0.9);
                color: white;
                padding: 20px;
                border-radius: 12px;
                z-index: 10000;
                text-align: center;
                max-width: 280px;
            `;
            
            tutorial.innerHTML = `
                <div style="font-size: 30px; margin-bottom: 10px;">👈 👉</div>
                <h3 style="margin: 10px 0;">Swipe to Move Articles!</h3>
                <p style="margin: 10px 0; font-size: 14px;">
                    Swipe articles <strong>left</strong> or <strong>right</strong> to move them between stages
                </p>
                <div style="display: flex; justify-content: space-around; margin: 15px 0; font-size: 12px;">
                    <div>← Previous Stage</div>
                    <div>Next Stage →</div>
                </div>
                <button onclick="this.parentElement.remove()" style="
                    background: #007AFF;
                    color: white;
                    border: none;
                    padding: 10px 20px;
                    border-radius: 6px;
                    font-size: 14px;
                    margin-top: 10px;
                    cursor: pointer;
                ">Got it!</button>
            ';
            
            document.body.appendChild(tutorial);
            
            // Auto-remove after 5 seconds
            setTimeout(() => {
                if (tutorial.parentElement) {
                    tutorial.remove();
                }
            }, 5000);
        }
        
        async function loadKanbanData() {
            console.log('=== loadKanbanData called ===');
            console.log('userId value:', userId);
            console.log('userId type:', typeof userId);
            
            if (!userId) {
                console.error('No user ID available - cannot load data');
                alert('No user ID found. Please login again.');
                return;
            }
            
            // Show swipe tutorial once for mobile users
            if (window.innerWidth <= 768 && !localStorage.getItem('swipeTutorialShown')) {
                showSwipeTutorial();
                localStorage.setItem('swipeTutorialShown', 'true');
            }
            
            console.log('Loading data for user:', userId);
            const stages = ['inbox', 'reading', 'reviewing', 'completed'];
            articlesData = {};
            
            // Ensure userId is URL encoded
            const encodedUserId = encodeURIComponent(userId);
            console.log('Encoded userId:', encodedUserId);
            
            for (const stage of stages) {
                try {
                    console.log('Fetching ' + stage + ' articles for user: ' + userId);
                    const res = await fetch('/api/articles?stage=' + stage + '&user_id=' + encodedUserId);
                    console.log('Response status for ' + stage + ':', res.status);
                    
                    if (!res.ok) {
                        console.error('Failed to fetch ' + stage + ':', res.status, res.statusText);
                        continue;
                    }
                    
                    const responseText = await res.text();
                    console.log('Raw response for ' + stage + ':', responseText);
                    
                    let articles;
                    try {
                        articles = JSON.parse(responseText);
                    } catch (parseError) {
                        console.error('Failed to parse JSON response:', parseError);
                        console.error('Response text:', responseText);
                        continue;
                    }
                    
                    console.log('Got ' + articles.length + ' articles for ' + stage);
                    console.log('Articles data:', articles);
                    articlesData[stage] = articles;
                    
                    // Debug: Check if articles have proper structure
                    if (articles.length > 0) {
                        console.log('First article sample:', articles[0]);
                    }
                    
                    // Update count
                    document.getElementById(stage + '-count').textContent = articles.length;
                    
                    // Render articles
                    const container = document.getElementById(stage + '-articles');
                    if (articles.length === 0) {
                        container.innerHTML = '<div class="empty-state">Drop articles here</div>';
                    } else {
                        container.innerHTML = articles.map(a => {
                            const favicon = getFaviconUrl(a.url);
                            const category = a.category || 'general';
                            const tags = a.tags ? a.tags.split(',').map(t => t.trim()).filter(t => t) : [];
                            // Check if it's an image
                            const isImage = a.metadata?.type === 'line-image' || a.url?.startsWith('https://obs.line-scdn.net/');
                            const stageIndex = ['inbox', 'reading', 'reviewing', 'completed'].indexOf(stage);
                            const canMoveLeft = stageIndex > 0;
                            const canMoveRight = stageIndex < 3;
                            
                            return '
                                <div class="article-card" data-id="' + a.id + '" data-stage="' + stage + '" data-url="' + a.url + '">
                                    <div class="article-header">
                                        ' + !isImage && favicon ? '<img src="' + favicon + '" class="article-favicon" onerror="this.style.display='none'">' : '
                                        <div class="article-title" title="' + a.title + '">' + a.title + '</div>
                                    </div>
                                    ' + isImage ? '<img src="' + a.url + '" style="width: 100%; height: 100px; object-fit: cover; border-radius: 4px; margin: 5px 0;" onerror="this.style.display='none'">' : '
                                    <div class="article-category">' + category + '</div>
                                    ' + !isImage ? '<div class="article-url" title="${a.url + '">' + a.url + '</div>' : ''}
                                    ' + tags.length > 0 ? '<div class="article-tags">' + tags.map(tag => '<span class="tag">${tag + '</span>').join('') + '</div>' : ''}
                                    <div class="article-time">' + formatDate(a.created_at) + '</div>
                                    <div class="move-buttons">
                                        <button class="move-btn move-left" ' + !canMoveLeft ? 'disabled' : ' data-id="' + a.id + '" data-direction="left">←</button>
                                        <button class="move-btn move-right" ' + !canMoveRight ? 'disabled' : ' data-id="' + a.id + '" data-direction="right">→</button>
                                        ' + userTeams.length > 0 ? '<button class="move-btn share-btn" onclick="shareArticleWithTeam(a.id)">🤝</button>' : '
                                    </div>
                                </div>
                            ';
                        }).join('');
                    }
                } catch (e) {
                    console.error('Error loading ' + stage + ':', e);
                }
            }
            
            attachDragListeners();
        }
        
        function attachDragListeners() {
            // Article cards
            // Handle move buttons
            document.querySelectorAll('.move-btn').forEach(btn => {
                btn.addEventListener('click', async (e) => {
                    e.stopPropagation();
                    e.preventDefault();
                    
                    // Visual feedback
                    btn.style.opacity = '0.5';
                    btn.disabled = true;
                    
                    const articleId = btn.dataset.id;
                    const direction = btn.dataset.direction;
                    const card = btn.closest('.article-card');
                    const currentStage = card.dataset.stage;
                    const stages = ['inbox', 'reading', 'reviewing', 'completed'];
                    const currentIndex = stages.indexOf(currentStage);
                    
                    console.log('Move button clicked:', { articleId, direction, currentStage, currentIndex });
                    
                    let newStage;
                    if (direction === 'left' && currentIndex > 0) {
                        newStage = stages[currentIndex - 1];
                    } else if (direction === 'right' && currentIndex < 3) {
                        newStage = stages[currentIndex + 1];
                    }
                    
                    if (newStage) {
                        try {
                            console.log('Moving article to:', newStage);
                            const response = await fetch('/api/articles/' + articleId + '/stage', {
                                method: 'POST',
                                headers: {
                                    'Content-Type': 'application/json',
                                    'X-User-Id': userId
                                },
                                body: JSON.stringify({ stage: newStage })
                            });
                            
                            if (response.ok) {
                                console.log('Move successful, reloading...');
                                await loadKanbanData();
                            } else {
                                console.error('Move failed:', response.status, await response.text());
                                btn.style.opacity = '1';
                                btn.disabled = false;
                            }
                        } catch (error) {
                            console.error('Failed to move article:', error);
                            btn.style.opacity = '1';
                            btn.disabled = false;
                        }
                    } else {
                        btn.style.opacity = '1';
                        btn.disabled = false;
                    }
                });
            });
            
            // Add swipe gesture support for article cards
            document.querySelectorAll('.article-card').forEach(card => {
                let touchStartX = 0;
                let touchStartY = 0;
                let touchEndX = 0;
                let touchEndY = 0;
                let cardStartTransform = 0;
                let isSwiping = false;
                
                // Touch start
                card.addEventListener('touchstart', (e) => {
                    touchStartX = e.changedTouches[0].screenX;
                    touchStartY = e.changedTouches[0].screenY;
                    cardStartTransform = 0;
                    isSwiping = false;
                    card.style.transition = 'none';
                }, { passive: true });
                
                // Touch move - show visual feedback
                card.addEventListener('touchmove', (e) => {
                    const currentX = e.changedTouches[0].screenX;
                    const currentY = e.changedTouches[0].screenY;
                    const deltaX = currentX - touchStartX;
                    const deltaY = currentY - touchStartY;
                    
                    // Only handle horizontal swipes
                    if (Math.abs(deltaX) > Math.abs(deltaY) && Math.abs(deltaX) > 10) {
                        isSwiping = true;
                        e.preventDefault();
                        
                        // Visual feedback - move card horizontally
                        const translateX = deltaX * 0.5; // Reduced movement for better UX
                        card.style.transform = 'translateX(' + translateX + 'px)';
                        
                        // Change opacity based on swipe distance
                        const opacity = Math.max(0.3, 1 - Math.abs(deltaX) / 300);
                        card.style.opacity = opacity;
                        
                        // Show direction indicator
                        if (Math.abs(deltaX) > 50) {
                            card.style.backgroundColor = deltaX > 0 ? 'rgba(76, 175, 80, 0.1)' : 'rgba(244, 67, 54, 0.1)';
                        }
                    }
                }, { passive: false });
                
                // Touch end - process swipe
                card.addEventListener('touchend', async (e) => {
                    touchEndX = e.changedTouches[0].screenX;
                    touchEndY = e.changedTouches[0].screenY;
                    
                    // Reset visual styles
                    card.style.transition = 'all 0.3s ease';
                    card.style.transform = '';
                    card.style.opacity = '';
                    card.style.backgroundColor = '';
                    
                    if (!isSwiping) {
                        // Handle tap (click)
                        handleCardClick(card);
                        return;
                    }
                    
                    const deltaX = touchEndX - touchStartX;
                    const deltaY = touchEndY - touchStartY;
                    const minSwipeDistance = 50;
                    
                    // Check if it's a horizontal swipe
                    if (Math.abs(deltaX) > minSwipeDistance && Math.abs(deltaX) > Math.abs(deltaY)) {
                        const articleId = card.dataset.id;
                        const currentStage = card.dataset.stage;
                        const stages = ['inbox', 'reading', 'reviewing', 'completed'];
                        const currentIndex = stages.indexOf(currentStage);
                        
                        let newStage;
                        if (deltaX > 0 && currentIndex < 3) {
                            // Swipe right - move to next stage
                            newStage = stages[currentIndex + 1];
                        } else if (deltaX < 0 && currentIndex > 0) {
                            // Swipe left - move to previous stage
                            newStage = stages[currentIndex - 1];
                        }
                        
                        if (newStage) {
                            // Animate card out
                            card.style.transform = 'translateX(' + deltaX > 0 ? '100%' : '-100%)';
                            card.style.opacity = '0';
                            
                            try {
                                const response = await fetch('/api/articles/' + articleId + '/stage', {
                                    method: 'POST',
                                    headers: {
                                        'Content-Type': 'application/json',
                                        'X-User-Id': userId
                                    },
                                    body: JSON.stringify({ stage: newStage })
                                });
                                
                                if (response.ok) {
                                    // Show success feedback
                                    setTimeout(() => {
                                        loadKanbanData();
                                    }, 300);
                                } else {
                                    // Reset card position on error
                                    card.style.transform = '';
                                    card.style.opacity = '';
                                }
                            } catch (error) {
                                console.error('Failed to move article:', error);
                                card.style.transform = '';
                                card.style.opacity = '';
                            }
                        }
                    }
                }, { passive: true });
                
                // Regular click handler
                function handleCardClick(card) {
                    const url = card.dataset.url;
                    const articleId = card.dataset.id;
                    const stage = card.dataset.stage;
                    const article = articlesData[stage]?.find(a => a.id === articleId);
                    
                    if (url) {
                        // Check if it's a LINE image URL
                        if (url.includes('obs.line-scdn.net') || (article && article.metadata?.type === 'line-image')) {
                            // For LINE images, show in a modal
                            const img = new Image();
                            img.onload = function() {
                                const modal = document.createElement('div');
                                modal.style.cssText = 'position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,0.9);z-index:9999;display:flex;align-items:center;justify-content:center;cursor:pointer;';
                                const imgElement = document.createElement('img');
                                imgElement.src = url;
                                imgElement.style.cssText = 'max-width:90%;max-height:90%;border-radius:8px;';
                                modal.appendChild(imgElement);
                                modal.onclick = () => modal.remove();
                                document.body.appendChild(modal);
                            };
                            img.onerror = function() {
                                window.open(url, '_blank');
                            };
                            img.src = url;
                        } else {
                            window.open(url, '_blank');
                        }
                    }
                }
                
                // Also handle regular clicks for desktop
                card.addEventListener('click', (e) => {
                    // Don't open if clicking on buttons
                    if (e.target.classList.contains('move-btn') || e.target.classList.contains('share-btn')) {
                        return;
                    }
                    
                    // Don't handle if it was a swipe
                    if (isSwiping) {
                        isSwiping = false;
                        return;
                    }
                    
                    handleCardClick(card);
                });
            });
            
            // Enhanced drag-and-drop for desktop
            if (window.innerWidth >= 1024) {
                let draggedElement = null;
                
                // Make article cards draggable on desktop
                document.querySelectorAll('.article-card').forEach(card => {
                    card.draggable = true;
                    
                    card.addEventListener('dragstart', (e) => {
                        draggedElement = card;
                        card.style.opacity = '0.5';
                        e.dataTransfer.effectAllowed = 'move';
                        e.dataTransfer.setData('text/html', card.innerHTML);
                    });
                    
                    card.addEventListener('dragend', (e) => {
                        card.style.opacity = '';
                        draggedElement = null;
                        
                        // Remove all drag-over classes
                        document.querySelectorAll('.drop-zone').forEach(zone => {
                            zone.classList.remove('drag-over');
                        });
                    });
                });
                
                // Drop zones with visual feedback
                document.querySelectorAll('.drop-zone').forEach(zone => {
                    zone.addEventListener('dragover', (e) => {
                        e.preventDefault();
                        e.dataTransfer.dropEffect = 'move';
                        zone.classList.add('drag-over');
                        
                        // Add visual indicator for drop position
                        const afterElement = getDragAfterElement(zone, e.clientY);
                        if (draggedElement) {
                            if (afterElement == null) {
                                zone.appendChild(draggedElement);
                            } else {
                                zone.insertBefore(draggedElement, afterElement);
                            }
                        }
                    });
                    
                    zone.addEventListener('dragleave', (e) => {
                        if (e.target === zone && !zone.contains(e.relatedTarget)) {
                            zone.classList.remove('drag-over');
                        }
                    });
                    
                    zone.addEventListener('drop', async (e) => {
                        e.preventDefault();
                        zone.classList.remove('drag-over');
                        
                        if (draggedElement) {
                            const articleId = draggedElement.dataset.id;
                            const newStage = zone.dataset.stage;
                            const oldStage = draggedElement.dataset.stage;
                            
                            if (oldStage !== newStage) {
                                // Show loading state
                                draggedElement.style.opacity = '0.3';
                                
                                try {
                                    const res = await fetch('/api/articles/' + articleId + '/stage', {
                                        method: 'POST',
                                        headers: {
                                            'Content-Type': 'application/json',
                                            'X-User-Id': userId
                                        },
                                        body: JSON.stringify({ stage: newStage })
                                    });
                                    
                                    if (res.ok) {
                                        // Smooth transition
                                        draggedElement.style.transition = 'all 0.3s ease';
                                        setTimeout(() => {
                                            loadKanbanData();
                                        }, 300);
                                    } else {
                                        // Revert on error
                                        draggedElement.style.opacity = '1';
                                        loadKanbanData();
                                    }
                                } catch (e) {
                                    console.error('Error updating stage:', e);
                                    draggedElement.style.opacity = '1';
                                    loadKanbanData();
                                }
                            }
                        }
                        draggedElement = null;
                    });
                });
                
                // Helper function to determine drop position
                function getDragAfterElement(container, y) {
                    const draggableElements = [...container.querySelectorAll('.article-card:not(.dragging)')];
                    
                    return draggableElements.reduce((closest, child) => {
                        const box = child.getBoundingClientRect();
                        const offset = y - box.top - box.height / 2;
                        
                        if (offset < 0 && offset > closest.offset) {
                            return { offset: offset, element: child };
                        } else {
                            return closest;
                        }
                    }, { offset: Number.NEGATIVE_INFINITY }).element;
                }
            }
        }
        
        async function loadListView(stage) {
            if (!userId) return;
            
            currentStage = stage;
            document.querySelectorAll('.tab').forEach(tab => {
                tab.classList.toggle('active', tab.dataset.stage === stage);
            });
            
            try {
                const res = await fetch('/api/articles?stage=' + stage + '&user_id=' + userId);
                const articles = await res.json();
                const container = document.getElementById('list-articles');
                
                if (articles.length === 0) {
                    container.innerHTML = '<div class="empty-state">No articles in this stage</div>';
                    return;
                }
                
                container.innerHTML = articles.map(a => {
                    const favicon = getFaviconUrl(a.url);
                    return '
                        <div class="article-list-item" onclick="window.open(a.url, '_blank')">
                            ' + favicon ? '<img src="' + favicon + '" class="article-favicon" onerror="this.style.display='none'">' : '
                            <div style="flex: 1;">
                                <div class="article-title">' + a.title + '</div>
                                <div class="article-url">' + a.url + '</div>
                            </div>
                            <div class="article-time">' + formatDate(a.created_at) + '</div>
                        </div>
                    ';
                }).join('');
            } catch (e) {
                console.error('Error loading list view:', e);
            }
        }
        
        // Tab listeners for list view
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('tab') && currentView === 'list') {
                loadListView(e.target.dataset.stage);
            }
        });
        
        async function migrateArticles() {
            if (!userId) {
                alert('Please login through LINE first');
                return;
            }
            
            if (confirm('This will claim all unclaimed articles to your account. Continue?')) {
                try {
                    const res = await fetch('/api/migrate?user_id=' + userId);
                    const result = await res.json();
                    if (result.success) {
                        alert('Success! Migrated ' + result.migrated_articles + ' articles to your account.');
                        loadKanbanData();
                    } else {
                        alert('Migration failed: ' + result.message);
                    }
                } catch (e) {
                    console.error('Migration error:', e);
                    alert('Migration failed. Please try again.');
                }
            }
        }
        
        // Team Mode Functions
        async function loadTeamView() {
            try {
                console.log('Loading team view for user:', userId);
                
                if (!userId) {
                    console.error('No user ID available for team view');
                    document.getElementById('teamMembers').innerHTML = '<p>Please login to view teams</p>';
                    return;
                }
                
                // Load user's teams
                const res = await fetch('/api/teams?user_id=' + encodeURIComponent(userId));
                console.log('Team API response status:', res.status);
                
                if (!res.ok) {
                    throw new Error('Failed to load teams: ' + res.status);
                }
                
                const teams = await res.json();
                console.log('Loaded teams:', teams);
                
                const teamSelect = document.getElementById('teamSelect');
                if (!teamSelect) {
                    console.error('Team select element not found');
                    return;
                }
                
                teamSelect.innerHTML = '<option value="">Personal Articles</option>';
                
                teams.forEach(team => {
                    const option = document.createElement('option');
                    option.value = team.id;
                    option.textContent = team.name;
                    teamSelect.appendChild(option);
                });
                
                // Show team management buttons
                document.getElementById('teamMembers').style.display = teams.length > 0 ? 'block' : 'none';
                
                if (teams.length > 0) {
                    teamSelect.value = teams[0].id;
                    await loadTeamArticles();
                } else {
                    console.log('No teams found for user');
                    document.getElementById('teamKanban').style.display = 'none';
                }
            } catch (error) {
                console.error('Error loading teams:', error);
                document.getElementById('teamMembers').innerHTML = '<p style="color: red;">Error loading teams: ' + error.message + '</p>';
            }
        }
        
        async function loadTeamArticles() {
            const teamId = document.getElementById('teamSelect').value;
            
            if (!teamId) {
                document.getElementById('teamMembers').style.display = 'none';
                document.getElementById('teamKanban').style.display = 'none';
                return;
            }
            
            try {
                // Load team details and articles
                const [teamRes, articlesRes] = await Promise.all([
                    fetch('/api/teams/' + teamId),
                    fetch('/api/teams/' + teamId + '/articles')
                ]);
                
                const team = await teamRes.json();
                const articles = await articlesRes.json();
                
                // Show team members and invite code
                document.getElementById('teamMembers').style.display = 'block';
                document.getElementById('inviteCode').textContent = team.invite_code;
                
                // Display team members
                const membersList = document.getElementById('membersList');
                if (team.member_ids && team.member_ids.length > 0) {
                    membersList.innerHTML = '
                        <div class="members-grid">
                            ' + team.member_ids.map(memberId => '
                                <div class="member-card">
                                    <div class="member-avatar">👤</div>
                                    <div class="member-name">' + memberId === team.owner_id ? '👑 Owner' : 'Member</div>
                                </div>
                            ').join('') + '
                        </div>
                        <p>Total members: ' + team.member_ids.length + '</p>
                    ';
                } else {
                    membersList.innerHTML = '<p>No members yet</p>';
                }
                
                // Display articles in kanban
                const stages = ['inbox', 'reading', 'reviewing', 'completed'];
                stages.forEach(stage => {
                    const stageArticles = articles.filter(a => a.stage === stage);
                    const container = document.getElementById('team-' + stage + '-articles');
                    const count = document.getElementById('team-' + stage + '-count');
                    count.textContent = stageArticles.length;
                    
                    if (stageArticles.length === 0) {
                        container.innerHTML = '<div class="empty-state">No articles</div>';
                    } else {
                        container.innerHTML = stageArticles.map(a => renderTeamArticle(a)).join('');
                    }
                });
                
                document.getElementById('teamKanban').style.display = 'grid';
            } catch (error) {
                console.error('Error loading team articles:', error);
            }
        }
        
        function renderTeamArticle(article) {
            const favicon = getFaviconUrl(article.url);
            return '
                <div class="article-card" data-id="' + article.id + '">
                    <div class="article-header">
                        ' + favicon ? '<img src="' + favicon + '" class="article-favicon" onerror="this.style.display='none'">' : '
                        <div class="article-title">' + article.title + '</div>
                    </div>
                    <div class="article-url">' + article.url + '</div>
                    <div class="article-time">' + formatDate(article.created_at) + '</div>
                    <div class="article-owner">By: ' + article.user_name || 'Unknown</div>
                </div>
            ';
        }
        
        async function showCreateTeam() {
            if (!userId) {
                alert('Please login first to create a team');
                return;
            }
            
            const name = prompt('Enter team name:');
            if (name && name.trim()) {
                try {
                    console.log('Creating team:', name, 'for user:', userId);
                    
                    const res = await fetch('/api/teams', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                            'X-User-Id': userId
                        },
                        body: JSON.stringify({ 
                            name: name.trim(), 
                            owner_id: userId,
                            description: 'Team created by ' + localStorage.getItem('lineDisplayName') || 'User'
                        })
                    });
                    
                    const result = await res.json();
                    console.log('Create team result:', result);
                    
                    if (res.ok && result.success) {
                        alert('Team "' + name + '" created successfully!\nTeam ID: ' + result.team_id);
                        await loadTeamView();
                    } else {
                        alert('Failed to create team: ' + (result.error || 'Unknown error'));
                    }
                } catch (error) {
                    console.error('Error creating team:', error);
                    alert('Error creating team: ' + error.message);
                }
            }
        }
        
        async function showJoinTeam() {
            if (!userId) {
                alert('Please login first to join a team');
                return;
            }
            
            const inviteCode = prompt('Enter team invite code:');
            if (inviteCode && inviteCode.trim()) {
                try {
                    console.log('Joining team with code:', inviteCode, 'for user:', userId);
                    
                    const res = await fetch('/api/teams/join', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                            'X-User-Id': userId
                        },
                        body: JSON.stringify({ 
                            invite_code: inviteCode.trim(), 
                            user_id: userId 
                        })
                    });
                    
                    const result = await res.json();
                    console.log('Join team result:', result);
                    
                    if (res.ok && result.success) {
                        alert('Joined team successfully!');
                        await loadTeamView();
                    } else {
                        alert('Failed to join team: ' + (result.error || 'Invalid invite code'));
                    }
                } catch (error) {
                    console.error('Error joining team:', error);
                    alert('Error joining team: ' + error.message);
                }
            }
        }
        
        // Auto-refresh every 30 seconds
        setInterval(() => {
            if (userId) {
                if (currentView === 'team') {
                    loadTeamArticles();
                } else {
                    loadKanbanData();
                }
            }
        }, 30000);
        
        // Keyboard shortcuts for desktop
        if (window.innerWidth >= 1024) {
            document.addEventListener('keydown', (e) => {
                // Check if user is not typing in an input
                if (document.activeElement.tagName === 'INPUT' || 
                    document.activeElement.tagName === 'TEXTAREA') {
                    return;
                }
                
                // Keyboard shortcuts
                switch(e.key) {
                    case '1':
                        if (e.ctrlKey || e.metaKey) {
                            e.preventDefault();
                            toggleView('kanban');
                        }
                        break;
                    case '2':
                        if (e.ctrlKey || e.metaKey) {
                            e.preventDefault();
                            toggleView('list');
                        }
                        break;
                    case '3':
                        if (e.ctrlKey || e.metaKey) {
                            e.preventDefault();
                            toggleView('team');
                        }
                        break;
                    case 'r':
                        if (e.ctrlKey || e.metaKey) {
                            e.preventDefault();
                            loadKanbanData();
                        }
                        break;
                    case '?':
                        // Show keyboard shortcuts help
                        showKeyboardHelp();
                        break;
                }
            });
            
            // Add keyboard help function
            window.showKeyboardHelp = function() {
                const helpDiv = document.createElement('div');
                helpDiv.style.cssText = '
                    position: fixed;
                    top: 50%;
                    left: 50%;
                    transform: translate(-50%, -50%);
                    background: rgba(0, 0, 0, 0.9);
                    color: white;
                    padding: 20px;
                    border-radius: 10px;
                    z-index: 10000;
                    min-width: 300px;
                `;
                
                helpDiv.innerHTML = `
                    <h3 style="margin-top: 0;">⌨️ Keyboard Shortcuts</h3>
                    <div style="margin: 10px 0;">
                        <kbd>Ctrl/Cmd + 1</kbd> - Kanban View
                    </div>
                    <div style="margin: 10px 0;">
                        <kbd>Ctrl/Cmd + 2</kbd> - List View
                    </div>
                    <div style="margin: 10px 0;">
                        <kbd>Ctrl/Cmd + 3</kbd> - Team View
                    </div>
                    <div style="margin: 10px 0;">
                        <kbd>Ctrl/Cmd + R</kbd> - Refresh Data
                    </div>
                    <div style="margin: 10px 0;">
                        <kbd>?</kbd> - Show This Help
                    </div>
                    <button onclick="this.parentElement.remove()" style="
                        background: #007AFF;
                        color: white;
                        border: none;
                        padding: 10px 20px;
                        border-radius: 5px;
                        margin-top: 15px;
                        cursor: pointer;
                        width: 100%;
                    ">Close</button>
                `;
                
                document.body.appendChild(helpDiv);
                
                // Close on ESC or click outside
                const closeHelp = (e) => {
                    if (e.key === 'Escape' || e.target === helpDiv) {
                        helpDiv.remove();
                        document.removeEventListener('keydown', closeHelp);
                    }
                };
                document.addEventListener('keydown', closeHelp);
            };
        }
    </script>
</body>
</html>"""
        
        self.send_response(200)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.send_header('Content-Length', str(len(html.encode())))
        self.end_headers()
        self.wfile.write(html.encode())
    
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
            self.send_header('Content-Length', '2')
            self.end_headers()
            self.wfile.write(b'OK')
            
        except Exception as e:
            logger.error(f"Webhook processing error: {e}")
            self.send_error(500, "Internal server error")
    
    def process_webhook_event(self, event: Dict):
        """Process individual webhook event with command support"""
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
                    
                    # Check for commands
                    if text.startswith('/'):
                        self.handle_command(text, user_id, reply_token)
                        return
                    
                    # Check if it's a URL or contains URLs
                    urls = extract_urls(text)
                    
                    if urls:
                        # Save each URL as an article
                        saved_count = 0
                        for url in urls:
                            logger.info(f"Saving URL: {url} for user: {user_id}")
                            
                            # Auto-categorize the URL
                            category, tags = categorize_url(url)
                            
                            article_id = database.save_article(
                                url=url,
                                title=f"Article from {url.split('/')[2] if '/' in url else url}",
                                user_id=user_id,
                                stage='inbox',
                                category=category,
                                tags=', '.join(tags) if tags else ''
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
                            "text": "📚 Send me a URL to save it!\n\nCommands:\n/help - Show this message\n/stats - View statistics\n/list - Recent articles\n\n📊 Dashboard:\n" + LIFF_URL
                        }]
                        send_line_reply(reply_token, messages)
                
                elif message_type == 'image':
                    # Handle image message
                    user_id = event.get('source', {}).get('userId')
                    reply_token = event.get('replyToken')
                    message_id = message.get('id')
                    
                    # Save image info as an article
                    image_title = f"Image {datetime.now().strftime('%Y-%m-%d %H:%M')}"
                    image_url = f"line://message/{message_id}/content"  # Special URL for LINE images
                    
                    article_id = database.save_article(
                        url=image_url,
                        title=image_title,
                        user_id=user_id,
                        stage='inbox',
                        category='image',
                        tags='line-image'
                    )
                    
                    if article_id:
                        # Send confirmation with image preview
                        flex_msg = {
                            "type": "flex",
                            "altText": "Image saved!",
                            "contents": {
                                "type": "bubble",
                                "hero": {
                                    "type": "image",
                                    "url": f"https://api.line.me/v2/bot/message/{message_id}/content",
                                    "size": "full",
                                    "aspectRatio": "20:13",
                                    "aspectMode": "cover"
                                },
                                "body": {
                                    "type": "box",
                                    "layout": "vertical",
                                    "contents": [
                                        {
                                            "type": "text",
                                            "text": "📸 Image Saved!",
                                            "weight": "bold",
                                            "size": "lg",
                                            "color": "#1DB446"
                                        },
                                        {
                                            "type": "text",
                                            "text": image_title,
                                            "size": "sm",
                                            "color": "#999999",
                                            "margin": "md"
                                        },
                                        {
                                            "type": "text",
                                            "text": "Stage: Inbox",
                                            "size": "sm",
                                            "color": "#666666",
                                            "margin": "sm"
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
                                        }
                                    ]
                                }
                            }
                        }
                        send_line_reply(reply_token, [flex_msg])
                    else:
                        messages = [{
                            "type": "text",
                            "text": "❌ Failed to save image. Please try again."
                        }]
                        send_line_reply(reply_token, messages)
                        
        except Exception as e:
            logger.error(f"Error processing webhook event: {e}")
    
    def handle_command(self, command: str, user_id: str, reply_token: str):
        """Handle bot commands"""
        cmd = command.lower().split()[0]
        
        if cmd == '/help':
            messages = [{
                "type": "text",
                "text": "📚 Article Hub\n\n• Send any URL to save it\n• Send images to save them\n• View your dashboard anytime\n\n📊 Dashboard:\n" + LIFF_URL
            }]
            send_line_reply(reply_token, messages)
        
        else:
            # Unknown command - just show the dashboard URL
            messages = [{
                "type": "text",
                "text": f"📊 View your dashboard:\n{LIFF_URL}"
            }]
            send_line_reply(reply_token, messages)
    
    def serve_api_stats(self):
        """Serve API statistics endpoint"""
        try:
            # Get user_id from query parameters or headers
            parsed_path = urlparse(self.path)
            query = parse_qs(parsed_path.query)
            user_id = query.get('user_id', [None])[0]
            show_all = query.get('show_all', [None])[0]  # Add show_all parameter
            
            # If no user_id in query, try to get from X-User-Id header
            if not user_id:
                user_id = self.headers.get('X-User-Id')
            
            # Require user_id for access
            if not user_id:
                logger.warning("API stats accessed without user_id")
                stats = {
                    'error': 'Authentication required',
                    'total_articles': 0,
                    'by_stage': {'inbox': 0, 'reading': 0, 'reviewing': 0, 'completed': 0},
                    'by_priority': {'high': 0, 'medium': 0, 'low': 0}
                }
                response = json.dumps(stats).encode()
                self.send_response(401)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.send_header('Content-Length', str(len(response)))
                self.end_headers()
                self.wfile.write(response)
                return
            
            # Get user's articles only
            all_articles = []
            docs = database.db.collection('articles').where('user_id', '==', user_id).stream()
            
            for doc in docs:
                article = doc.to_dict()
                all_articles.append(article)
            
            # Calculate statistics
            stats = {
                'total_articles': len(all_articles),
                'by_stage': {'inbox': 0, 'reading': 0, 'reviewing': 0, 'completed': 0},
                'by_priority': {'high': 0, 'medium': 0, 'low': 0}
            }
            
            for article in all_articles:
                stage = article.get('stage', 'inbox')
                if stage in stats['by_stage']:
                    stats['by_stage'][stage] += 1
                
                priority = article.get('priority', 'medium')
                if priority in stats['by_priority']:
                    stats['by_priority'][priority] += 1
            
            logger.info(f"Stats calculated: {stats}")
            
        except Exception as e:
            logger.error(f"Error calculating stats: {e}")
            # Return empty stats on error
            stats = {
                'total_articles': 0,
                'by_stage': {'inbox': 0, 'reading': 0, 'reviewing': 0, 'completed': 0},
                'by_priority': {'high': 0, 'medium': 0, 'low': 0}
            }
        
        response = json.dumps(stats).encode()
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Content-Length', str(len(response)))
        self.end_headers()
        self.wfile.write(response)
    
    def serve_api_articles(self, parsed_path):
        """Serve API articles endpoint"""
        try:
            query = parse_qs(parsed_path.query)
            stage = query.get('stage', ['inbox'])[0]
            user_id = query.get('user_id', [None])[0]
            show_all = query.get('show_all', [None])[0]  # Add show_all parameter
            
            logger.info(f"API articles request: stage={stage}, user_id={user_id}")
            
            # If no user_id in query, try to get from X-User-Id header
            if not user_id:
                user_id = self.headers.get('X-User-Id')
                logger.info(f"Got user_id from header: {user_id}")
            
            # Require user_id for access
            if not user_id:
                logger.warning("API articles accessed without user_id")
                articles = []
                response = json.dumps({'error': 'Authentication required', 'articles': []}).encode()
                self.send_response(401)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.send_header('Content-Length', str(len(response)))
                self.end_headers()
                self.wfile.write(response)
                return
            
            # Get user's articles only
            articles = database.get_articles_by_stage_and_user(stage, user_id)
            logger.info(f"Found {len(articles)} articles for user {user_id} in stage {stage}")
            
            # Convert Firestore timestamps to strings for JSON serialization
            for article in articles:
                if 'created_at' in article and article['created_at']:
                    try:
                        article['created_at'] = article['created_at'].isoformat() if hasattr(article['created_at'], 'isoformat') else str(article['created_at'])
                    except:
                        article['created_at'] = str(article['created_at'])
                
                if 'updated_at' in article and article['updated_at']:
                    try:
                        article['updated_at'] = article['updated_at'].isoformat() if hasattr(article['updated_at'], 'isoformat') else str(article['updated_at'])
                    except:
                        article['updated_at'] = str(article['updated_at'])
            
            logger.info(f"Returning {len(articles)} articles for stage '{stage}'")
            
        except Exception as e:
            logger.error(f"Error getting articles: {e}")
            articles = []
        
        response = json.dumps(articles, default=str).encode()
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Content-Length', str(len(response)))
        self.end_headers()
        self.wfile.write(response)
    
    def serve_api_debug(self):
        """Serve debug information about the database"""
        try:
            # Get all articles
            all_articles = []
            docs = database.db.collection('articles').stream()
            for doc in docs:
                article = doc.to_dict()
                article['id'] = doc.id
                all_articles.append(article)
            
            # Get all users
            all_users = []
            try:
                user_docs = database.db.collection('users').stream()
                for doc in user_docs:
                    user = doc.to_dict()
                    user['id'] = doc.id
                    all_users.append(user)
            except Exception as e:
                logger.warning(f"Could not fetch users: {e}")
            
            debug_info = {
                'database_status': 'connected',
                'total_articles': len(all_articles),
                'total_users': len(all_users),
                'articles_by_stage': {},
                'articles_by_user': {},
                'recent_articles': all_articles[-5:] if all_articles else [],
                'sample_article': all_articles[0] if all_articles else None
            }
            
            # Count by stage
            for article in all_articles:
                stage = article.get('stage', 'unknown')
                debug_info['articles_by_stage'][stage] = debug_info['articles_by_stage'].get(stage, 0) + 1
                
                user_id = article.get('user_id', 'unknown')
                debug_info['articles_by_user'][user_id] = debug_info['articles_by_user'].get(user_id, 0) + 1
            
            logger.info(f"Debug info generated: {len(all_articles)} articles, {len(all_users)} users")
            
        except Exception as e:
            logger.error(f"Error generating debug info: {e}")
            debug_info = {
                'database_status': 'error',
                'error': str(e),
                'total_articles': 0,
                'total_users': 0
            }
        
        response = json.dumps(debug_info, default=str, indent=2).encode()
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Content-Length', str(len(response)))
        self.end_headers()
        self.wfile.write(response)
    
    def serve_api_migrate(self):
        """Migrate orphaned articles to current user"""
        try:
            # Get user_id from query parameters
            parsed_path = urlparse(self.path)
            query = parse_qs(parsed_path.query)
            user_id = query.get('user_id', [None])[0]
            
            if not user_id:
                self.send_error(400, "user_id parameter required")
                return
            
            # Find all articles with no user_id or 'unknown' user_id
            migrated_count = 0
            docs = database.db.collection('articles').stream()
            
            for doc in docs:
                article = doc.to_dict()
                article_user = article.get('user_id')
                
                # Migrate if no user_id, empty string, or 'unknown'
                if not article_user or article_user == 'unknown' or article_user == '':
                    try:
                        database.db.collection('articles').document(doc.id).update({
                            'user_id': user_id,
                            'migrated_at': firestore.SERVER_TIMESTAMP
                        })
                        migrated_count += 1
                        logger.info(f"Migrated article {doc.id} to user {user_id}")
                    except Exception as e:
                        logger.error(f"Failed to migrate article {doc.id}: {e}")
            
            result = {
                'success': True,
                'migrated_articles': migrated_count,
                'user_id': user_id,
                'message': f'Successfully migrated {migrated_count} articles to your account'
            }
            
        except Exception as e:
            logger.error(f"Migration error: {e}")
            result = {
                'success': False,
                'error': str(e),
                'message': 'Migration failed'
            }
        
        response = json.dumps(result).encode()
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Content-Length', str(len(response)))
        self.end_headers()
        self.wfile.write(response)
    
    def handle_api_articles_post(self):
        """Handle POST requests to articles API"""
        try:
            # Parse article ID from path - expecting /api/articles/{id}/stage
            path_parts = self.path.split('/')
            logger.info(f"API POST path parts: {path_parts}")
            
            if len(path_parts) >= 5 and path_parts[1] == 'api' and path_parts[2] == 'articles' and path_parts[4] == 'stage':
                article_id = path_parts[3]
                logger.info(f"Updating article {article_id} stage")
                
                # Read request body
                content_length = int(self.headers.get('Content-Length', 0))
                body = self.rfile.read(content_length)
                data = json.loads(body.decode())
                
                # Get user ID from header
                user_id = self.headers.get('X-User-Id')
                logger.info(f"User ID from header: {user_id}")
                
                # Update stage
                new_stage = data.get('stage')
                logger.info(f"New stage: {new_stage}")
                
                if new_stage and database.update_article_stage(article_id, new_stage):
                    response = json.dumps({'success': True}).encode()
                    self.send_response(200)
                    self.send_header('Content-Type', 'application/json')
                    self.send_header('Access-Control-Allow-Origin', '*')
                    self.send_header('Content-Length', str(len(response)))
                    self.end_headers()
                    self.wfile.write(response)
                else:
                    logger.error(f"Failed to update stage for article {article_id}")
                    self.send_error(400, "Failed to update stage")
            else:
                logger.error(f"Invalid API path: {self.path}")
                self.send_error(404, "Invalid endpoint")
        except Exception as e:
            logger.error(f"Error in handle_api_articles_post: {e}")
            self.send_error(500, str(e))

    def serve_api_debug(self):
        """Serve debug information"""
        try:
            # Get query parameters
            parsed_path = urlparse(self.path)
            query = parse_qs(parsed_path.query)
            user_id = query.get('user_id', [None])[0]
            
            # Get all articles for debugging
            all_articles = []
            user_articles = []
            
            docs = database.db.collection('articles').stream()
            
            for doc in docs:
                article = doc.to_dict()
                article['id'] = doc.id
                # Convert timestamp for JSON
                if 'created_at' in article and article['created_at']:
                    try:
                        # Handle Firestore timestamp
                        if hasattr(article['created_at'], 'isoformat'):
                            article['created_at'] = article['created_at'].isoformat()
                        else:
                            article['created_at'] = str(article['created_at'])
                    except:
                        article['created_at'] = None
                
                if 'updated_at' in article and article['updated_at']:
                    try:
                        if hasattr(article['updated_at'], 'isoformat'):
                            article['updated_at'] = article['updated_at'].isoformat()
                        else:
                            article['updated_at'] = str(article['updated_at'])
                    except:
                        article['updated_at'] = None
                all_articles.append(article)
                
                # Check if this belongs to the user
                if article.get('user_id') == user_id:
                    user_articles.append(article)
            
            # Get unique user_ids
            user_ids = set()
            for article in all_articles:
                uid = article.get('user_id')
                if uid:
                    user_ids.add(str(uid))
            
            debug_info = {
                'total_articles': len(all_articles),
                'user_articles_count': len(user_articles),
                'requested_user_id': user_id,
                'unique_user_ids': list(user_ids),
                'sample_articles': all_articles[:5],
                'user_articles': user_articles[:5]
            }
            
            response = json.dumps(debug_info, indent=2).encode()
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Content-Length', str(len(response)))
            self.end_headers()
            self.wfile.write(response)
            
        except Exception as e:
            logger.error(f"Error in debug endpoint: {e}")
            self.send_error(500, str(e))
    
    def serve_api_migrate(self):
        """Serve migration endpoint"""
        try:
            response = json.dumps({'migrated': 0}).encode()
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Content-Length', str(len(response)))
            self.end_headers()
            self.wfile.write(response)
        except Exception as e:
            logger.error(f"Error in migrate endpoint: {e}")
            self.send_error(500, str(e))
    
    def serve_api_auto_migrate(self):
        """Serve auto-migration GET endpoint"""
        try:
            response = json.dumps({'error': 'Use POST method'}).encode()
            self.send_response(405)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Content-Length', str(len(response)))
            self.end_headers()
            self.wfile.write(response)
        except Exception as e:
            logger.error(f"Error in auto-migrate GET: {e}")
            self.send_error(500, str(e))
    
    def serve_api_test_save(self):
        """Test save endpoint to debug database issues"""
        try:
            # Get user_id from query params
            parsed_path = urlparse(self.path)
            query = parse_qs(parsed_path.query)
            user_id = query.get('user_id', ['test_user'])[0]
            
            # Save a test article
            test_url = f"https://test.com/{datetime.now().timestamp()}"
            article_id = database.save_article(
                url=test_url,
                title="Test Article " + datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                user_id=user_id,
                stage='inbox'
            )
            
            # Verify it was saved
            saved_article = None
            if article_id:
                doc = database.db.collection('articles').document(article_id).get()
                if doc.exists:
                    saved_article = doc.to_dict()
                    saved_article['id'] = article_id
                    # Convert timestamps
                    for field in ['created_at', 'updated_at']:
                        if field in saved_article and saved_article[field]:
                            try:
                                if hasattr(saved_article[field], 'isoformat'):
                                    saved_article[field] = saved_article[field].isoformat()
                                else:
                                    saved_article[field] = str(saved_article[field])
                            except:
                                saved_article[field] = None
            
            response_data = {
                'success': bool(article_id),
                'article_id': article_id,
                'user_id': user_id,
                'test_url': test_url,
                'saved_article': saved_article
            }
            
            response = json.dumps(response_data).encode()
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Content-Length', str(len(response)))
            self.end_headers()
            self.wfile.write(response)
            
        except Exception as e:
            logger.error(f"Error in test save: {e}")
            self.send_error(500, str(e))
    
    def serve_logout(self):
        """Serve logout endpoint with LIFF logout"""
        # Serve a page that logs out from LIFF then redirects
        html = """<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Logging out...</title>
    <script src="https://static.line-scdn.net/liff/edge/2/sdk.js"></script>
</head>
<body>
    <p>Logging out...</p>
    <script>
        // Clear local storage
        localStorage.removeItem('lineUserId');
        localStorage.removeItem('lineDisplayName');
        
        // Initialize LIFF and logout
        liff.init({ liffId: '2007870100-ao8GpgRQ' })
            .then(() => {
                if (liff.isLoggedIn()) {
                    liff.logout();
                }
                // Redirect to home page instead of /login
                window.location.href = '/';
            })
            .catch(() => {
                // Even if LIFF fails, redirect to home
                window.location.href = '/';
            });
    </script>
</body>
</html>"""
        
        self.send_response(200)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.send_header('Content-Length', str(len(html.encode())))
        self.end_headers()
        self.wfile.write(html.encode())  # IMPORTANT: Write the response body!
    
    def serve_api_teams(self):
        """Get user's teams"""
        try:
            query = parse_qs(urlparse(self.path).query)
            user_id = query.get('user_id', [None])[0]
            
            if not user_id:
                self.send_error(400, "User ID required")
                return
            
            teams = database.get_user_teams(user_id)
            
            response = json.dumps(teams, default=str).encode()
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Content-Length', str(len(response)))
            self.end_headers()
            self.wfile.write(response)
            
        except Exception as e:
            logger.error(f"Error getting teams: {e}")
            self.send_error(500, str(e))
    
    def serve_api_team_details(self, parsed_path):
        """Get team details or articles"""
        try:
            path_parts = parsed_path.path.split('/')
            if len(path_parts) < 4:
                self.send_error(404, "Invalid path")
                return
            
            team_id = path_parts[3]
            
            if len(path_parts) > 4 and path_parts[4] == 'articles':
                # Get team articles
                articles = database.get_team_articles(team_id)
                response = json.dumps(articles, default=str).encode()
            else:
                # Get team details
                team_ref = database.db.collection('teams').document(team_id).get()
                if not team_ref.exists:
                    self.send_error(404, "Team not found")
                    return
                
                team_data = team_ref.to_dict()
                team_data['id'] = team_id
                response = json.dumps(team_data, default=str).encode()
            
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Content-Length', str(len(response)))
            self.end_headers()
            self.wfile.write(response)
            
        except Exception as e:
            logger.error(f"Error getting team details: {e}")
            self.send_error(500, str(e))
    
    def handle_api_teams_post(self):
        """Create a new team"""
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            body = json.loads(self.rfile.read(content_length))
            
            name = body.get('name')
            owner_id = body.get('owner_id')
            description = body.get('description', '')
            
            if not name or not owner_id:
                self.send_error(400, "Name and owner_id required")
                return
            
            team_id = database.create_team(name, owner_id, description)
            
            if team_id:
                response = json.dumps({'success': True, 'team_id': team_id}).encode()
                self.send_response(200)
            else:
                response = json.dumps({'success': False, 'error': 'Failed to create team'}).encode()
                self.send_response(500)
            
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Content-Length', str(len(response)))
            self.end_headers()
            self.wfile.write(response)
            
        except Exception as e:
            logger.error(f"Error creating team: {e}")
            self.send_error(500, str(e))
    
    def handle_api_teams_join(self):
        """Join a team using invite code"""
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            body = json.loads(self.rfile.read(content_length))
            
            invite_code = body.get('invite_code')
            user_id = body.get('user_id')
            
            if not invite_code or not user_id:
                self.send_error(400, "Invite code and user_id required")
                return
            
            team_id = database.join_team(user_id, invite_code)
            
            if team_id:
                response = json.dumps({'success': True, 'team_id': team_id}).encode()
                self.send_response(200)
            else:
                response = json.dumps({'success': False, 'error': 'Invalid invite code'}).encode()
                self.send_response(400)
            
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Content-Length', str(len(response)))
            self.end_headers()
            self.wfile.write(response)
            
        except Exception as e:
            logger.error(f"Error joining team: {e}")
            self.send_error(500, str(e))
    
    def handle_api_article_share(self):
        """Share an article with a team"""
        try:
            # Parse article ID from path: /api/articles/{id}/share
            path_parts = self.path.split('/')
            if len(path_parts) < 5:
                self.send_error(404, "Invalid path")
                return
            
            article_id = path_parts[3]
            
            # Get request body
            content_length = int(self.headers.get('Content-Length', 0))
            body = json.loads(self.rfile.read(content_length))
            
            team_id = body.get('team_id')
            if not team_id:
                self.send_error(400, "team_id required")
                return
            
            # Share the article with the team
            success = database.share_article_with_team(article_id, team_id)
            
            if success:
                response = json.dumps({'success': True}).encode()
                self.send_response(200)
            else:
                response = json.dumps({'success': False, 'error': 'Failed to share article'}).encode()
                self.send_response(400)
            
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Content-Length', str(len(response)))
            self.end_headers()
            self.wfile.write(response)
            
        except Exception as e:
            logger.error(f"Error sharing article: {e}")
            self.send_error(500, str(e))
    
    def handle_api_auto_migrate(self):
        """Handle auto-migration POST endpoint"""
        try:
            # Get user ID from header or body
            user_id = self.headers.get('X-User-Id')
            
            if not user_id:
                # Try to get from request body
                content_length = int(self.headers.get('Content-Length', 0))
                if content_length > 0:
                    body = json.loads(self.rfile.read(content_length))
                    user_id = body.get('user_id')
            
            if not user_id:
                response = json.dumps({'error': 'User ID required', 'migrated': 0}).encode()
                self.send_response(400)
            else:
                # Migrate unclaimed articles to this user
                migrated_count = 0
                articles_ref = database.db.collection('articles')
                
                # Find articles without user_id or empty string user_id
                unclaimed_docs = articles_ref.where('user_id', 'in', [None, '', 'None']).limit(50).stream()
                
                for doc in unclaimed_docs:
                    try:
                        doc.reference.update({'user_id': user_id})
                        migrated_count += 1
                    except Exception as e:
                        logger.error(f"Error migrating article {doc.id}: {e}")
                
                logger.info(f"Auto-migrated {migrated_count} articles to user {user_id}")
                response = json.dumps({'migrated': migrated_count}).encode()
                self.send_response(200)
            
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Content-Length', str(len(response)))
            self.end_headers()
            self.wfile.write(response)
            
        except Exception as e:
            logger.error(f"Error in auto-migrate POST: {e}")
            self.send_error(500, str(e))

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