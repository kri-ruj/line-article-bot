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
from collections import Counter
from openai import OpenAI

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Configuration
LINE_ACCESS_TOKEN = os.getenv('LINE_CHANNEL_ACCESS_TOKEN')
LINE_REPLY_URL = 'https://api.line.me/v2/bot/message/reply'
LINE_PUSH_URL = 'https://api.line.me/v2/bot/message/push'
DATABASE_PATH = 'articles_enhanced.db'
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '')

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize OpenAI client
openai_client = None
if OPENAI_API_KEY and len(OPENAI_API_KEY) > 20:
    openai_client = OpenAI(api_key=OPENAI_API_KEY)

# Database helper
def get_db():
    """Get database connection with proper settings"""
    conn = sqlite3.connect(DATABASE_PATH, timeout=30.0, isolation_level=None)
    conn.execute('PRAGMA journal_mode=WAL')
    conn.execute('PRAGMA busy_timeout=30000')
    conn.row_factory = sqlite3.Row
    return conn

# Initialize enhanced database
def init_database():
    with closing(get_db()) as conn:
        cursor = conn.cursor()
        
        # Enhanced articles table with AI fields
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS articles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                url TEXT NOT NULL,
                url_hash TEXT UNIQUE,
                title TEXT,
                content TEXT,
                summary TEXT,
                
                -- AI Classification Fields
                category TEXT,
                subcategory TEXT,
                topics TEXT,  -- JSON array of topics
                tags TEXT,    -- JSON array of auto-generated tags
                
                -- Entity Extraction
                people TEXT,      -- JSON array of mentioned people
                organizations TEXT,  -- JSON array of mentioned orgs
                locations TEXT,   -- JSON array of locations
                technologies TEXT,  -- JSON array of tech mentioned
                
                -- Content Analysis
                sentiment TEXT,  -- positive/negative/neutral
                sentiment_score REAL,  -- -1 to 1
                mood TEXT,      -- informative/urgent/casual/technical
                complexity_level TEXT,  -- beginner/intermediate/advanced
                
                -- Key Information
                key_points TEXT,  -- JSON array of main points
                action_items TEXT,  -- JSON array of actionable items
                questions_raised TEXT,  -- JSON array of questions
                
                -- Metadata
                author TEXT,
                published_date TEXT,
                reading_time INTEGER,
                word_count INTEGER,
                language TEXT,
                
                -- User Interaction
                saved_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_read BOOLEAN DEFAULT 0,
                user_notes TEXT,
                user_rating INTEGER,
                
                -- Connections
                related_articles TEXT,  -- JSON array of related article IDs
                follow_up_reminder TEXT,
                
                -- Source Analysis
                source_credibility TEXT,
                source_type TEXT  -- news/blog/research/social/documentation
            )
        ''')
        
        # Knowledge graph table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS knowledge_graph (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_article_id INTEGER,
                target_article_id INTEGER,
                relationship_type TEXT,  -- similar/contradicts/expands/references
                strength REAL,  -- 0 to 1
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (source_article_id) REFERENCES articles(id),
                FOREIGN KEY (target_article_id) REFERENCES articles(id)
            )
        ''')
        
        # Insights table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS insights (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                insight_type TEXT,  -- trend/pattern/anomaly/recommendation
                title TEXT,
                description TEXT,
                related_articles TEXT,  -- JSON array of article IDs
                importance_score REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_dismissed BOOLEAN DEFAULT 0
            )
        ''')
        
        # Learning patterns table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS learning_patterns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                pattern_type TEXT,  -- reading_time/topic_preference/complexity_preference
                pattern_data TEXT,  -- JSON
                confidence REAL,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create indexes
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_topics ON articles(topics)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_sentiment ON articles(sentiment)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_category ON articles(category, subcategory)')
        
        conn.commit()
    logger.info("Enhanced database initialized successfully")

# AI Analysis Functions
def analyze_with_ai(content, title, url):
    """Comprehensive AI analysis of article content"""
    if not openai_client or not content:
        return {}
    
    try:
        # Comprehensive analysis prompt
        analysis_prompt = f"""Analyze this article and provide a detailed JSON response with the following information:

Title: {title}
URL: {url}
Content: {content[:3000]}

Return a JSON object with these fields:
{{
    "summary": "2-3 sentence summary",
    "category": "main category (Technology/Business/Science/Health/Politics/Entertainment/Sports/Education/Other)",
    "subcategory": "specific subcategory",
    "topics": ["list", "of", "main", "topics"],
    "tags": ["relevant", "hashtag", "style", "tags"],
    "people": ["mentioned", "people", "names"],
    "organizations": ["mentioned", "companies", "organizations"],
    "locations": ["mentioned", "places", "countries"],
    "technologies": ["mentioned", "technologies", "tools", "platforms"],
    "sentiment": "positive/negative/neutral",
    "sentiment_score": 0.0,  // -1 to 1
    "mood": "informative/urgent/casual/technical/analytical",
    "complexity_level": "beginner/intermediate/advanced",
    "key_points": ["main", "takeaway", "points"],
    "action_items": ["actionable", "items", "if", "any"],
    "questions_raised": ["questions", "the", "article", "raises"],
    "source_type": "news/blog/research/social/documentation/tutorial",
    "source_credibility": "high/medium/low",
    "language": "detected language",
    "recommended_follow_up": "suggested next action or related reading"
}}

Be thorough and accurate. Extract as much valuable information as possible."""

        response = openai_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are an expert content analyst who extracts detailed insights from articles."},
                {"role": "user", "content": analysis_prompt}
            ],
            max_tokens=1000,
            temperature=0.3,
            response_format={"type": "json_object"}
        )
        
        analysis = json.loads(response.choices[0].message.content)
        logger.info(f"AI analysis completed for: {title[:50]}")
        return analysis
        
    except Exception as e:
        logger.error(f"AI analysis error: {str(e)}")
        return {}

def generate_insights(user_id):
    """Generate insights from user's article collection"""
    with closing(get_db()) as conn:
        cursor = conn.cursor()
        
        # Get user's recent articles
        cursor.execute('''
            SELECT topics, tags, category, sentiment, saved_at
            FROM articles
            WHERE user_id = ? AND saved_at > datetime('now', '-7 days')
        ''', (user_id,))
        
        recent_articles = cursor.fetchall()
        
        if not recent_articles:
            return []
        
        insights = []
        
        # Topic frequency analysis
        all_topics = []
        for article in recent_articles:
            if article['topics']:
                try:
                    topics = json.loads(article['topics'])
                    all_topics.extend(topics)
                except:
                    pass
        
        if all_topics:
            topic_counts = Counter(all_topics)
            trending = topic_counts.most_common(3)
            if trending:
                insights.append({
                    'type': 'trend',
                    'title': 'Trending Topics',
                    'description': f"You've been reading a lot about: {', '.join([t[0] for t in trending])}",
                    'importance': 0.8
                })
        
        # Sentiment analysis
        sentiments = [a['sentiment'] for a in recent_articles if a['sentiment']]
        if sentiments:
            sentiment_counts = Counter(sentiments)
            dominant = sentiment_counts.most_common(1)[0]
            insights.append({
                'type': 'pattern',
                'title': 'Reading Mood',
                'description': f"Most of your recent articles are {dominant[0]} ({dominant[1]}/{len(sentiments)} articles)",
                'importance': 0.6
            })
        
        # Category diversity
        categories = [a['category'] for a in recent_articles if a['category']]
        if categories:
            unique_cats = len(set(categories))
            if unique_cats == 1:
                insights.append({
                    'type': 'recommendation',
                    'title': 'Diversify Your Reading',
                    'description': f"You've only read {categories[0]} articles recently. Try exploring other topics!",
                    'importance': 0.7
                })
        
        return insights

def find_related_articles(article_id, article_data):
    """Find related articles using AI similarity"""
    with closing(get_db()) as conn:
        cursor = conn.cursor()
        
        # Get other articles
        cursor.execute('''
            SELECT id, title, topics, tags, category
            FROM articles
            WHERE id != ?
            ORDER BY saved_at DESC
            LIMIT 20
        ''', (article_id,))
        
        other_articles = cursor.fetchall()
        related = []
        
        for other in other_articles:
            similarity = calculate_similarity(article_data, other)
            if similarity > 0.3:
                related.append({
                    'id': other['id'],
                    'title': other['title'],
                    'similarity': similarity
                })
        
        # Sort by similarity
        related.sort(key=lambda x: x['similarity'], reverse=True)
        return [r['id'] for r in related[:5]]

def calculate_similarity(article1, article2):
    """Calculate similarity between two articles"""
    score = 0.0
    
    # Category match
    if article1.get('category') == article2.get('category'):
        score += 0.3
    
    # Topic overlap
    try:
        topics1 = set(json.loads(article1.get('topics', '[]')))
        topics2 = set(json.loads(article2.get('topics', '[]')))
        if topics1 and topics2:
            overlap = len(topics1.intersection(topics2)) / len(topics1.union(topics2))
            score += overlap * 0.4
    except:
        pass
    
    # Tag overlap
    try:
        tags1 = set(json.loads(article1.get('tags', '[]')))
        tags2 = set(json.loads(article2.get('tags', '[]')))
        if tags1 and tags2:
            overlap = len(tags1.intersection(tags2)) / len(tags1.union(tags2))
            score += overlap * 0.3
    except:
        pass
    
    return score

def extract_article_content(url):
    """Extract article content from URL"""
    try:
        url = url.strip()
        response = requests.get(url, timeout=10, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Remove scripts and styles
        for script in soup(["script", "style"]):
            script.decompose()
        
        # Extract title
        title = soup.find('title')
        title = title.get_text() if title else urlparse(url).netloc
        
        # Extract content
        content_tags = soup.find_all(['article', 'main', 'div'], class_=re.compile('content|article|post|entry'))
        if not content_tags:
            content_tags = soup.find_all('p')
        
        text_content = ' '.join([tag.get_text() for tag in content_tags[:100]])
        text_content = re.sub(r'\s+', ' ', text_content).strip()
        
        # Basic metrics
        word_count = len(text_content.split())
        reading_time = max(1, word_count // 200)
        
        return {
            'title': title[:200],
            'content': text_content[:10000],  # Increased for better AI analysis
            'word_count': word_count,
            'reading_time': reading_time
        }
    except Exception as e:
        logger.error(f"Error extracting article: {str(e)}")
        return {
            'title': url,
            'content': '',
            'word_count': 0,
            'reading_time': 1
        }

def save_enhanced_article(user_id, url, article_info, ai_analysis):
    """Save article with all AI enhancements"""
    url_hash = hashlib.md5(url.encode()).hexdigest()
    
    try:
        with closing(get_db()) as conn:
            cursor = conn.cursor()
            
            # Check if exists
            cursor.execute('SELECT id FROM articles WHERE url_hash = ?', (url_hash,))
            existing = cursor.fetchone()
            
            if existing:
                return {'status': 'duplicate', 'id': existing['id']}
            
            # Prepare all fields
            cursor.execute('''
                INSERT INTO articles (
                    user_id, url, url_hash, title, content, summary,
                    category, subcategory, topics, tags,
                    people, organizations, locations, technologies,
                    sentiment, sentiment_score, mood, complexity_level,
                    key_points, action_items, questions_raised,
                    reading_time, word_count, language,
                    source_type, source_credibility
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                user_id, url, url_hash,
                article_info.get('title'),
                article_info.get('content'),
                ai_analysis.get('summary', 'No summary available'),
                ai_analysis.get('category', 'General'),
                ai_analysis.get('subcategory'),
                json.dumps(ai_analysis.get('topics', [])),
                json.dumps(ai_analysis.get('tags', [])),
                json.dumps(ai_analysis.get('people', [])),
                json.dumps(ai_analysis.get('organizations', [])),
                json.dumps(ai_analysis.get('locations', [])),
                json.dumps(ai_analysis.get('technologies', [])),
                ai_analysis.get('sentiment'),
                ai_analysis.get('sentiment_score', 0),
                ai_analysis.get('mood'),
                ai_analysis.get('complexity_level'),
                json.dumps(ai_analysis.get('key_points', [])),
                json.dumps(ai_analysis.get('action_items', [])),
                json.dumps(ai_analysis.get('questions_raised', [])),
                article_info.get('reading_time'),
                article_info.get('word_count'),
                ai_analysis.get('language', 'English'),
                ai_analysis.get('source_type'),
                ai_analysis.get('source_credibility')
            ))
            
            conn.commit()
            article_id = cursor.lastrowid
            
            # Find related articles
            article_data = {
                'category': ai_analysis.get('category'),
                'topics': json.dumps(ai_analysis.get('topics', [])),
                'tags': json.dumps(ai_analysis.get('tags', []))
            }
            related = find_related_articles(article_id, article_data)
            
            if related:
                cursor.execute(
                    'UPDATE articles SET related_articles = ? WHERE id = ?',
                    (json.dumps(related), article_id)
                )
                conn.commit()
            
            # Generate insights
            user_insights = generate_insights(user_id)
            for insight in user_insights:
                cursor.execute('''
                    INSERT INTO insights (user_id, insight_type, title, description, importance_score)
                    VALUES (?, ?, ?, ?, ?)
                ''', (user_id, insight['type'], insight['title'], insight['description'], insight['importance']))
            
            return {
                'status': 'saved',
                'id': article_id,
                'analysis': ai_analysis,
                'related': related
            }
            
    except Exception as e:
        logger.error(f"Database error: {str(e)}")
        return {'status': 'error', 'message': str(e)}

# Flask routes
@app.route("/", methods=['GET'])
def home():
    """Enhanced dashboard with AI insights"""
    with closing(get_db()) as conn:
        cursor = conn.cursor()
        
        # Statistics
        cursor.execute('SELECT COUNT(*) as count FROM articles')
        total_articles = cursor.fetchone()['count']
        
        # Topic cloud
        cursor.execute('SELECT topics FROM articles WHERE topics IS NOT NULL LIMIT 100')
        all_topics = []
        for row in cursor.fetchall():
            try:
                topics = json.loads(row['topics'])
                all_topics.extend(topics)
            except:
                pass
        
        topic_counts = Counter(all_topics).most_common(20)
        
        # Recent insights
        cursor.execute('''
            SELECT title, description, importance_score
            FROM insights
            WHERE is_dismissed = 0
            ORDER BY created_at DESC
            LIMIT 5
        ''')
        insights = cursor.fetchall()
        
        # Category distribution
        cursor.execute('''
            SELECT category, COUNT(*) as count
            FROM articles
            GROUP BY category
            ORDER BY count DESC
        ''')
        categories = cursor.fetchall()
    
    html = f'''
    <!DOCTYPE html>
    <html>
    <head>
        <title>AI-Enhanced Article Bot</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); }}
            .container {{ max-width: 1400px; margin: 0 auto; background: white; padding: 30px; border-radius: 15px; box-shadow: 0 20px 60px rgba(0,0,0,0.3); }}
            h1 {{ color: #764ba2; font-size: 2.5em; }}
            .stats {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin: 30px 0; }}
            .stat-card {{ padding: 20px; background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); border-radius: 10px; text-align: center; color: white; }}
            .stat-number {{ font-size: 2.5em; font-weight: bold; }}
            .insights {{ background: #f8f9fa; padding: 20px; border-radius: 10px; margin: 20px 0; }}
            .insight {{ padding: 10px; margin: 10px 0; background: white; border-left: 4px solid #764ba2; }}
            .topic-cloud {{ display: flex; flex-wrap: wrap; gap: 10px; margin: 20px 0; }}
            .topic {{ padding: 5px 15px; background: #667eea; color: white; border-radius: 20px; font-size: 0.9em; }}
            .category-chart {{ display: flex; gap: 10px; margin: 20px 0; align-items: flex-end; height: 200px; }}
            .bar {{ flex: 1; background: linear-gradient(to top, #667eea, #764ba2); color: white; text-align: center; padding: 10px; border-radius: 5px 5px 0 0; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🧠 AI-Enhanced Article Intelligence System</h1>
            <p>Advanced content analysis with GPT-3.5 • Entity extraction • Sentiment analysis • Knowledge graph</p>
            
            <div class="stats">
                <div class="stat-card">
                    <div class="stat-number">{total_articles}</div>
                    <div>Articles Analyzed</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">{len(topic_counts)}</div>
                    <div>Topics Discovered</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">{len(categories)}</div>
                    <div>Categories</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">{len(insights)}</div>
                    <div>Active Insights</div>
                </div>
            </div>
            
            <h2>🎯 AI Insights</h2>
            <div class="insights">
    '''
    
    for insight in insights:
        importance = insight['importance_score'] * 100
        html += f'''
                <div class="insight">
                    <strong>{insight['title']}</strong> (Importance: {importance:.0f}%)
                    <p>{insight['description']}</p>
                </div>
        '''
    
    html += f'''
            </div>
            
            <h2>☁️ Topic Cloud</h2>
            <div class="topic-cloud">
    '''
    
    for topic, count in topic_counts[:20]:
        size = min(1.5, 0.8 + (count / 10))
        html += f'<span class="topic" style="font-size: {size}em">{topic} ({count})</span>'
    
    html += '''
            </div>
            
            <h2>📊 Category Distribution</h2>
            <div class="category-chart">
    '''
    
    max_count = max([c['count'] for c in categories]) if categories else 1
    for cat in categories[:8]:
        height = (cat['count'] / max_count) * 100
        html += f'''
                <div class="bar" style="height: {height}%">
                    <div>{cat['category']}</div>
                    <div style="font-size: 2em">{cat['count']}</div>
                </div>
        '''
    
    html += '''
            </div>
            
            <p style="margin-top: 40px; text-align: center; color: #666;">
                <a href="/api/topics">Topics API</a> | 
                <a href="/api/insights">Insights API</a> | 
                <a href="/api/graph">Knowledge Graph</a>
            </p>
        </div>
    </body>
    </html>
    '''
    return html

@app.route('/callback', methods=['POST'])
def callback():
    """Handle LINE webhooks with AI enhancement"""
    body = request.get_data(as_text=True)
    
    try:
        body_json = json.loads(body)
    except:
        return 'OK', 200
    
    if body_json.get('events'):
        for event in body_json['events']:
            user_id = event.get('source', {}).get('userId', 'unknown')
            
            if event.get('type') == 'message':
                message = event.get('message', {})
                reply_token = event.get('replyToken')
                
                if message.get('type') == 'text':
                    text = message.get('text', '')
                    handle_enhanced_message(user_id, text, reply_token)
    
    return 'OK', 200

def handle_enhanced_message(user_id, text, reply_token):
    """Handle messages with AI enhancement"""
    reply_text = ""
    
    # Check for URLs
    url_pattern = r'https?://(?:[-\w.])+(?:\:\d+)?(?:[/\w\s._~%!$&\'()*+,;=:@-]+)?'
    urls = re.findall(url_pattern, text)
    
    if urls:
        url = urls[0].strip()
        logger.info(f"Processing URL with AI: {url}")
        
        # Extract content
        article_info = extract_article_content(url)
        
        # AI analysis
        ai_analysis = analyze_with_ai(
            article_info.get('content', ''),
            article_info.get('title', ''),
            url
        )
        
        # Save with enhancements
        result = save_enhanced_article(user_id, url, article_info, ai_analysis)
        
        if result['status'] == 'saved':
            analysis = result.get('analysis', {})
            
            reply_text = f"🧠 AI-Enhanced Article Saved!\n\n"
            reply_text += f"📚 {article_info.get('title', 'Article')[:60]}...\n\n"
            
            # Summary
            reply_text += f"📝 Summary:\n{analysis.get('summary', 'Processing...')}\n\n"
            
            # Categories and topics
            reply_text += f"📂 Category: {analysis.get('category', 'General')} > {analysis.get('subcategory', 'N/A')}\n"
            topics = analysis.get('topics', [])[:3]
            if topics:
                reply_text += f"🏷️ Topics: {', '.join(topics)}\n"
            
            # Sentiment and mood
            sentiment = analysis.get('sentiment', 'neutral')
            mood = analysis.get('mood', 'informative')
            reply_text += f"😊 Sentiment: {sentiment} | Mood: {mood}\n"
            
            # Key points
            key_points = analysis.get('key_points', [])
            if key_points:
                reply_text += f"\n🎯 Key Points:\n"
                for i, point in enumerate(key_points[:3], 1):
                    reply_text += f"{i}. {point[:50]}...\n"
            
            # Action items
            actions = analysis.get('action_items', [])
            if actions:
                reply_text += f"\n✅ Action Items:\n"
                for action in actions[:2]:
                    reply_text += f"• {action}\n"
            
            # Entities
            people = analysis.get('people', [])
            orgs = analysis.get('organizations', [])
            tech = analysis.get('technologies', [])
            
            if people or orgs or tech:
                reply_text += f"\n🔍 Entities Found:\n"
                if people:
                    reply_text += f"👤 People: {', '.join(people[:3])}\n"
                if orgs:
                    reply_text += f"🏢 Orgs: {', '.join(orgs[:3])}\n"
                if tech:
                    reply_text += f"💻 Tech: {', '.join(tech[:3])}\n"
            
            # Related articles
            related = result.get('related', [])
            if related:
                reply_text += f"\n📖 Related articles found: {len(related)}\n"
            
            reply_text += f"\n⏱️ {article_info.get('reading_time', 1)} min read"
            reply_text += f" | 📊 {article_info.get('word_count', 0)} words"
            reply_text += f"\n🔍 Complexity: {analysis.get('complexity_level', 'N/A')}"
    
    elif text.lower() == '/insights':
        # Get user insights
        insights = generate_insights(user_id)
        if insights:
            reply_text = "🎯 Your Personalized Insights:\n\n"
            for insight in insights[:3]:
                reply_text += f"• {insight['title']}\n  {insight['description']}\n\n"
        else:
            reply_text = "📊 No insights yet. Save more articles to get personalized insights!"
    
    elif text.lower() == '/topics':
        # Get user's top topics
        with closing(get_db()) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT topics FROM articles
                WHERE user_id = ? AND topics IS NOT NULL
            ''', (user_id,))
            
            all_topics = []
            for row in cursor.fetchall():
                try:
                    topics = json.loads(row['topics'])
                    all_topics.extend(topics)
                except:
                    pass
            
            if all_topics:
                topic_counts = Counter(all_topics).most_common(10)
                reply_text = "☁️ Your Top Topics:\n\n"
                for topic, count in topic_counts:
                    reply_text += f"• {topic}: {count} articles\n"
            else:
                reply_text = "No topics analyzed yet. Send me articles!"
    
    elif text.lower() == '/sentiment':
        # Sentiment analysis summary
        with closing(get_db()) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT sentiment, COUNT(*) as count
                FROM articles
                WHERE user_id = ? AND sentiment IS NOT NULL
                GROUP BY sentiment
            ''', (user_id,))
            
            sentiments = cursor.fetchall()
            if sentiments:
                reply_text = "😊 Your Reading Sentiment:\n\n"
                for sent in sentiments:
                    emoji = {'positive': '😊', 'negative': '😔', 'neutral': '😐'}.get(sent['sentiment'], '❓')
                    reply_text += f"{emoji} {sent['sentiment'].title()}: {sent['count']} articles\n"
            else:
                reply_text = "No sentiment data yet. Save more articles!"
    
    elif text.lower() in ['/help', 'help']:
        reply_text = "🧠 AI-Enhanced Article Bot\n\n"
        reply_text += "📝 Commands:\n"
        reply_text += "• Send URL - AI analysis & save\n"
        reply_text += "• /insights - Personal insights\n"
        reply_text += "• /topics - Your top topics\n"
        reply_text += "• /sentiment - Sentiment analysis\n"
        reply_text += "• /list - Recent articles\n"
        reply_text += "• /help - This message\n\n"
        reply_text += "✨ AI Features:\n"
        reply_text += "• GPT-3.5 analysis\n"
        reply_text += "• Entity extraction\n"
        reply_text += "• Sentiment analysis\n"
        reply_text += "• Topic modeling\n"
        reply_text += "• Action items\n"
        reply_text += "• Related articles\n"
        reply_text += "• Personal insights"
    
    else:
        reply_text = "🧠 Send me a URL for AI analysis!\n\nTry /insights or /help"
    
    # Send reply
    if reply_token and reply_text:
        send_reply(reply_token, reply_text[:2000])  # LINE message limit

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

# API endpoints
@app.route('/api/topics', methods=['GET'])
def api_topics():
    """API for topic analysis"""
    with closing(get_db()) as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT topics FROM articles WHERE topics IS NOT NULL')
        
        all_topics = []
        for row in cursor.fetchall():
            try:
                topics = json.loads(row['topics'])
                all_topics.extend(topics)
            except:
                pass
        
        topic_counts = Counter(all_topics).most_common(50)
        return jsonify({
            'topics': [{'name': t, 'count': c} for t, c in topic_counts]
        })

@app.route('/api/insights', methods=['GET'])
def api_insights():
    """API for insights"""
    with closing(get_db()) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM insights
            WHERE is_dismissed = 0
            ORDER BY importance_score DESC, created_at DESC
            LIMIT 20
        ''')
        
        insights = []
        for row in cursor.fetchall():
            insights.append({
                'id': row['id'],
                'type': row['insight_type'],
                'title': row['title'],
                'description': row['description'],
                'importance': row['importance_score'],
                'created_at': row['created_at']
            })
        
        return jsonify({'insights': insights})

@app.route('/api/graph', methods=['GET'])
def api_graph():
    """API for knowledge graph"""
    with closing(get_db()) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT a1.title as source, a2.title as target, kg.relationship_type, kg.strength
            FROM knowledge_graph kg
            JOIN articles a1 ON kg.source_article_id = a1.id
            JOIN articles a2 ON kg.target_article_id = a2.id
            ORDER BY kg.strength DESC
            LIMIT 100
        ''')
        
        edges = []
        for row in cursor.fetchall():
            edges.append({
                'source': row['source'],
                'target': row['target'],
                'type': row['relationship_type'],
                'strength': row['strength']
            })
        
        return jsonify({'edges': edges})

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy', 'ai': 'enabled', 'database': 'enhanced'})

if __name__ == "__main__":
    init_database()
    
    port = int(os.environ.get('PORT', '5001'))
    print("\n" + "="*60)
    print("🧠 AI-ENHANCED ARTICLE INTELLIGENCE SYSTEM")
    print("="*60)
    print(f"\nServer starting on http://localhost:{port}")
    print("\n✨ AI Features:")
    print("  • GPT-3.5 comprehensive analysis")
    print("  • Entity extraction (people, orgs, tech)")
    print("  • Sentiment & mood analysis")
    print("  • Topic modeling & tagging")
    print("  • Key points & action items")
    print("  • Knowledge graph connections")
    print("  • Personal insights generation")
    print("  • Trend detection")
    print("\n" + "="*60)
    
    app.run(host='0.0.0.0', port=port, debug=True)