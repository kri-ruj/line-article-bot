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
            'reading_time': max(1, words // 200),  # Assume 200 words per minute
            'text': text[:3000]  # First 3000 chars for AI analysis
        }
    except Exception as e:
        logger.error(f"Error extracting article info: {e}")
        # Return defaults for problematic URLs (like Facebook)
        return {
            'title': url.split('/')[-2] if '/' in url else 'Article',
            'summary': '',
            'word_count': 0,
            'reading_time': 5,
            'text': ''
        }

def analyze_article_with_ai(text, title=""):
    """Analyze article with AI for enhanced insights (5x features)"""
    try:
        from openai import OpenAI
        import os
        
        # Check if OpenAI API key is available
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            return None
            
        client = OpenAI(api_key=api_key)
        
        prompt = f"""Analyze this article and provide comprehensive insights:
Title: {title}
Content: {text[:2000]}

Provide analysis in JSON format with these 5 categories:
1. "summary": Brief 2-3 sentence summary
2. "category": Main category (Technology/Business/Health/Science/Entertainment/Politics/Sports/Other)
3. "sentiment": Overall sentiment (positive/neutral/negative) with score 0-100
4. "difficulty": Reading difficulty (elementary/intermediate/advanced/expert)
5. "key_insights": List of 3-5 main takeaways
6. "topics": List of main topics/keywords (5-10 items)
7. "target_audience": Who would benefit most from this article
8. "quality_score": Article quality 0-100 based on clarity, depth, accuracy
9. "action_items": Practical things reader can do after reading
10. "related_concepts": Concepts reader should explore next"""

        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are an expert content analyst. Respond only with valid JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=500
        )
        
        import json
        result = json.loads(response.choices[0].message.content)
        logger.info(f"✅ AI analysis completed for: {title}")
        return result
        
    except Exception as e:
        logger.error(f"AI analysis error: {e}")
        return None

def save_article_to_kanban(url, title="", summary=""):
    """Save article to Kanban database with AI analysis"""
    url_hash = hashlib.md5(url.encode()).hexdigest()
    
    # Extract article info if not provided
    if not title or not summary:
        article_info = extract_article_info(url)
        title = title or article_info['title']
        summary = summary or article_info['summary']
        word_count = article_info['word_count']
        reading_time = article_info['reading_time']
        text = article_info.get('text', '')
    else:
        word_count = len(summary.split()) if summary else 0
        reading_time = max(1, word_count // 200)
        text = summary
    
    # Perform AI analysis
    ai_analysis = analyze_article_with_ai(text, title) if text else None
    
    try:
        with closing(get_db(KANBAN_DB_PATH)) as conn:
            cursor = conn.cursor()
            
            # Check if exists
            cursor.execute('SELECT id FROM articles_kanban WHERE url_hash = ?', (url_hash,))
            existing = cursor.fetchone()
            
            if existing:
                return {'status': 'duplicate', 'id': existing[0]}
            
            # Prepare AI analysis data
            if ai_analysis:
                ai_summary = ai_analysis.get('summary', summary)[:500]
                category = ai_analysis.get('category', 'Other')
                sentiment = f"{ai_analysis.get('sentiment', 'neutral')}"
                difficulty = ai_analysis.get('difficulty', 'intermediate')
                key_insights = ', '.join(ai_analysis.get('key_insights', []))[:500]
                topics = ', '.join(ai_analysis.get('topics', []))[:200]
                quality_score = ai_analysis.get('quality_score', 0)
            else:
                ai_summary = summary[:500]
                category = 'Other'
                sentiment = 'neutral'
                difficulty = 'intermediate'
                key_insights = ''
                topics = ''
                quality_score = 0
            
            # Insert new article with AI analysis
            cursor.execute('''
                INSERT INTO articles_kanban (
                    url, url_hash, title, summary, word_count, reading_time,
                    stage, added_date, category, sentiment, difficulty,
                    key_insights, topics, quality_score
                ) VALUES (?, ?, ?, ?, ?, ?, 'inbox', CURRENT_TIMESTAMP, ?, ?, ?, ?, ?, ?)
            ''', (url, url_hash, title[:200], ai_summary, word_count, reading_time,
                  category, sentiment, difficulty, key_insights, topics, quality_score))
            
            conn.commit()
            article_id = cursor.lastrowid
            
            logger.info(f"✅ Article saved to Kanban: {title}")
            return {
                'status': 'saved', 
                'id': article_id, 
                'title': title,
                'ai_analysis': ai_analysis or {
                    'summary': ai_summary,
                    'category': category,
                    'sentiment': sentiment,
                    'difficulty': difficulty,
                    'topics': topics,
                    'quality_score': quality_score
                }
            }
            
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
                # Get AI insights if available
                ai_info = result.get('ai_analysis', {})
                
                reply_text = f"""✅ Article Saved & Analyzed!

📚 {result.get('title', 'Article')[:50]}...

🤖 AI Insights:
• Category: {ai_info.get('category', 'Other')}
• Difficulty: {ai_info.get('difficulty', 'intermediate')}
• Sentiment: {ai_info.get('sentiment', 'neutral')}
• Quality: {ai_info.get('quality_score', 0)}/100

📝 Summary:
{ai_info.get('summary', 'Article saved to your reading list.')[:200]}

📋 Key Topics:
{ai_info.get('topics', 'General content')}

View full analysis: https://aa4fe2493ae1.ngrok-free.app"""
                
            elif result['status'] == 'duplicate':
                reply_text = "📚 This article is already in your collection!"
                
            else:
                reply_text = f"❌ Error saving article: {result.get('message', 'Unknown error')}"
        
        elif text.lower() == '/help':
            reply_text = """🧠 Article Intelligence Bot (5x AI Enhanced)

📝 Commands:
• Send any URL - Save & AI analyze article
• /help - Show this message
• /list - Recent articles with AI insights
• /stats - Your statistics
• /ai - Show AI analysis for recent article
• /summary - Today's progress summary

🤖 AI Features (5x Enhanced):
• Smart summarization
• Category classification
• Sentiment analysis
• Reading difficulty assessment
• Key insights extraction
• Topic identification
• Quality scoring
• Target audience detection
• Action items generation
• Related concepts suggestion

📊 Dashboard:
https://aa4fe2493ae1.ngrok-free.app"""
        
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
        
        elif text.lower() == '/ai':
            # Show AI analysis for most recent article
            try:
                with closing(get_db(KANBAN_DB_PATH)) as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        SELECT title, category, sentiment, difficulty, 
                               key_insights, topics, quality_score, summary
                        FROM articles_kanban 
                        ORDER BY added_date DESC 
                        LIMIT 1
                    ''')
                    article = cursor.fetchone()
                    
                    if article:
                        reply_text = f"""🤖 AI Analysis - Latest Article

📚 {article['title'][:50]}...

📊 Analysis:
• Category: {article['category']}
• Difficulty: {article['difficulty']}
• Sentiment: {article['sentiment']}
• Quality Score: {article['quality_score']}/100

📝 Summary:
{article['summary'][:300]}...

🔑 Key Insights:
{article['key_insights'][:200]}

#️⃣ Topics:
{article['topics']}"""
                    else:
                        reply_text = "No articles found. Send me a URL to analyze!"
            except:
                reply_text = "Unable to retrieve AI analysis"
        
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
                    word_count INTEGER DEFAULT 0,
                    reading_time INTEGER DEFAULT 0,
                    stage TEXT DEFAULT 'inbox',
                    added_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_archived BOOLEAN DEFAULT 0,
                    category TEXT DEFAULT 'Other',
                    sentiment TEXT DEFAULT 'neutral',
                    difficulty TEXT DEFAULT 'intermediate',
                    key_insights TEXT,
                    topics TEXT,
                    quality_score INTEGER DEFAULT 0,
                    target_audience TEXT,
                    action_items TEXT,
                    related_concepts TEXT,
                    priority TEXT DEFAULT 'medium',
                    study_notes TEXT,
                    key_learnings TEXT,
                    total_study_time INTEGER DEFAULT 0,
                    stage_updated TIMESTAMP
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