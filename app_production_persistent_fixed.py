#!/usr/bin/env python3
"""
Production-ready Article Intelligence Hub - With Persistent Storage
Uses Google Cloud Storage to persist SQLite database across deployments
"""

import os
import json
import sqlite3
import logging
import hashlib
import secrets
import re
import tempfile
import atexit
from datetime import datetime, timedelta
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs, unquote
import urllib.request
import urllib.error
import subprocess
import threading
import time


# URL Extraction Functions
def extract_urls(text):
    """Extract all URLs from text"""
    urls = []
    
    # Pattern 1: Standard URLs with protocol
    pattern1 = r'https?://(?:[-\w.])+(?::\d+)?(?:[/\w\-._~:?#\[\]@!$&\'()*+,;=%.]*)?'
    urls.extend(re.findall(pattern1, text, re.IGNORECASE))
    
    # Pattern 2: URLs starting with www
    pattern2 = r'(?:^|[\s])(?:www\.)(?:[-\w.])+(?:\.[\w]{2,})(?:[/\w\-._~:?#\[\]@!$&\'()*+,;=%.]*)?'
    www_urls = re.findall(pattern2, text, re.IGNORECASE)
    for url in www_urls:
        url = url.strip()
        if url:
            urls.append(f'https://{url}')
    
    # Pattern 3: Common short URL services
    short_domains = ['bit.ly', 't.co', 'goo.gl', 'tinyurl.com', 'youtu.be', 'lnkd.in']
    for domain in short_domains:
        pattern = rf'(?:https?://)?(?:{re.escape(domain)})/[\w\-]+'
        short_urls = re.findall(pattern, text, re.IGNORECASE)
        for url in short_urls:
            if not url.startswith('http'):
                url = f'https://{url}'
            urls.append(url)
    
    # Pattern 4: Domain names with common TLDs
    tlds = ['com', 'org', 'net', 'edu', 'gov', 'io', 'co', 'ai', 'app', 'dev', 'me']
    tld_pattern = '|'.join(re.escape(tld) for tld in tlds)
    pattern4 = rf'(?:^|[\s])([a-zA-Z0-9][-a-zA-Z0-9]*(?:\.[a-zA-Z0-9][-a-zA-Z0-9]*)*\.(?:{tld_pattern})(?:[/\w\-._~:?#\[\]@!$&\'()*+,;=%.]*)?)'
    
    domain_urls = re.findall(pattern4, text, re.IGNORECASE)
    for url in domain_urls:
        url = url.strip()
        if url and not any(url in u for u in urls):
            full_url = f'https://{url}'
            if full_url not in urls:
                urls.append(full_url)
    
    # Clean and deduplicate
    cleaned = []
    for url in urls:
        url = re.sub(r'[.,;:!?\)\]\}]+$', '', url)
        url = url.strip('\'"')
        try:
            result = urlparse(url)
            if result.scheme and result.netloc and url not in cleaned:
                cleaned.append(url)
        except:
            pass
    
    return cleaned

# Configuration from environment variables
PORT = int(os.environ.get('PORT', 8080))
PROJECT_ID = os.environ.get('GCP_PROJECT', 'secondbrain-app-20250612')
BUCKET_NAME = os.environ.get('GCS_BUCKET', f'{PROJECT_ID}-article-data')
DB_FILENAME = 'articles.db'
DB_PATH = f'/tmp/{DB_FILENAME}'
LINE_CHANNEL_ACCESS_TOKEN = os.environ.get('LINE_CHANNEL_ACCESS_TOKEN', '9JTrTJ3+0lXerYu6HRjq4LNF+3UuDG5IwxfU0S8f5QYMJNai+WU3dgs2U5RfO74YDGGh5B1eAi4DoDxl0lq5CAA/kDkAwfaz2AL/qTEiO3Toiz1pS0nCtRNZKDoY0sI3JIWQucLySxrq7gEf7Rvx/QdB04t89/1O/w1cDnyilFU=')
LINE_CHANNEL_SECRET = os.environ.get('LINE_CHANNEL_SECRET', '85fa3bc67d3b99f12c1e92a32dd3ee17')
LINE_LOGIN_CHANNEL_ID = os.environ.get('LINE_LOGIN_CHANNEL_ID', '2007870100')
LINE_LOGIN_CHANNEL_SECRET = os.environ.get('LINE_LOGIN_CHANNEL_SECRET', 'b97f5738faf8cff53619b1d876bec909')
LIFF_ID = os.environ.get('LIFF_ID', '2007552096-GxP76rNd')
BASE_URL = os.environ.get('BASE_URL', 'https://article-hub-959205905728.asia-northeast1.run.app')

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class CloudStorageManager:
    """Manages database persistence with Google Cloud Storage"""
    
    def __init__(self):
        self.bucket_name = BUCKET_NAME
        self.db_path = DB_PATH
        self.db_filename = DB_FILENAME
        self.last_sync = None
        self.sync_interval = 30  # Sync every 30 seconds
        self.setup_bucket()
        self.download_database()
        self.start_sync_thread()
    
    def setup_bucket(self):
        """Create bucket if it doesn't exist"""
        try:
            # Check if bucket exists
            result = subprocess.run(
                ['gsutil', 'ls', f'gs://{self.bucket_name}'],
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                # Create bucket
                logging.info(f"Creating bucket: {self.bucket_name}")
                subprocess.run(
                    ['gsutil', 'mb', '-p', PROJECT_ID, '-l', 'asia-northeast1', f'gs://{self.bucket_name}'],
                    check=True
                )
                logging.info(f"Bucket created: {self.bucket_name}")
        except Exception as e:
            logging.error(f"Error setting up bucket: {e}")
    
        def download_database(self):
        """Download database from Cloud Storage if it exists and is valid"""
        try:
            logging.info("Checking for existing database in Cloud Storage...")
            
            # First check if cloud database exists
            result = subprocess.run(
                ['gsutil', 'ls', '-l', f'gs://{self.bucket_name}/{self.db_filename}'],
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                logging.info("No database in Cloud Storage yet")
                return
            
            # Parse size from gsutil output
            cloud_size = 0
            try:
                # Output format: "32768  2025-08-03T17:45:37Z  gs://..."
                parts = result.stdout.strip().split()
                if parts:
                    cloud_size = int(parts[0])
            except:
                pass
            
            logging.info(f"Cloud database size: {cloud_size} bytes")
            
            # Download to temp file first
            temp_db = f"{self.db_path}.download"
            result = subprocess.run(
                ['gsutil', '-q', 'cp', f'gs://{self.bucket_name}/{self.db_filename}', temp_db],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                # Verify the downloaded database
                try:
                    conn = sqlite3.connect(temp_db)
                    cursor = conn.cursor()
                    cursor.execute("SELECT COUNT(*) FROM articles")
                    count = cursor.fetchone()[0]
                    conn.close()
                    
                    logging.info(f"Downloaded database has {count} articles")
                    
                    # Use the downloaded database
                    import shutil
                    shutil.move(temp_db, self.db_path)
                    logging.info("Database downloaded and verified from Cloud Storage")
                    
                except Exception as e:
                    logging.error(f"Downloaded database verification failed: {e}")
                    # Clean up bad download
                    try:
                        os.remove(temp_db)
                    except:
                        pass
            else:
                logging.warning(f"Could not download database: {result.stderr}")
                
        except subprocess.TimeoutExpired:
            logging.error("Database download timed out")
        except Exception as e:
            logging.warning(f"Could not download database: {e}")
            logging.info("Will use new database")
    def sync_database(self):
        """Sync database to Cloud Storage periodically"""
        while True:
            time.sleep(self.sync_interval)
            try:
                self.upload_database()
            except Exception as e:
                logging.error(f"Error in sync thread: {e}")
    
    def start_sync_thread(self):
        """Start background thread for periodic syncing"""
        sync_thread = threading.Thread(target=self.sync_database, daemon=True)
        sync_thread.start()
        logging.info("Started database sync thread")
    
    def cleanup(self):
        """Final sync before shutdown"""
        try:
            logging.info("Performing final database sync before shutdown...")
            # Force a sync even if recently synced
            self.upload_database()
            logging.info("Final sync complete")
        except Exception as e:
            logging.error(f"Error in final sync: {e}")

# Initialize storage manager globally
storage_manager = None

class RequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed_path = urlparse(self.path)
        
        routes = {
            '/': self.serve_homepage,
            '/kanban': self.serve_kanban,
            '/login': self.handle_line_login,
            '/callback': self.handle_login_callback,
            '/api/articles': self.serve_articles,
            '/api/user': self.serve_user_info,
            '/api/backup': self.handle_backup,
            '/manifest.json': self.serve_manifest,
            '/service-worker.js': self.serve_service_worker,
            '/health': self.health_check
        }
        
        handler = routes.get(parsed_path.path)
        if handler:
            handler()
        elif parsed_path.path.startswith('/icon'):
            self.serve_icon()
        else:
            self.send_error(404)
    
    def do_POST(self):
        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length).decode('utf-8') if content_length > 0 else ''
        
        parsed_path = urlparse(self.path)
        
        routes = {
            '/webhook': self.handle_line_webhook,
            '/callback': self.handle_line_webhook,
            '/api/articles': self.handle_add_article,
            '/api/articles/update': self.handle_update_article,
            '/api/logout': self.handle_logout,
            '/api/sync': self.handle_manual_sync
        }
        
        handler = routes.get(parsed_path.path)
        if handler:
            if parsed_path.path in ['/webhook', '/callback']:
                handler(post_data)
            elif parsed_path.path in ['/api/logout', '/api/sync']:
                handler()
            else:
                handler(post_data)
        else:
            self.send_error(404)
    
    def handle_manual_sync(self):
        """Handle manual database sync request"""
        try:
            storage_manager.upload_database()
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'success': True, 'message': 'Database synced'}).encode())
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'success': False, 'error': str(e)}).encode())
    
    def handle_backup(self):
        """Provide database download"""
        try:
            with open(DB_PATH, 'rb') as f:
                db_content = f.read()
            
            self.send_response(200)
            self.send_header('Content-Type', 'application/x-sqlite3')
            self.send_header('Content-Disposition', f'attachment; filename="articles_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.db"')
            self.send_header('Content-Length', str(len(db_content)))
            self.end_headers()
            self.wfile.write(db_content)
        except Exception as e:
            self.send_error(500, str(e))
    
    def health_check(self):
        """Health check endpoint"""
        # Trigger a sync on health check
        try:
            storage_manager.upload_database()
        except:
            pass
        
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps({
            'status': 'healthy',
            'last_sync': storage_manager.last_sync.isoformat() if storage_manager.last_sync else None,
            'database_size': os.path.getsize(DB_PATH) if os.path.exists(DB_PATH) else 0
        }).encode())
    
    def handle_line_webhook(self, post_data):
        """Handle LINE webhook events"""
        try:
            events = json.loads(post_data)
            logging.info(f"LINE Webhook received: {events}")
            
            for event in events.get('events', []):
                if event['type'] == 'message' and event['message']['type'] == 'text':
                    user_id = event['source']['userId']
                    message_text = event['message']['text']
                    reply_token = event['replyToken']
                    
                    # Process the message
                    # Extract URLs from message
                    urls = extract_urls(message_text)
                    
                    if urls:
                        # Save all extracted URLs
                        saved_count = 0
                        for url in urls:
                            try:
                                self.save_article_from_line(user_id, url)
                                saved_count += 1
                            except Exception as e:
                                logging.error(f"Failed to save URL {url}: {e}")
                        
                        if saved_count == 1:
                            reply = self.create_flex_message(f'✅ Article saved!', urls[0])
                        elif saved_count > 1:
                            reply = {
                                'type': 'text',
                                'text': f'✅ Saved {saved_count} articles from your message!\n\n' + 
                                       '\n'.join([f'• {url[:50]}{"..." if len(url) > 50 else ""}' for url in urls[:5]]) +
                                       (f'\n... and {len(urls)-5} more' if len(urls) > 5 else ''),
                                'quickReply': {
                                    'items': [
                                        {
                                            'type': 'action',
                                            'action': {
                                                'type': 'uri',
                                                'label': '📊 View in LIFF',
                                                'uri': f'https://liff.line.me/{LIFF_ID}'
                                            }
                                        },
                                        {
                                            'type': 'action',
                                            'action': {
                                                'type': 'message',
                                                'label': '📚 List',
                                                'text': '/list'
                                            }
                                        }
                                    ]
                                }
                            }
                        else:
                            reply = {'type': 'text', 'text': '⚠️ No valid URLs found in your message'}
                    elif message_text.startswith('http'):
                        # Fallback for direct URL (shouldn't normally reach here)
                        self.save_article_from_line(user_id, message_text)
                        reply = self.create_flex_message('✅ Article saved!', message_text)
                    elif message_text == '/help':
                        reply = self.create_help_message()
                    elif message_text == '/stats':
                        reply = self.create_stats_message(user_id)
                    elif message_text == '/list':
                        reply = self.create_articles_list(user_id)
                    elif message_text == '/backup':
                        reply = self.create_backup_message()
                    else:
                        reply = self.create_quick_reply_message()
                    
                    self.send_line_reply(reply_token, reply)
            
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'success': True}).encode())
            
        except Exception as e:
            logging.error(f"Webhook error: {e}")
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'success': False}).encode())
    
    def create_backup_message(self):
        """Create backup information message"""
        try:
            db_size = os.path.getsize(DB_PATH) / 1024  # Size in KB
            last_sync = storage_manager.last_sync.strftime('%Y-%m-%d %H:%M:%S') if storage_manager.last_sync else 'Never'
            
            # Get article count
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM articles")
            article_count = cursor.fetchone()[0]
            conn.close()
            
            return {
                'type': 'text',
                'text': f'''💾 Database Status
                
Articles: {article_count}
Size: {db_size:.1f} KB
Last Sync: {last_sync}

Your data is automatically backed up to Google Cloud Storage every 30 seconds and persists across updates!

Download backup: {BASE_URL}/api/backup'''
            }
        except Exception as e:
            return {'type': 'text', 'text': f'Error getting backup info: {e}'}
    
    def create_flex_message(self, title, url):
        """Create a flex message for article saved"""
        return {
            'type': 'flex',
            'altText': title,
            'contents': {
                'type': 'bubble',
                'hero': {
                    'type': 'box',
                    'layout': 'vertical',
                    'contents': [
                        {
                            'type': 'text',
                            'text': '📚 Article Intelligence Hub',
                            'weight': 'bold',
                            'size': 'lg',
                            'color': '#667eea'
                        }
                    ],
                    'backgroundColor': '#f7fafc',
                    'paddingAll': '20px'
                },
                'body': {
                    'type': 'box',
                    'layout': 'vertical',
                    'contents': [
                        {
                            'type': 'text',
                            'text': title,
                            'weight': 'bold',
                            'size': 'xl',
                            'wrap': True
                        },
                        {
                            'type': 'text',
                            'text': self.extract_title_from_url(url),
                            'size': 'md',
                            'color': '#666666',
                            'margin': 'md',
                            'wrap': True
                        },
                        {
                            'type': 'text',
                            'text': '💾 Data saved persistently!',
                            'size': 'sm',
                            'color': '#34d399',
                            'margin': 'md'
                        }
                    ]
                },
                'footer': {
                    'type': 'box',
                    'layout': 'vertical',
                    'spacing': 'sm',
                    'contents': [
                        {
                            'type': 'button',
                            'action': {
                                'type': 'uri',
                                'label': '📖 Open Article',
                                'uri': url
                            },
                            'style': 'primary',
                            'color': '#667eea'
                        },
                        {
                            'type': 'button',
                            'action': {
                                'type': 'uri',
                                'label': '📊 View Dashboard',
                                'uri': 'https://liff.line.me/2007552096-GxP76rNd'
                            },
                            'style': 'secondary'
                        }
                    ]
                }
            }
        }
    
    def create_quick_reply_message(self):
        """Create quick reply message"""
        return {
            'type': 'text',
            'text': '📚 Send me a URL to save it, or use the menu below:',
            'quickReply': {
                'items': [
                    {
                        'type': 'action',
                        'action': {
                            'type': 'message',
                            'label': '📊 Stats',
                            'text': '/stats'
                        }
                    },
                    {
                        'type': 'action',
                        'action': {
                            'type': 'message',
                            'label': '📚 List',
                            'text': '/list'
                        }
                    },
                    {
                        'type': 'action',
                        'action': {
                            'type': 'uri',
                            'label': '🎯 Dashboard',
                            'uri': 'https://liff.line.me/2007552096-GxP76rNd'
                        }
                    },
                    {
                        'type': 'action',
                        'action': {
                            'type': 'message',
                            'label': '💾 Backup',
                            'text': '/backup'
                        }
                    }
                ]
            }
        }
    
    def create_help_message(self):
        """Create help message"""
        return {
            'type': 'text',
            'text': f'''📚 Article Intelligence Hub - Help

Commands:
• Send any URL - Save article
• /list - Show recent articles  
• /stats - View statistics
• /backup - Database status
• /help - Show this help

Features:
• 🎯 Kanban board for progress tracking
• 📊 Smart categorization
• 🔍 Quick access to saved articles
• 📱 Mobile optimized interface
• 💾 Persistent cloud storage

Access dashboard: https://liff.line.me/2007552096-GxP76rNd'''
        }
    
    def create_stats_message(self, user_id):
        """Create statistics message"""
        stats = self.get_user_stats(user_id)
        return {
            'type': 'text',
            'text': f'''📊 Your Statistics

Total Articles: {stats['total']}
├─ 📥 Inbox: {stats['inbox']}
├─ 📖 Reading: {stats['reading']}
├─ 📝 Reviewing: {stats['reviewing']}
└─ ✅ Completed: {stats['completed']}

Categories:
{stats['categories_text']}

Keep learning! 🚀'''
        }
    
    def create_articles_list(self, user_id):
        """Create articles list message"""
        articles = self.get_recent_articles(user_id, 5)
        if not articles:
            return {'type': 'text', 'text': '📚 No articles saved yet.\nSend me a URL to get started!'}
        
        articles_text = '📚 Recent Articles:\n\n'
        for i, article in enumerate(articles, 1):
            title = article['title'][:30] + '...' if len(article['title']) > 30 else article['title']
            articles_text += f"{i}. {title}\n   📁 {article['category']} | {article['stage']}\n\n"
        
        return {'type': 'text', 'text': articles_text}
    
    def send_line_reply(self, reply_token, message):
        """Send reply via LINE API"""
        try:
            url = 'https://api.line.me/v2/bot/message/reply'
            headers = {
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {LINE_CHANNEL_ACCESS_TOKEN}'
            }
            
            data = {
                'replyToken': reply_token,
                'messages': [message]
            }
            
            req = urllib.request.Request(
                url,
                data=json.dumps(data).encode('utf-8'),
                headers=headers,
                method='POST'
            )
            
            with urllib.request.urlopen(req) as response:
                logging.info(f"LINE reply sent: {response.status}")
        except Exception as e:
            logging.error(f"Error sending LINE reply: {e}")
    
    def save_article_from_line(self, user_id, url):
        """Save article from LINE message"""
        title = self.extract_title_from_url(url)
        category = self.detect_category(url)
        save_article(user_id, url, title, category)
        logging.info(f"Article saved from LINE: {url}")
        # Immediately sync to cloud after saving
        try:
            storage_manager.upload_database()
            logging.info(f"Database synced after saving article")
        except Exception as e:
            logging.error(f"Failed to sync after save: {e}")
    
    def get_user_stats(self, user_id):
        """Get user statistics"""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN stage = 'inbox' THEN 1 ELSE 0 END) as inbox,
                SUM(CASE WHEN stage = 'reading' THEN 1 ELSE 0 END) as reading,
                SUM(CASE WHEN stage = 'reviewing' THEN 1 ELSE 0 END) as reviewing,
                SUM(CASE WHEN stage = 'completed' THEN 1 ELSE 0 END) as completed
            FROM articles
            WHERE user_id = ?
        ''', (user_id,))
        
        stats = cursor.fetchone()
        
        cursor.execute('''
            SELECT category, COUNT(*) as count
            FROM articles
            WHERE user_id = ?
            GROUP BY category
            ORDER BY count DESC
            LIMIT 5
        ''', (user_id,))
        
        categories = cursor.fetchall()
        conn.close()
        
        categories_text = '\n'.join([f"• {cat}: {count}" for cat, count in categories]) if categories else 'No categories yet'
        
        return {
            'total': stats[0] or 0,
            'inbox': stats[1] or 0,
            'reading': stats[2] or 0,
            'reviewing': stats[3] or 0,
            'completed': stats[4] or 0,
            'categories_text': categories_text
        }
    
    def get_recent_articles(self, user_id, limit=5):
        """Get recent articles for user"""
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM articles
            WHERE user_id = ?
            ORDER BY created_at DESC
            LIMIT ?
        ''', (user_id, limit))
        
        articles = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return articles
    
    def handle_line_login(self):
        """Handle LINE Login initiation"""
        state = secrets.token_urlsafe(32)
        nonce = secrets.token_urlsafe(32)
        
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
            
            # Create session
            session_token = secrets.token_urlsafe(32)
            save_session(session_token, user_id)
            
            # Redirect to kanban
            self.send_response(302)
            self.send_header('Location', '/kanban')
            self.send_header('Set-Cookie', f'session={session_token}; HttpOnly; Secure; SameSite=Lax; Max-Age=2592000')
            self.end_headers()
            
        except Exception as e:
            logging.error(f"Login callback error: {e}")
            self.send_error(500, 'Login failed')
    
    def handle_logout(self):
        """Handle logout"""
        self.send_response(302)
        self.send_header('Location', '/')
        self.send_header('Set-Cookie', 'session=; HttpOnly; Secure; SameSite=Lax; Max-Age=0')
        self.end_headers()
    
    def handle_add_article(self, post_data):
        """Handle adding article via API"""
        try:
            data = json.loads(post_data)
            url = data.get('url')
            
            if not url:
                raise ValueError('URL is required')
            
            # Get user from session
            cookie = self.headers.get('Cookie', '')
            user_id = None
            if 'session=' in cookie:
                session_token = cookie.split('session=')[1].split(';')[0]
                user = get_user_by_session(session_token)
                if user:
                    user_id = user['user_id']
            
            # Use demo user if not logged in
            if not user_id:
                user_id = 'demo_user'
            
            title = self.extract_title_from_url(url)
            category = self.detect_category(url)
            
            save_article(user_id, url, title, category)
            
            # Trigger sync after adding article
            storage_manager.upload_database()
            
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'success': True}).encode())
            
        except Exception as e:
            self.send_response(400)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'success': False, 'error': str(e)}).encode())
    
    def handle_update_article(self, post_data):
        """Handle updating article stage"""
        try:
            data = json.loads(post_data)
            article_id = data.get('id')
            stage = data.get('stage')
            
            if not article_id or not stage:
                raise ValueError('Article ID and stage are required')
            
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE articles
                SET stage = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (stage, article_id))
            
            if stage == 'completed':
                cursor.execute('''
                    UPDATE articles
                    SET completed_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                ''', (article_id,))
            
            conn.commit()
            conn.close()
            
            # Trigger sync after update
            storage_manager.upload_database()
            
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'success': True}).encode())
            
        except Exception as e:
            self.send_response(400)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'success': False, 'error': str(e)}).encode())
    
    def serve_homepage(self):
        """Serve homepage with login"""
        html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Article Intelligence Hub</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
        }}
        .container {{
            text-align: center;
            padding: 40px;
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            max-width: 500px;
            margin: 20px;
        }}
        h1 {{
            color: #333;
            margin-bottom: 20px;
            font-size: 2.5em;
        }}
        .subtitle {{
            color: #666;
            margin-bottom: 40px;
            font-size: 1.2em;
        }}
        .features {{
            text-align: left;
            margin: 30px 0;
        }}
        .feature {{
            padding: 10px;
            margin: 10px 0;
            background: #f7fafc;
            border-radius: 10px;
        }}
        .login-btn {{
            display: inline-block;
            padding: 15px 40px;
            background: #06c755;
            color: white;
            text-decoration: none;
            border-radius: 50px;
            font-size: 1.2em;
            font-weight: bold;
            transition: all 0.3s;
            margin: 10px;
        }}
        .login-btn:hover {{
            background: #05a947;
            transform: translateY(-2px);
            box-shadow: 0 10px 20px rgba(6, 199, 85, 0.3);
        }}
        .guest-btn {{
            background: #667eea;
        }}
        .guest-btn:hover {{
            background: #5469d4;
            box-shadow: 0 10px 20px rgba(102, 126, 234, 0.3);
        }}
        .status {{
            margin-top: 20px;
            padding: 10px;
            background: #e6fffa;
            border-radius: 10px;
            color: #047857;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>📚 Article Intelligence Hub</h1>
        <p class="subtitle">Your smart article manager with LINE integration</p>
        
        <div class="features">
            <div class="feature">🎯 Kanban board for article progress tracking</div>
            <div class="feature">💬 Save articles via LINE chat</div>
            <div class="feature">📊 Smart categorization</div>
            <div class="feature">📱 Mobile optimized interface</div>
            <div class="feature">💾 Persistent cloud storage</div>
        </div>
        
        <a href="/login" class="login-btn">Login with LINE</a>
        <a href="/kanban" class="login-btn guest-btn">Guest Mode</a>
        
        <div class="status">
            ✅ Data is persistently stored in Google Cloud Storage
        </div>
    </div>
</body>
</html>'''
        
        self.send_response(200)
        self.send_header('Content-Type', 'text/html')
        self.end_headers()
        self.wfile.write(html.encode())
    
    def serve_kanban(self):
        """Serve the Kanban board interface"""
        # Check if user is logged in
        cookie = self.headers.get('Cookie', '')
        session_token = None
        user = None
        
        if 'session=' in cookie:
            session_token = cookie.split('session=')[1].split(';')[0]
            user = get_user_by_session(session_token)
        
        # Get user info for display
        user_display = json.dumps(user) if user else 'null'
        
        html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>📚 Article Kanban Board</title>
    
    <!-- PWA Meta Tags -->
    <meta name="theme-color" content="#667eea">
    <meta name="apple-mobile-web-app-capable" content="yes">
    <link rel="manifest" href="/manifest.json">
    
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 10px;
        }}
        
        .header {{
            background: rgba(255, 255, 255, 0.98);
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
        
        .user-info {{
            display: flex;
            align-items: center;
            gap: 10px;
        }}
        
        .user-avatar {{
            width: 35px;
            height: 35px;
            border-radius: 50%;
        }}
        
        .add-article {{
            background: white;
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 20px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        
        .add-form {{
            display: flex;
            gap: 10px;
        }}
        
        .add-input {{
            flex: 1;
            padding: 12px;
            border: 2px solid #e5e7eb;
            border-radius: 8px;
            font-size: 14px;
        }}
        
        .add-btn {{
            padding: 12px 24px;
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: white;
            border: none;
            border-radius: 8px;
            font-weight: 600;
            cursor: pointer;
        }}
        
        .kanban-board {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 15px;
            margin-bottom: 80px;
        }}
        
        .kanban-column {{
            background: rgba(255, 255, 255, 0.98);
            border-radius: 12px;
            padding: 15px;
            min-height: 400px;
        }}
        
        .column-header {{
            font-weight: 600;
            font-size: 16px;
            margin-bottom: 15px;
            padding: 10px;
            border-radius: 8px;
            text-align: center;
        }}
        
        .column-inbox {{ background: linear-gradient(135deg, #fbbf24, #f59e0b); color: white; }}
        .column-reading {{ background: linear-gradient(135deg, #60a5fa, #3b82f6); color: white; }}
        .column-reviewing {{ background: linear-gradient(135deg, #a78bfa, #8b5cf6); color: white; }}
        .column-completed {{ background: linear-gradient(135deg, #34d399, #10b981); color: white; }}
        
        .articles-container {{
            min-height: 300px;
            padding: 5px;
        }}
        
        .article-card {{
            background: white;
            border-radius: 10px;
            padding: 15px;
            margin-bottom: 10px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
            cursor: move;
            transition: all 0.3s;
        }}
        
        .article-card:hover {{
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        }}
        
        .article-card.dragging {{
            opacity: 0.5;
            transform: rotate(5deg);
        }}
        
        .article-title {{
            font-weight: 600;
            margin-bottom: 8px;
            color: #1f2937;
        }}
        
        .article-meta {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-top: 10px;
        }}
        
        .article-category {{
            background: #f3f4f6;
            padding: 4px 10px;
            border-radius: 12px;
            font-size: 12px;
            color: #6b7280;
        }}
        
        .article-actions {{
            display: flex;
            gap: 8px;
        }}
        
        .action-btn {{
            padding: 6px;
            background: transparent;
            border: none;
            cursor: pointer;
            font-size: 16px;
            transition: transform 0.2s;
        }}
        
        .action-btn:hover {{
            transform: scale(1.2);
        }}
        
        .drop-zone {{
            min-height: 100px;
            border: 2px dashed transparent;
            border-radius: 8px;
            transition: all 0.3s;
        }}
        
        .drop-zone.drag-over {{
            border-color: #667eea;
            background: rgba(102, 126, 234, 0.1);
        }}
        
        /* Mobile optimized */
        @media (max-width: 768px) {{
            body {{
                padding: 5px;
            }}
            
            .header {{
                flex-direction: column;
                gap: 10px;
                text-align: center;
                padding: 10px;
                margin-bottom: 10px;
            }}
            
            .add-article {{
                padding: 10px;
                margin-bottom: 10px;
            }}
            
            .add-form {{
                flex-direction: column;
            }}
            
            .add-input {{
                width: 100%;
            }}
            
            .kanban-board {{
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 8px;
                padding: 5px;
                min-height: calc(100vh - 200px);
            }}
            
            .kanban-column {{
                width: 100%;
                min-height: 200px;
                max-height: calc(50vh - 100px);
                overflow-y: auto;
                -webkit-overflow-scrolling: touch;
            }}
            
            .column-header {{
                position: sticky;
                top: 0;
                z-index: 10;
                background: inherit;
            }}
            
            .articles-container {{
                min-height: 200px;
                max-height: calc(100vh - 300px);
                overflow-y: auto;
                padding-bottom: 20px;
            }}
            
            .article-card {{
                touch-action: none;
                -webkit-user-select: none;
                user-select: none;
            }}
        }}
    </style>
</head>
<body>
    <div class="header">
        <div class="logo">📚 Article Intelligence Hub</div>
        <div class="user-info">
            <span id="userDisplay"></span>
            <a href="/login" style="padding: 8px 16px; background: #00B900; color: white; border-radius: 20px; text-decoration: none; font-weight: 500;">Login</a>
        </div>
    </div>
    
    <div class="add-article">
        <form class="add-form" onsubmit="addArticle(event)">
            <input type="url" class="add-input" id="urlInput" placeholder="Paste article URL here..." required>
            <button type="submit" class="add-btn">Add Article</button>
        </form>
    </div>
    
    <div class="kanban-board">
        <div class="kanban-column">
            <div class="column-header column-inbox">📥 Inbox</div>
            <div class="articles-container drop-zone" data-stage="inbox"></div>
        </div>
        
        <div class="kanban-column">
            <div class="column-header column-reading">📖 Reading</div>
            <div class="articles-container drop-zone" data-stage="reading"></div>
        </div>
        
        <div class="kanban-column">
            <div class="column-header column-reviewing">📝 Reviewing</div>
            <div class="articles-container drop-zone" data-stage="reviewing"></div>
        </div>
        
        <div class="kanban-column">
            <div class="column-header column-completed">✅ Completed</div>
            <div class="articles-container drop-zone" data-stage="completed"></div>
        </div>
    </div>
    
    <script>
        const userData = {user_display};
        let articles = [];
        let draggedElement = null;
        
        // Display user info
        if (userData) {{
            document.getElementById('userDisplay').innerHTML = `
                <img src="${{userData.picture_url}}" class="user-avatar">
                <span>${{userData.display_name}}</span>
            `;
        }}
        
        // Load articles
        async function loadArticles() {{
            try {{
                const response = await fetch('/api/articles');
                const data = await response.json();
                articles = data.articles || [];
                renderKanban();
            }} catch (error) {{
                console.error('Error loading articles:', error);
            }}
        }}
        
        // Render Kanban board
        function renderKanban() {{
            const stages = ['inbox', 'reading', 'reviewing', 'completed'];
            
            stages.forEach(stage => {{
                const container = document.querySelector(`[data-stage="${{stage}}"]`);
                container.innerHTML = '';
                
                const stageArticles = articles.filter(a => a.stage === stage);
                stageArticles.forEach(article => {{
                    const card = createArticleCard(article);
                    container.appendChild(card);
                }});
            }});
        }}
        
        // Create article card
        function createArticleCard(article) {{
            const card = document.createElement('div');
            card.className = 'article-card';
            card.draggable = true;
            card.dataset.articleId = article.id;
            
            card.innerHTML = `
                <div class="article-title">${{article.title || 'Untitled'}}</div>
                <div class="article-meta">
                    <span class="article-category">${{article.category || 'General'}}</span>
                    <div class="article-actions">
                        <button class="action-btn" onclick="copyUrl('${{article.url}}', this)">📋</button>
                        <button class="action-btn" onclick="window.open('${{article.url}}', '_blank')">🔗</button>
                    </div>
                </div>
            `;
            
            // Drag events
            card.addEventListener('dragstart', handleDragStart);
            card.addEventListener('dragend', handleDragEnd);
            
            // Enable touch drag for mobile
            enableTouchDrag(card);
            
            return card;
        }}
        
        // Drag and drop handlers (desktop and mobile)
        function handleDragStart(e) {{
            draggedElement = e.target;
            e.target.classList.add('dragging');
            
            // For mobile
            if (e.type === 'touchstart') {{
                e.preventDefault();
                const touch = e.touches[0];
                e.target.style.position = 'fixed';
                e.target.style.zIndex = '1000';
                moveAt(touch.pageX, touch.pageY, e.target);
            }}
        }}
        
        function handleDragEnd(e) {{
            if (e.target) {{
                e.target.classList.remove('dragging');
                e.target.style.position = '';
                e.target.style.zIndex = '';
            }}
        }}
        
        function moveAt(pageX, pageY, element) {{
            element.style.left = pageX - element.offsetWidth / 2 + 'px';
            element.style.top = pageY - element.offsetHeight / 2 + 'px';
        }}
        
        // Enable touch drag and drop
        function enableTouchDrag(card) {{
            let currentDroppable = null;
            let ghost = null;
            let initialX = 0;
            let initialY = 0;
            
            card.addEventListener('touchstart', function(e) {{
                const touch = e.touches[0];
                draggedElement = card;
                card.classList.add('dragging');
                
                // Store initial position
                initialX = touch.pageX;
                initialY = touch.pageY;
                
                // Create ghost element for visual feedback
                ghost = card.cloneNode(true);
                ghost.style.position = 'fixed';
                ghost.style.zIndex = '9999';
                ghost.style.opacity = '0.8';
                ghost.style.pointerEvents = 'none';
                ghost.style.width = card.offsetWidth + 'px';
                ghost.id = 'drag-ghost';
                document.body.appendChild(ghost);
                
                // Position ghost at touch point
                ghost.style.left = (touch.pageX - card.offsetWidth / 2) + 'px';
                ghost.style.top = (touch.pageY - card.offsetHeight / 2) + 'px';
            }}, {{passive: false}});
            
            card.addEventListener('touchmove', function(e) {{
                if (!draggedElement || !ghost) return;
                e.preventDefault();
                
                const touch = e.touches[0];
                
                // Move ghost with touch
                ghost.style.left = (touch.pageX - ghost.offsetWidth / 2) + 'px';
                ghost.style.top = (touch.pageY - ghost.offsetHeight / 2) + 'px';
                
                // Find droppable element under touch point
                ghost.style.display = 'none';
                const elemBelow = document.elementFromPoint(touch.pageX, touch.pageY);
                ghost.style.display = 'block';
                
                const droppableBelow = elemBelow?.closest('.drop-zone');
                
                if (currentDroppable !== droppableBelow) {{
                    if (currentDroppable) {{
                        currentDroppable.classList.remove('drag-over');
                    }}
                    currentDroppable = droppableBelow;
                    if (currentDroppable) {{
                        currentDroppable.classList.add('drag-over');
                    }}
                }}
            }}, {{passive: false}});
            
            card.addEventListener('touchend', async function(e) {{
                if (!draggedElement) return;
                
                const touch = e.changedTouches[0];
                const deltaX = Math.abs(touch.pageX - initialX);
                const deltaY = Math.abs(touch.pageY - initialY);
                
                // Remove ghost
                if (ghost) {{
                    ghost.remove();
                    ghost = null;
                }}
                
                card.classList.remove('dragging');
                
                // Only process as drag if moved more than 10px
                if (deltaX > 10 || deltaY > 10) {{
                    if (currentDroppable && currentDroppable !== card.parentElement) {{
                        currentDroppable.classList.remove('drag-over');
                        const newStage = currentDroppable.dataset.stage;
                        const articleId = draggedElement.dataset.articleId;
                        
                        // Update article stage
                        await updateArticleStage(articleId, newStage);
                        
                        // Move card to new column
                        currentDroppable.appendChild(draggedElement);
                        
                        // Update stats
                        updateStats();
                    }}
                }}
                
                // Clean up
                if (currentDroppable) {{
                    currentDroppable.classList.remove('drag-over');
                }}
                
                draggedElement = null;
                currentDroppable = null;
            }}, {{passive: false}});
        }}
        
        // Setup drop zones
        document.querySelectorAll('.drop-zone').forEach(zone => {{
            zone.addEventListener('dragover', e => {{
                e.preventDefault();
                zone.classList.add('drag-over');
            }});
            
            zone.addEventListener('dragleave', () => {{
                zone.classList.remove('drag-over');
            }});
            
            zone.addEventListener('drop', async e => {{
                e.preventDefault();
                zone.classList.remove('drag-over');
                
                if (draggedElement) {{
                    const articleId = draggedElement.dataset.articleId;
                    const newStage = zone.dataset.stage;
                    
                    zone.appendChild(draggedElement);
                    
                    // Update in database
                    await updateArticleStage(articleId, newStage);
                }}
            }});
        }});
        
        // Update article stage
        async function updateArticleStage(articleId, stage) {{
            try {{
                await fetch('/api/articles/update', {{
                    method: 'POST',
                    headers: {{ 'Content-Type': 'application/json' }},
                    body: JSON.stringify({{ id: articleId, stage: stage }})
                }});
                updateStats();
            }} catch (error) {{
                console.error('Error updating article:', error);
            }}
        }}
        
        // Update stats display
        function updateStats() {{
            // Recalculate stats from DOM
            const stats = {{
                inbox: document.querySelectorAll('.drop-zone[data-stage="inbox"] .article-card').length,
                reading: document.querySelectorAll('.drop-zone[data-stage="reading"] .article-card').length,
                reviewing: document.querySelectorAll('.drop-zone[data-stage="reviewing"] .article-card').length,
                completed: document.querySelectorAll('.drop-zone[data-stage="completed"] .article-card').length
            }};
            
            // Update column counts
            Object.keys(stats).forEach(stage => {{
                const counter = document.querySelector(`.drop-zone[data-stage="${{stage}}"]`)?.parentElement?.querySelector('.column-count');
                if (counter) {{
                    counter.textContent = stats[stage];
                }}
            }});
            
            // Update stats container if exists
            const statsContainer = document.querySelector('.stats-container');
            if (statsContainer) {{
                statsContainer.innerHTML = `
                    <div class="stat-card">
                        <div class="stat-value">${{stats.inbox}}</div>
                        <div class="stat-label">📥 Inbox</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-value">${{stats.reading}}</div>
                        <div class="stat-label">📖 Reading</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-value">${{stats.reviewing}}</div>
                        <div class="stat-label">📝 Reviewing</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-value">${{stats.completed}}</div>
                        <div class="stat-label">✅ Completed</div>
                    </div>
                `;
            }}
        }}
        
        // Add article
        async function addArticle(event) {{
            event.preventDefault();
            const url = document.getElementById('urlInput').value;
            
            try {{
                const response = await fetch('/api/articles', {{
                    method: 'POST',
                    headers: {{ 'Content-Type': 'application/json' }},
                    body: JSON.stringify({{ url: url }})
                }});
                
                if (response.ok) {{
                    document.getElementById('urlInput').value = '';
                    loadArticles();
                }}
            }} catch (error) {{
                console.error('Error adding article:', error);
            }}
        }}
        
        // Copy URL
        function copyUrl(url, button) {{
            navigator.clipboard.writeText(url).then(() => {{
                button.textContent = '✅';
                setTimeout(() => {{ button.textContent = '📋'; }}, 2000);
            }});
        }}
        
        // Load articles on page load
        loadArticles();
        
        // Refresh every 30 seconds
        setInterval(loadArticles, 30000);
    </script>
</body>
</html>'''
        
        self.send_response(200)
        self.send_header('Content-Type', 'text/html')
        self.end_headers()
        self.wfile.write(html.encode())
    
    def serve_articles(self):
        """Serve articles JSON"""
        cookie = self.headers.get('Cookie', '')
        user_id = None
        
        if 'session=' in cookie:
            session_token = cookie.split('session=')[1].split(';')[0]
            user = get_user_by_session(session_token)
            if user:
                user_id = user['user_id']
        
        # Use demo mode if not logged in
        if not user_id:
            user_id = '%'  # This will match all articles in demo mode
        
        articles = get_user_articles(user_id)
        
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(articles).encode())
    
    def serve_user_info(self):
        """Serve user info"""
        cookie = self.headers.get('Cookie', '')
        user = None
        
        if 'session=' in cookie:
            session_token = cookie.split('session=')[1].split(';')[0]
            user = get_user_by_session(session_token)
        
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps({'user': user}).encode())
    
    def serve_manifest(self):
        """Serve PWA manifest"""
        manifest = {
            "name": "Article Intelligence Hub",
            "short_name": "ArticleHub",
            "description": "Smart article management with persistent storage",
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
    
    def extract_title_from_url(self, url):
        """Extract title from URL"""
        title = re.sub(r'^https?://(www\.)?', '', url)
        title = title.split('?')[0].split('#')[0]
        parts = title.split('/')
        if len(parts) > 1 and parts[-1]:
            title = parts[-1].replace('-', ' ').replace('_', ' ').title()
        else:
            title = parts[0].split('.')[0].title()
        return title[:100]
    
    def detect_category(self, url):
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

# Database functions
def initialize_database():
    """Initialize database with all tables"""
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
    
    # Articles table with Kanban stages
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
            source TEXT DEFAULT 'web',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            completed_at TIMESTAMP,
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
    
    # Use LIKE for demo mode
    if user_id == '%':
        cursor.execute('''
            SELECT * FROM articles
            ORDER BY created_at DESC
            LIMIT 100
        ''')
    else:
        cursor.execute('''
            SELECT * FROM articles
            WHERE user_id = ?
            ORDER BY created_at DESC
            LIMIT 100
        ''', (user_id,))
    
    articles = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    # Clean titles for JavaScript
    for article in articles:
        if article.get('title'):
            article['title'] = ' '.join(article['title'].split())
    
    return articles

def main():
    """Main entry point"""
    global storage_manager
    
    print(f"\n{'='*60}")
    print("🚀 Article Intelligence Hub - With Persistent Storage")
    print(f"{'='*60}")
    print(f"Port: {PORT}")
    print(f"Base URL: {BASE_URL}")
    print(f"Database: {DB_PATH}")
    print(f"Cloud Storage: gs://{BUCKET_NAME}")
    print(f"LIFF ID: {LIFF_ID}")
    print(f"Webhook: {BASE_URL}/webhook")
    print(f"{'='*60}\n")
    
    # Initialize storage manager
    storage_manager = CloudStorageManager()
    
    # Initialize database
    initialize_database()
    
    # Register cleanup on exit
    atexit.register(storage_manager.cleanup)
    
    # Start server
    server = HTTPServer(('0.0.0.0', PORT), RequestHandler)
    print(f"Server running on http://0.0.0.0:{PORT}")
    print(f"Webhook endpoint: {BASE_URL}/webhook")
    print(f"Kanban board: {BASE_URL}/kanban")
    print(f"💾 Persistent storage enabled with auto-sync every 30 seconds")
    server.serve_forever()

if __name__ == '__main__':
    main()