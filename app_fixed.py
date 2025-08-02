import os
import logging
import sqlite3
import hashlib
from flask import Flask, request, jsonify, render_template_string
from datetime import datetime, timedelta
import json
import requests
from dotenv import load_dotenv
import threading
import schedule
import time
from bs4 import BeautifulSoup
import re
from urllib.parse import urlparse
from contextlib import closing

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Configuration
LINE_ACCESS_TOKEN = os.getenv('LINE_CHANNEL_ACCESS_TOKEN')
LINE_REPLY_URL = 'https://api.line.me/v2/bot/message/reply'
LINE_PUSH_URL = 'https://api.line.me/v2/bot/message/push'
DATABASE_PATH = 'articles.db'
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '')

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database connection helper
def get_db():
    """Get database connection with proper settings"""
    conn = sqlite3.connect(DATABASE_PATH, timeout=30.0, isolation_level=None)
    conn.execute('PRAGMA journal_mode=WAL')
    conn.execute('PRAGMA busy_timeout=30000')
    conn.row_factory = sqlite3.Row
    return conn

# Initialize database
def init_database():
    with closing(get_db()) as conn:
        cursor = conn.cursor()
        
        # Create articles table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS articles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                url TEXT NOT NULL,
                url_hash TEXT UNIQUE,
                title TEXT,
                content TEXT,
                summary TEXT,
                category TEXT,
                author TEXT,
                published_date TEXT,
                reading_time INTEGER,
                word_count INTEGER,
                saved_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_read BOOLEAN DEFAULT 0,
                user_notes TEXT,
                tags TEXT
            )
        ''')
        
        # Create webhooks log table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS webhook_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                event_type TEXT,
                user_id TEXT,
                message_text TEXT,
                raw_data TEXT
            )
        ''')
        
        # Create daily summaries table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS daily_summaries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                summary_date DATE,
                articles_count INTEGER,
                summary_text TEXT,
                sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create indexes
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_user_id ON articles(user_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_saved_at ON articles(saved_at)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_url_hash ON articles(url_hash)')
        
        conn.commit()
    logger.info("Database initialized successfully")

# Article extraction
def extract_article_content(url):
    """Extract article content from URL"""
    try:
        # Clean URL
        url = url.strip()
        
        response = requests.get(url, timeout=10, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()
        
        # Extract title
        title = soup.find('title')
        title = title.get_text() if title else urlparse(url).netloc
        
        # Try to find main content
        content_tags = soup.find_all(['article', 'main', 'div'], class_=re.compile('content|article|post|entry'))
        if not content_tags:
            content_tags = soup.find_all('p')
        
        # Extract text
        text_content = ' '.join([tag.get_text() for tag in content_tags[:50]])
        text_content = re.sub(r'\s+', ' ', text_content).strip()
        
        # Calculate reading metrics
        word_count = len(text_content.split())
        reading_time = max(1, word_count // 200)
        
        # Determine category
        category = 'General'
        url_lower = url.lower()
        if 'tech' in url_lower or 'technology' in url_lower:
            category = 'Technology'
        elif 'business' in url_lower or 'finance' in url_lower:
            category = 'Business'
        elif 'news' in url_lower:
            category = 'News'
        
        return {
            'title': title[:200],
            'content': text_content[:5000],
            'category': category,
            'word_count': word_count,
            'reading_time': reading_time
        }
    except Exception as e:
        logger.error(f"Error extracting article: {str(e)}")
        return {
            'title': url,
            'content': '',
            'category': 'General',
            'word_count': 0,
            'reading_time': 1
        }

def generate_summary(content, title=''):
    """Generate AI summary of article content"""
    if not content:
        return "No content available for summary."
    
    # Use OpenAI if available
    if OPENAI_API_KEY and len(OPENAI_API_KEY) > 20:
        try:
            from openai import OpenAI
            client = OpenAI(api_key=OPENAI_API_KEY)
            
            prompt = f"Summarize this article in 2-3 sentences:\n\nTitle: {title}\n\nContent: {content[:2000]}"
            
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that creates concise article summaries."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=150,
                temperature=0.7
            )
            
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"OpenAI API error: {str(e)}")
    
    # Fallback to simple summary
    sentences = content.split('.')[:3]
    summary = '. '.join(sentences).strip()
    return summary[:300] if summary else "Article saved successfully."

def save_article_to_db(user_id, url, article_info):
    """Save article to database"""
    url_hash = hashlib.md5(url.encode()).hexdigest()
    
    try:
        with closing(get_db()) as conn:
            cursor = conn.cursor()
            
            # Check if exists
            cursor.execute('SELECT id, title FROM articles WHERE url_hash = ?', (url_hash,))
            existing = cursor.fetchone()
            
            if existing:
                return {'status': 'duplicate', 'id': existing['id'], 'title': existing['title']}
            
            # Generate summary
            summary = generate_summary(article_info.get('content', ''), article_info.get('title', ''))
            
            # Insert new article
            cursor.execute('''
                INSERT INTO articles (
                    user_id, url, url_hash, title, content, summary, 
                    category, reading_time, word_count
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                user_id, url, url_hash,
                article_info.get('title'),
                article_info.get('content'),
                summary,
                article_info.get('category'),
                article_info.get('reading_time'),
                article_info.get('word_count')
            ))
            
            conn.commit()
            article_id = cursor.lastrowid
            
            return {
                'status': 'saved',
                'id': article_id,
                'title': article_info.get('title'),
                'summary': summary,
                'category': article_info.get('category'),
                'reading_time': article_info.get('reading_time'),
                'word_count': article_info.get('word_count')
            }
            
    except Exception as e:
        logger.error(f"Database error: {str(e)}")
        return {'status': 'error', 'message': str(e)}

def get_user_articles(user_id, limit=10):
    """Get user's saved articles"""
    with closing(get_db()) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, title, url, summary, category, reading_time, saved_at, is_read
            FROM articles
            WHERE user_id = ?
            ORDER BY saved_at DESC
            LIMIT ?
        ''', (user_id, limit))
        return cursor.fetchall()

def get_user_stats(user_id):
    """Get user statistics"""
    with closing(get_db()) as conn:
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) as total FROM articles WHERE user_id = ?', (user_id,))
        total = cursor.fetchone()['total']
        
        cursor.execute('SELECT SUM(reading_time) as total_reading FROM articles WHERE user_id = ?', (user_id,))
        total_reading = cursor.fetchone()['total_reading'] or 0
        
        cursor.execute('SELECT category, COUNT(*) as count FROM articles WHERE user_id = ? GROUP BY category', (user_id,))
        categories = cursor.fetchall()
        
        return {
            'total': total,
            'total_reading': total_reading,
            'categories': [(row['category'], row['count']) for row in categories]
        }

# Flask routes
@app.route("/", methods=['GET'])
def home():
    """Dashboard"""
    with closing(get_db()) as conn:
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) as count FROM articles')
        total_articles = cursor.fetchone()['count']
        
        cursor.execute('SELECT COUNT(DISTINCT user_id) as count FROM articles')
        total_users = cursor.fetchone()['count']
        
        cursor.execute('''
            SELECT title, url, category, saved_at, user_id
            FROM articles
            ORDER BY saved_at DESC
            LIMIT 10
        ''')
        recent = cursor.fetchall()
    
    html = f'''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Article Bot Dashboard</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }}
            .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 10px; }}
            h1 {{ color: #27ACB2; }}
            .stats {{ display: flex; gap: 20px; margin: 20px 0; }}
            .stat-card {{ flex: 1; padding: 15px; background: #f8f9fa; border-radius: 5px; text-align: center; }}
            .stat-number {{ font-size: 2em; color: #27ACB2; font-weight: bold; }}
            table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
            th, td {{ padding: 10px; text-align: left; border-bottom: 1px solid #ddd; }}
            th {{ background: #27ACB2; color: white; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>📚 Article Bot Dashboard - SQLite Database</h1>
            <p>✅ Using local SQLite database (no Google Sheets needed!)</p>
            
            <div class="stats">
                <div class="stat-card">
                    <div class="stat-number">{total_articles}</div>
                    <div>Total Articles</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">{total_users}</div>
                    <div>Active Users</div>
                </div>
            </div>
            
            <h2>Recent Articles</h2>
            <table>
                <tr>
                    <th>Title</th>
                    <th>Category</th>
                    <th>User</th>
                    <th>Saved At</th>
                </tr>
    '''
    
    for article in recent:
        html += f'''
                <tr>
                    <td><a href="{article['url']}" target="_blank">{article['title'][:60]}...</a></td>
                    <td>{article['category']}</td>
                    <td>{article['user_id'][:8]}...</td>
                    <td>{article['saved_at']}</td>
                </tr>
        '''
    
    html += '''
            </table>
        </div>
    </body>
    </html>
    '''
    return html

@app.route('/callback', methods=['POST'])
def callback():
    """Handle LINE webhooks"""
    body = request.get_data(as_text=True)
    
    try:
        body_json = json.loads(body)
    except:
        return 'OK', 200
    
    # Process events
    if body_json.get('events'):
        for event in body_json['events']:
            user_id = event.get('source', {}).get('userId', 'unknown')
            
            # Log to database
            with closing(get_db()) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO webhook_logs (event_type, user_id, message_text, raw_data)
                    VALUES (?, ?, ?, ?)
                ''', (
                    event.get('type'),
                    user_id,
                    event.get('message', {}).get('text', '') if event.get('type') == 'message' else None,
                    json.dumps(event)
                ))
                conn.commit()
            
            # Handle message events
            if event.get('type') == 'message':
                message = event.get('message', {})
                reply_token = event.get('replyToken')
                
                if message.get('type') == 'text':
                    text = message.get('text', '')
                    handle_text_message(user_id, text, reply_token)
    
    return 'OK', 200

def handle_text_message(user_id, text, reply_token):
    """Handle text messages"""
    reply_text = ""
    
    # Check for URLs
    url_pattern = r'https?://(?:[-\w.])+(?:\:\d+)?(?:[/\w\s._~%!$&\'()*+,;=:@-]+)?'
    urls = re.findall(url_pattern, text)
    
    if urls:
        url = urls[0].strip()
        logger.info(f"Processing URL: {url}")
        
        # Extract content
        article_info = extract_article_content(url)
        
        # Save to database
        result = save_article_to_db(user_id, url, article_info)
        
        if result['status'] == 'saved':
            reply_text = f"✅ Article Saved to Database!\n\n"
            reply_text += f"📚 {result['title'][:100]}\n\n"
            reply_text += f"📝 AI Summary:\n{result['summary'][:200]}...\n\n"
            reply_text += f"⏱️ Reading time: {result.get('reading_time', 1)} min\n"
            reply_text += f"📊 Words: {result.get('word_count', 0)}\n"
            reply_text += f"🏷️ Category: {result.get('category', 'General')}\n\n"
            reply_text += "💾 Saved in SQLite database"
        elif result['status'] == 'duplicate':
            reply_text = f"ℹ️ Already in database!\n\n📚 {result['title'][:100]}"
        else:
            reply_text = "⚠️ Error saving. Try again."
    
    elif text.lower() == '/list':
        articles = get_user_articles(user_id, 5)
        if articles:
            reply_text = "📚 Your Articles (from database):\n\n"
            for i, article in enumerate(articles, 1):
                reply_text += f"{i}. {article['title'][:50]}...\n"
                reply_text += f"   📁 {article['category']} | ⏱️ {article['reading_time']} min\n\n"
        else:
            reply_text = "📭 No articles yet. Send me URLs!"
    
    elif text.lower() == '/stats':
        stats = get_user_stats(user_id)
        reply_text = f"📊 Your Statistics\n\n"
        reply_text += f"📚 Total: {stats['total']} articles\n"
        reply_text += f"⏱️ Reading time: {stats['total_reading']} min\n\n"
        
        if stats['categories']:
            reply_text += "📑 Categories:\n"
            for cat, count in stats['categories']:
                reply_text += f"  • {cat}: {count}\n"
    
    elif text.lower() in ['/help', 'help']:
        reply_text = "🤖 Article Bot (SQLite)\n\n"
        reply_text += "📝 Commands:\n"
        reply_text += "• Send URL - Save to database\n"
        reply_text += "• /list - View articles\n"
        reply_text += "• /stats - Your statistics\n"
        reply_text += "• /help - This message\n\n"
        reply_text += "✨ Features:\n"
        reply_text += "• AI summaries (GPT-3.5)\n"
        reply_text += "• SQLite database\n"
        reply_text += "• No Google Sheets needed!"
    
    else:
        reply_text = "👋 Send me a URL to save!\n\nType /help for commands."
    
    # Send reply
    if reply_token and reply_text:
        send_reply(reply_token, reply_text)

def send_reply(reply_token, text):
    """Send reply to LINE"""
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {LINE_ACCESS_TOKEN}'
    }
    
    data = {
        'replyToken': reply_token,
        'messages': [{'type': 'text', 'text': text}]
    }
    
    try:
        response = requests.post(LINE_REPLY_URL, headers=headers, json=data)
        if response.status_code == 200:
            logger.info("Reply sent successfully")
        else:
            logger.error(f"Failed to send reply: {response.status_code}")
    except Exception as e:
        logger.error(f"Error sending reply: {str(e)}")

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy', 'database': 'SQLite'})

if __name__ == "__main__":
    init_database()
    
    port = int(os.environ.get('PORT', '5001'))
    print("\n" + "="*60)
    print("ARTICLE BOT - SQLite Database Edition")
    print("="*60)
    print(f"\nServer starting on http://localhost:{port}")
    print("\n✅ Features:")
    print("  • SQLite database (no Google Sheets!)")
    print("  • AI summaries with GPT-3.5")
    print("  • Content extraction")
    print("  • Dashboard interface")
    print("\n" + "="*60)
    
    app.run(host='0.0.0.0', port=port, debug=True)