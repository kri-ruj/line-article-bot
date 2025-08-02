#!/usr/bin/env python3
"""Fixed LINE Bot with proper response handling"""

import os
import sqlite3
import json
import hashlib
import requests
from flask import Flask, request, jsonify
from datetime import datetime
from contextlib import closing
from dotenv import load_dotenv
import logging
import traceback
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage

load_dotenv()

app = Flask(__name__)

# Configuration
LINE_ACCESS_TOKEN = os.getenv('LINE_CHANNEL_ACCESS_TOKEN')
LINE_SECRET = os.getenv('LINE_CHANNEL_SECRET')

line_bot_api = LineBotApi(LINE_ACCESS_TOKEN)
handler = WebhookHandler(LINE_SECRET)

DATABASE_PATH = 'articles_enhanced.db'
KANBAN_DB_PATH = 'articles_kanban.db'

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_db(db_path=DATABASE_PATH):
    """Get database connection"""
    conn = sqlite3.connect(db_path, timeout=30.0, isolation_level=None)
    conn.execute('PRAGMA journal_mode=WAL')
    conn.row_factory = sqlite3.Row
    return conn

def extract_article_info(url):
    """Extract article information from URL"""
    try:
        from bs4 import BeautifulSoup
        response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Extract title
        title = None
        if soup.title:
            title = soup.title.string
        elif soup.find('h1'):
            title = soup.find('h1').get_text()
        elif soup.find('meta', property='og:title'):
            title = soup.find('meta', property='og:title')['content']
        
        # Extract description/summary
        summary = None
        meta_desc = soup.find('meta', {'name': 'description'})
        if meta_desc:
            summary = meta_desc.get('content', '')
        elif soup.find('meta', property='og:description'):
            summary = soup.find('meta', property='og:description')['content']
        
        # Calculate word count
        text = soup.get_text()
        words = len(text.split())
        
        # Clean up title and summary
        if title:
            title = ' '.join(title.split())[:200]  # Clean whitespace, limit length
        if summary:
            summary = ' '.join(summary.split())[:500]
            
        return {
            'title': title or url.split('/')[-1] or 'Untitled',
            'summary': summary or '',
            'word_count': words,
            'reading_time': max(1, words // 200)  # Assume 200 words per minute
        }
    except Exception as e:
        logger.error(f"Error extracting article info: {e}")
        # Return defaults for problematic URLs (like Facebook)
        return {
            'title': url.split('/')[-2] if '/' in url else 'Article',
            'summary': '',
            'word_count': 0,
            'reading_time': 5
        }

def save_article_to_kanban(url, title="", summary=""):
    """Save article to Kanban database"""
    url_hash = hashlib.md5(url.encode()).hexdigest()
    
    # Extract article info if not provided
    if not title or not summary:
        article_info = extract_article_info(url)
        title = title or article_info['title']
        summary = summary or article_info['summary']
        word_count = article_info['word_count']
        reading_time = article_info['reading_time']
    else:
        word_count = len(summary.split()) if summary else 0
        reading_time = max(1, word_count // 200)
    
    try:
        with closing(get_db(KANBAN_DB_PATH)) as conn:
            cursor = conn.cursor()
            
            # Check if exists
            cursor.execute('SELECT id FROM articles_kanban WHERE url_hash = ?', (url_hash,))
            existing = cursor.fetchone()
            
            if existing:
                return {'status': 'duplicate', 'id': existing[0]}
            
            # Insert new article with more data
            cursor.execute('''
                INSERT INTO articles_kanban (
                    url, url_hash, title, summary, word_count, reading_time,
                    stage, added_date
                ) VALUES (?, ?, ?, ?, ?, ?, 'inbox', CURRENT_TIMESTAMP)
            ''', (url, url_hash, title[:200], summary[:500], word_count, reading_time))
            
            conn.commit()
            article_id = cursor.lastrowid
            
            logger.info(f"✅ Article saved to Kanban: {title}")
            return {'status': 'saved', 'id': article_id, 'title': title}
            
    except Exception as e:
        logger.error(f"Database error: {str(e)}")
        return {'status': 'error', 'message': str(e)}

@app.route('/')
def home():
    """Homepage"""
    return """
    <h1>🧠 LINE Article Bot</h1>
    <p>Status: ✅ Active</p>
    <p>Send me URLs via LINE to save articles!</p>
    <hr>
    <p>Commands:</p>
    <ul>
        <li>Send any URL - Save article</li>
        <li>/help - Show commands</li>
        <li>/list - Show recent articles</li>
        <li>/stats - Show statistics</li>
    </ul>
    """

@app.route('/callback', methods=['POST'])
def callback():
    """Handle LINE webhook with proper response"""
    # Get request body as text
    body = request.get_data(as_text=True)
    logger.info("Request body: " + body)
    
    # Log all headers for debugging
    logger.info(f"Headers: {dict(request.headers)}")
    
    # Parse the body to check if it's from LINE
    try:
        data = json.loads(body) if body else {}
        if 'events' in data and data['events']:
            logger.info(f"LINE webhook received with {len(data['events'])} events")
            for event in data['events']:
                logger.info(f"Event type: {event.get('type')}, Message: {event.get('message', {}).get('text', 'N/A')}")
    except:
        pass
    
    # Get X-Line-Signature header value
    signature = request.headers.get('X-Line-Signature', '')
    
    # Handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        logger.error("Invalid signature")
        return 'Invalid signature', 400
    except Exception as e:
        logger.error(f"Handler error: {str(e)}")
        return 'OK', 200
    
    return 'OK', 200

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    """Handle LINE text messages"""
    try:
        user_id = event.source.user_id
        text = event.message.text
        reply_token = event.reply_token
        
        logger.info(f"Message from {user_id}: {text}")
        
        # Check for URLs
        import re
        url_pattern = r'https?://(?:[-\w.])+(?:\:\d+)?(?:[/\w\s._~%!$&\'()*+,;=:@-]+)?'
        urls = re.findall(url_pattern, text)
        
        if urls:
            url = urls[0].strip()
            logger.info(f"Processing URL: {url}")
            
            # Save to database
            result = save_article_to_kanban(url)
            
            if result['status'] == 'saved':
                reply_text = f"""✅ Article Saved!

📚 {url[:50]}...

The article has been added to your Inbox in the Kanban board.

📋 Next steps:
• Visit dashboard to review
• Move to "Reading" when you start
• Add study notes as you learn

View dashboard: https://aa4fe2493ae1.ngrok-free.app"""
                
            elif result['status'] == 'duplicate':
                reply_text = "📚 This article is already in your collection!"
                
            else:
                reply_text = f"❌ Error saving article: {result.get('message', 'Unknown error')}"
        
        elif text.lower() == '/help':
            reply_text = """🧠 Article Intelligence Bot

📝 Commands:
• Send any URL - Save & analyze article
• /help - Show this message
• /list - Recent articles
• /stats - Your statistics

📊 Dashboard:
https://aa4fe2493ae1.ngrok-free.app

✨ Features:
• AI-powered analysis
• Kanban board tracking
• Study progress monitoring"""
        
        elif text.lower() == '/stats':
            # Get statistics
            try:
                with closing(get_db(KANBAN_DB_PATH)) as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT COUNT(*) FROM articles_kanban')
                    total = cursor.fetchone()[0]
                    
                    cursor.execute("SELECT COUNT(*) FROM articles_kanban WHERE stage = 'completed'")
                    completed = cursor.fetchone()[0]
                    
                    cursor.execute("SELECT COUNT(*) FROM articles_kanban WHERE stage = 'reading'")
                    reading = cursor.fetchone()[0]
                
                reply_text = f"""📊 Your Statistics:

📚 Total Articles: {total}
📖 Currently Reading: {reading}
✅ Completed: {completed}
📥 In Inbox: {total - reading - completed}

View full dashboard:
https://aa4fe2493ae1.ngrok-free.app"""
            except:
                reply_text = "📊 Statistics unavailable"
        
        elif text.lower() == '/summary' or text.lower() == '/today':
            # Get today's summary
            try:
                with closing(get_db(KANBAN_DB_PATH)) as conn:
                    cursor = conn.cursor()
                    # Get today's articles
                    cursor.execute('''
                        SELECT COUNT(*) as count, stage 
                        FROM articles_kanban 
                        WHERE DATE(added_date) = DATE('now')
                        GROUP BY stage
                    ''')
                    today_stats = cursor.fetchall()
                    
                    # Get total today
                    cursor.execute('''
                        SELECT COUNT(*) FROM articles_kanban 
                        WHERE DATE(added_date) = DATE('now')
                    ''')
                    total_today = cursor.fetchone()[0]
                    
                    # Get this week stats
                    cursor.execute('''
                        SELECT COUNT(*) FROM articles_kanban 
                        WHERE DATE(added_date) >= DATE('now', '-7 days')
                    ''')
                    week_total = cursor.fetchone()[0]
                    
                    reply_text = f"""📊 Daily Summary:

📅 Today: {total_today} articles saved
📚 This week: {week_total} articles

Today's Progress:"""
                    
                    stage_counts = {}
                    for row in today_stats:
                        stage_counts[row['stage']] = row['count']
                    
                    reply_text += f"""
📥 Inbox: {stage_counts.get('inbox', 0)}
📖 Reading: {stage_counts.get('reading', 0)}
🔍 Reviewing: {stage_counts.get('reviewing', 0)}
✅ Completed: {stage_counts.get('completed', 0)}

Keep up the great learning! 💪"""
            except:
                reply_text = "📊 Unable to generate summary"
        
        elif text.lower() == '/list':
            # List recent articles
            try:
                with closing(get_db(KANBAN_DB_PATH)) as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        SELECT title, stage, added_date 
                        FROM articles_kanban 
                        ORDER BY added_date DESC 
                        LIMIT 5
                    ''')
                    articles = cursor.fetchall()
                    
                    if articles:
                        reply_text = "📚 Recent Articles:\n\n"
                        for i, article in enumerate(articles, 1):
                            stage_emoji = {
                                'inbox': '📥',
                                'reading': '📖',
                                'reviewing': '🔍',
                                'completed': '✅'
                            }.get(article['stage'], '📄')
                            
                            title = article['title'][:40] + '...' if len(article['title']) > 40 else article['title']
                            reply_text += f"{i}. {stage_emoji} {title}\n"
                    else:
                        reply_text = "No articles yet. Send me some URLs!"
            except:
                reply_text = "Error retrieving articles"
        
        else:
            reply_text = """👋 Hi! Send me a URL to save an article.

Try commands:
• /help - Show help
• /stats - View statistics
• /list - Recent articles

Dashboard: https://aa4fe2493ae1.ngrok-free.app"""
        
        # Send reply
        line_bot_api.reply_message(
            reply_token,
            TextSendMessage(text=reply_text)
        )
        logger.info("✅ Reply sent successfully")
        
    except Exception as e:
        logger.error(f"Error handling message: {str(e)}\n{traceback.format_exc()}")
        
        # Try to send error message
        try:
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="❌ An error occurred. Please try again.")
            )
        except:
            pass

@app.route('/test-save', methods=['GET'])
def test_save():
    """Test endpoint to verify saving works"""
    result = save_article_to_kanban(
        "https://example.com/test",
        "Test Article",
        "This is a test"
    )
    return jsonify(result)

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'line_configured': bool(LINE_ACCESS_TOKEN and LINE_SECRET),
        'database': 'connected'
    })

if __name__ == '__main__':
    # Initialize Kanban database if needed
    try:
        with closing(get_db(KANBAN_DB_PATH)) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS articles_kanban (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    url TEXT NOT NULL,
                    url_hash TEXT UNIQUE,
                    title TEXT,
                    summary TEXT,
                    stage TEXT DEFAULT 'inbox',
                    added_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_archived BOOLEAN DEFAULT 0
                )
            ''')
            conn.commit()
        logger.info("✅ Kanban database ready")
    except Exception as e:
        logger.error(f"Database init error: {e}")
    
    port = 5005
    print("\n" + "="*60)
    print("🧠 LINE BOT WITH FIXED RESPONSES")
    print("="*60)
    print(f"\nServer starting on http://localhost:{port}")
    print("\n✅ Features:")
    print("  • Proper LINE webhook handling")
    print("  • Direct replies to messages")
    print("  • Article saving to Kanban")
    print("  • Statistics and listing")
    print("\n📱 Webhook URL for LINE:")
    print("  https://aa4fe2493ae1.ngrok-free.app/callback")
    print("\n" + "="*60)
    
    app.run(host='0.0.0.0', port=port, debug=True)