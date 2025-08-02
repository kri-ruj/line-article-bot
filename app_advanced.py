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

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Configuration
LINE_ACCESS_TOKEN = os.getenv('LINE_CHANNEL_ACCESS_TOKEN')
LINE_REPLY_URL = 'https://api.line.me/v2/bot/message/reply'
LINE_PUSH_URL = 'https://api.line.me/v2/bot/message/push'
DATABASE_PATH = 'articles.db'
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '')  # Optional for AI summaries

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize database
def init_database():
    conn = sqlite3.connect(DATABASE_PATH, timeout=30.0, check_same_thread=False)
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
    
    # Create indexes for better performance
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_user_id ON articles(user_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_saved_at ON articles(saved_at)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_url_hash ON articles(url_hash)')
    
    conn.commit()
    conn.close()
    logger.info("Database initialized successfully")

# Article extraction and summarization
def extract_article_content(url):
    """Extract article content from URL"""
    try:
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
        text_content = ' '.join([tag.get_text() for tag in content_tags[:50]])  # Limit to first 50 paragraphs
        text_content = re.sub(r'\s+', ' ', text_content).strip()
        
        # Calculate reading metrics
        word_count = len(text_content.split())
        reading_time = max(1, word_count // 200)  # Assuming 200 words per minute
        
        # Try to extract author
        author = None
        author_tag = soup.find(['meta'], attrs={'name': 'author'})
        if author_tag:
            author = author_tag.get('content')
        
        # Try to extract publish date
        published_date = None
        date_tag = soup.find(['meta'], attrs={'property': 'article:published_time'})
        if date_tag:
            published_date = date_tag.get('content')
        
        # Determine category based on URL or content
        category = 'General'
        url_lower = url.lower()
        if 'tech' in url_lower or 'technology' in url_lower:
            category = 'Technology'
        elif 'business' in url_lower or 'finance' in url_lower:
            category = 'Business'
        elif 'health' in url_lower or 'medical' in url_lower:
            category = 'Health'
        elif 'science' in url_lower:
            category = 'Science'
        elif 'sport' in url_lower:
            category = 'Sports'
        
        return {
            'title': title[:200],
            'content': text_content[:5000],  # Limit content to 5000 chars
            'author': author,
            'published_date': published_date,
            'category': category,
            'word_count': word_count,
            'reading_time': reading_time
        }
    except Exception as e:
        logger.error(f"Error extracting article: {str(e)}")
        return {
            'title': urlparse(url).netloc,
            'content': '',
            'author': None,
            'published_date': None,
            'category': 'General',
            'word_count': 0,
            'reading_time': 1
        }

def generate_summary(content, title=''):
    """Generate AI summary of article content"""
    if not content:
        return "No content available for summary."
    
    # If OpenAI API key is available, use GPT for summary
    if OPENAI_API_KEY and OPENAI_API_KEY != 'sk-proj-YOUR_ACTUAL_API_KEY_HERE':
        try:
            from openai import OpenAI
            client = OpenAI(api_key=OPENAI_API_KEY)
            
            prompt = f"Summarize this article in 2-3 sentences. Focus on the key points and main takeaways:\n\nTitle: {title}\n\nContent: {content[:2000]}"
            
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that creates concise, informative article summaries."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=150,
                temperature=0.7
            )
            
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"OpenAI API error: {str(e)}")
    
    # Fallback to simple extractive summary
    sentences = content.split('.')[:3]
    summary = '. '.join(sentences).strip()
    if summary and not summary.endswith('.'):
        summary += '.'
    
    return summary[:300] if summary else "Article saved. Content extraction pending."

def save_article_to_db(user_id, url, article_info):
    """Save article to database"""
    conn = sqlite3.connect(DATABASE_PATH, timeout=30.0, check_same_thread=False)
    cursor = conn.cursor()
    
    # Generate URL hash to check for duplicates
    url_hash = hashlib.md5(url.encode()).hexdigest()
    
    try:
        # Check if article already exists
        cursor.execute('SELECT id, title FROM articles WHERE url_hash = ?', (url_hash,))
        existing = cursor.fetchone()
        
        if existing:
            return {'status': 'duplicate', 'id': existing[0], 'title': existing[1]}
        
        # Generate summary
        summary = generate_summary(article_info.get('content', ''), article_info.get('title', ''))
        
        # Insert new article
        cursor.execute('''
            INSERT INTO articles (
                user_id, url, url_hash, title, content, summary, 
                category, author, published_date, reading_time, word_count
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            user_id, url, url_hash,
            article_info.get('title'),
            article_info.get('content'),
            summary,
            article_info.get('category'),
            article_info.get('author'),
            article_info.get('published_date'),
            article_info.get('reading_time'),
            article_info.get('word_count')
        ))
        
        conn.commit()
        article_id = cursor.lastrowid
        
        return {
            'status': 'saved',
            'id': article_id,
            'title': article_info.get('title'),
            'summary': summary
        }
        
    except Exception as e:
        logger.error(f"Database error: {str(e)}")
        return {'status': 'error', 'message': str(e)}
    finally:
        conn.close()

def get_user_articles(user_id, limit=10):
    """Get user's saved articles"""
    conn = sqlite3.connect(DATABASE_PATH, timeout=30.0)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT id, title, url, summary, category, reading_time, saved_at, is_read
        FROM articles
        WHERE user_id = ?
        ORDER BY saved_at DESC
        LIMIT ?
    ''', (user_id, limit))
    
    articles = cursor.fetchall()
    conn.close()
    
    return articles

def generate_daily_summary(user_id):
    """Generate daily summary for user"""
    conn = sqlite3.connect(DATABASE_PATH, timeout=30.0)
    cursor = conn.cursor()
    
    # Get articles from last 24 hours
    yesterday = datetime.now() - timedelta(days=1)
    
    cursor.execute('''
        SELECT title, summary, category, reading_time
        FROM articles
        WHERE user_id = ? AND saved_at > ?
        ORDER BY saved_at DESC
    ''', (user_id, yesterday))
    
    articles = cursor.fetchall()
    
    if not articles:
        return None
    
    # Create summary text
    summary_text = f"📊 Your Daily Digest\n{datetime.now().strftime('%Y-%m-%d')}\n\n"
    summary_text += f"📚 Articles saved: {len(articles)}\n"
    
    # Calculate total reading time
    total_reading_time = sum(article[3] or 0 for article in articles)
    summary_text += f"⏱️ Total reading time: {total_reading_time} minutes\n\n"
    
    # Group by category
    categories = {}
    for article in articles:
        cat = article[2] or 'General'
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(article)
    
    summary_text += "📑 By Category:\n"
    for cat, cat_articles in categories.items():
        summary_text += f"  • {cat}: {len(cat_articles)} articles\n"
    
    summary_text += "\n📝 Recent Articles:\n"
    for i, article in enumerate(articles[:5], 1):
        summary_text += f"\n{i}. {article[0][:50]}...\n"
        if article[1]:
            summary_text += f"   📄 {article[1][:100]}...\n"
    
    # Save summary to database
    cursor.execute('''
        INSERT INTO daily_summaries (user_id, summary_date, articles_count, summary_text)
        VALUES (?, ?, ?, ?)
    ''', (user_id, datetime.now().date(), len(articles), summary_text))
    
    conn.commit()
    conn.close()
    
    return summary_text

# Flask routes
@app.route("/", methods=['GET'])
def home():
    """Dashboard view"""
    conn = sqlite3.connect(DATABASE_PATH, timeout=30.0)
    cursor = conn.cursor()
    
    # Get statistics
    cursor.execute('SELECT COUNT(*) FROM articles')
    total_articles = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(DISTINCT user_id) FROM articles')
    total_users = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM webhook_logs')
    total_webhooks = cursor.fetchone()[0]
    
    # Get recent articles
    cursor.execute('''
        SELECT title, url, category, saved_at, user_id
        FROM articles
        ORDER BY saved_at DESC
        LIMIT 10
    ''')
    recent_articles = cursor.fetchall()
    
    conn.close()
    
    html = '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Article Bot Dashboard</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }
            .container { max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 10px; }
            h1 { color: #27ACB2; }
            .stats { display: flex; gap: 20px; margin: 20px 0; }
            .stat-card { flex: 1; padding: 15px; background: #f8f9fa; border-radius: 5px; text-align: center; }
            .stat-number { font-size: 2em; color: #27ACB2; font-weight: bold; }
            table { width: 100%; border-collapse: collapse; margin-top: 20px; }
            th, td { padding: 10px; text-align: left; border-bottom: 1px solid #ddd; }
            th { background: #27ACB2; color: white; }
            .category { display: inline-block; padding: 3px 8px; background: #e9ecef; border-radius: 3px; font-size: 0.9em; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>📚 Article Bot Dashboard</h1>
            
            <div class="stats">
                <div class="stat-card">
                    <div class="stat-number">''' + str(total_articles) + '''</div>
                    <div>Total Articles</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">''' + str(total_users) + '''</div>
                    <div>Active Users</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">''' + str(total_webhooks) + '''</div>
                    <div>Webhooks Received</div>
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
    
    for article in recent_articles:
        html += f'''
                <tr>
                    <td><a href="{article[1]}" target="_blank">{article[0][:60]}...</a></td>
                    <td><span class="category">{article[2]}</span></td>
                    <td>{article[4][:8]}...</td>
                    <td>{article[3]}</td>
                </tr>
        '''
    
    html += '''
            </table>
            
            <p style="margin-top: 30px; color: #666;">
                <a href="/logs">View Webhook Logs</a> | 
                <a href="/stats">Detailed Statistics</a> |
                <a href="/health">Health Check</a>
            </p>
        </div>
    </body>
    </html>
    '''
    
    return html

@app.route('/callback', methods=['POST'])
def callback():
    """Handle LINE webhooks"""
    headers = dict(request.headers)
    body = request.get_data(as_text=True)
    
    # Parse body
    try:
        body_json = json.loads(body) if body else {}
    except:
        body_json = {"raw": body}
    
    # Log webhook to database
    conn = sqlite3.connect(DATABASE_PATH, timeout=30.0)
    cursor = conn.cursor()
    
    # Process events
    if body_json.get('events'):
        for event in body_json['events']:
            user_id = event.get('source', {}).get('userId', 'unknown')
            event_type = event.get('type')
            
            # Log to database
            cursor.execute('''
                INSERT INTO webhook_logs (event_type, user_id, message_text, raw_data)
                VALUES (?, ?, ?, ?)
            ''', (
                event_type,
                user_id,
                event.get('message', {}).get('text', '') if event_type == 'message' else None,
                json.dumps(event)
            ))
            
            # Handle message events
            if event_type == 'message':
                message = event.get('message', {})
                reply_token = event.get('replyToken')
                
                if message.get('type') == 'text':
                    text = message.get('text', '')
                    handle_text_message(user_id, text, reply_token)
    
    conn.commit()
    conn.close()
    
    return 'OK', 200

def handle_text_message(user_id, text, reply_token):
    """Handle text messages from users"""
    reply_text = ""
    
    # Check for URLs
    url_pattern = r'https?://(?:[-\w.])+(?:\:\d+)?(?:[/\w\s._~%!$&\'()*+,;=:@-]+)?'
    urls = re.findall(url_pattern, text)
    
    if urls:
        url = urls[0]
        # Extract article content
        article_info = extract_article_content(url)
        
        # Save to database
        result = save_article_to_db(user_id, url, article_info)
        
        if result['status'] == 'saved':
            reply_text = f"✅ Article Saved!\n\n"
            reply_text += f"📚 {result['title'][:100]}\n\n"
            reply_text += f"📝 Summary:\n{result['summary'][:200]}...\n\n"
            reply_text += f"⏱️ Reading time: {article_info['reading_time']} min\n"
            reply_text += f"📊 Word count: {article_info['word_count']}\n"
            reply_text += f"🏷️ Category: {article_info['category']}\n\n"
            reply_text += "Type /list to see all your articles"
        elif result['status'] == 'duplicate':
            reply_text = f"ℹ️ Article already saved!\n\n📚 {result['title'][:100]}\n\nType /list to view your articles"
        else:
            reply_text = "❌ Error saving article. Please try again."
    
    elif text.lower() == '/list':
        articles = get_user_articles(user_id, 5)
        if articles:
            reply_text = "📚 Your Recent Articles:\n\n"
            for i, article in enumerate(articles, 1):
                status = "✅" if article[7] else "📖"
                reply_text += f"{i}. {status} {article[1][:50]}...\n"
                reply_text += f"   📁 {article[4]} | ⏱️ {article[5]} min\n\n"
            
            conn = sqlite3.connect(DATABASE_PATH, timeout=30.0)
            cursor = conn.cursor()
            cursor.execute('SELECT COUNT(*) FROM articles WHERE user_id = ?', (user_id,))
            total = cursor.fetchone()[0]
            conn.close()
            
            reply_text += f"📊 Total saved: {total} articles"
        else:
            reply_text = "📭 No articles saved yet.\nSend me a URL to get started!"
    
    elif text.lower() == '/summary':
        summary = generate_daily_summary(user_id)
        reply_text = summary if summary else "📭 No articles in the last 24 hours"
    
    elif text.lower() in ['/help', 'help']:
        reply_text = "🤖 Smart Article Bot\n\n"
        reply_text += "📝 Commands:\n"
        reply_text += "• Send any URL - Save & summarize article\n"
        reply_text += "• /list - View your saved articles\n"
        reply_text += "• /summary - Get daily digest\n"
        reply_text += "• /stats - View your statistics\n"
        reply_text += "• /help - Show this message\n\n"
        reply_text += "✨ Features:\n"
        reply_text += "• AI-powered summaries\n"
        reply_text += "• Content extraction\n"
        reply_text += "• Reading time estimation\n"
        reply_text += "• Category detection\n"
        reply_text += "• Daily digests"
    
    elif text.lower() == '/stats':
        conn = sqlite3.connect(DATABASE_PATH, timeout=30.0)
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM articles WHERE user_id = ?', (user_id,))
        total = cursor.fetchone()[0]
        
        cursor.execute('SELECT SUM(reading_time) FROM articles WHERE user_id = ?', (user_id,))
        total_reading = cursor.fetchone()[0] or 0
        
        cursor.execute('SELECT category, COUNT(*) FROM articles WHERE user_id = ? GROUP BY category', (user_id,))
        categories = cursor.fetchall()
        
        conn.close()
        
        reply_text = f"📊 Your Statistics\n\n"
        reply_text += f"📚 Total articles: {total}\n"
        reply_text += f"⏱️ Total reading time: {total_reading} minutes\n"
        reply_text += f"📖 Average reading time: {total_reading//total if total > 0 else 0} min/article\n\n"
        
        if categories:
            reply_text += "📑 By Category:\n"
            for cat, count in categories:
                reply_text += f"  • {cat}: {count} articles\n"
    
    else:
        reply_text = f"👋 Hi! Send me a URL to save and summarize it.\n\nType /help for all commands."
    
    # Send reply
    if reply_token and reply_text:
        send_reply(reply_token, reply_text)

def send_reply(reply_token, text):
    """Send reply message to LINE"""
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
            logger.error(f"Failed to send reply: {response.status_code} - {response.text}")
    except Exception as e:
        logger.error(f"Error sending reply: {str(e)}")

def send_push_message(user_id, text):
    """Send push message to user"""
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {LINE_ACCESS_TOKEN}'
    }
    
    data = {
        'to': user_id,
        'messages': [{'type': 'text', 'text': text}]
    }
    
    try:
        response = requests.post(LINE_PUSH_URL, headers=headers, json=data)
        if response.status_code == 200:
            logger.info(f"Push message sent to {user_id}")
        else:
            logger.error(f"Failed to send push: {response.status_code}")
    except Exception as e:
        logger.error(f"Error sending push: {str(e)}")

@app.route('/stats', methods=['GET'])
def stats_page():
    """Statistics page"""
    conn = sqlite3.connect(DATABASE_PATH, timeout=30.0)
    cursor = conn.cursor()
    
    # Get various statistics
    cursor.execute('''
        SELECT 
            COUNT(*) as total,
            COUNT(DISTINCT user_id) as users,
            AVG(reading_time) as avg_reading,
            SUM(word_count) as total_words,
            COUNT(CASE WHEN is_read = 1 THEN 1 END) as read_count
        FROM articles
    ''')
    
    stats = cursor.fetchone()
    
    # Get category distribution
    cursor.execute('''
        SELECT category, COUNT(*) as count
        FROM articles
        GROUP BY category
        ORDER BY count DESC
    ''')
    
    categories = cursor.fetchall()
    
    conn.close()
    
    return jsonify({
        'total_articles': stats[0],
        'total_users': stats[1],
        'average_reading_time': round(stats[2] or 0, 1),
        'total_words': stats[3] or 0,
        'read_articles': stats[4],
        'categories': [{'name': cat[0], 'count': cat[1]} for cat in categories]
    })

@app.route('/logs', methods=['GET'])
def view_logs():
    """View webhook logs"""
    conn = sqlite3.connect(DATABASE_PATH, timeout=30.0)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT timestamp, event_type, user_id, message_text
        FROM webhook_logs
        ORDER BY timestamp DESC
        LIMIT 50
    ''')
    
    logs = cursor.fetchall()
    conn.close()
    
    return jsonify([{
        'timestamp': log[0],
        'event_type': log[1],
        'user_id': log[2],
        'message_text': log[3]
    } for log in logs])

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy', 'database': 'connected'})

# Daily summary scheduler
def run_daily_summaries():
    """Send daily summaries to all active users"""
    conn = sqlite3.connect(DATABASE_PATH, timeout=30.0)
    cursor = conn.cursor()
    
    # Get all users with articles from yesterday
    yesterday = datetime.now() - timedelta(days=1)
    cursor.execute('''
        SELECT DISTINCT user_id
        FROM articles
        WHERE saved_at > ?
    ''', (yesterday,))
    
    users = cursor.fetchall()
    conn.close()
    
    for user in users:
        user_id = user[0]
        summary = generate_daily_summary(user_id)
        if summary:
            send_push_message(user_id, summary)
            logger.info(f"Daily summary sent to {user_id}")

def schedule_runner():
    """Background thread for scheduled tasks"""
    schedule.every().day.at("09:00").do(run_daily_summaries)
    
    while True:
        schedule.run_pending()
        time.sleep(60)

if __name__ == "__main__":
    # Initialize database
    init_database()
    
    # Start scheduler in background thread
    scheduler_thread = threading.Thread(target=schedule_runner, daemon=True)
    scheduler_thread.start()
    logger.info("Scheduler started - daily summaries at 09:00")
    
    # Start Flask app
    port = int(os.environ.get('PORT', '5001'))
    print("\n" + "="*60)
    print("ADVANCED ARTICLE BOT WITH AI & DATABASE")
    print("="*60)
    print(f"\nServer starting on http://localhost:{port}")
    print("\n✨ Features:")
    print("  • SQLite database for persistent storage")
    print("  • AI-powered article summarization")
    print("  • Automatic content extraction")
    print("  • Daily digest summaries (9:00 AM)")
    print("  • Web dashboard for monitoring")
    print("\n📊 Endpoints:")
    print(f"  • Dashboard: http://localhost:{port}/")
    print(f"  • Statistics: http://localhost:{port}/stats")
    print(f"  • Logs: http://localhost:{port}/logs")
    print("\n" + "="*60)
    
    app.run(host='0.0.0.0', port=port, debug=True)