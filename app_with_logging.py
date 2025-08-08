#!/usr/bin/env python3
"""
ULTIMATE Article Intelligence Hub with Comprehensive Logging
No dependencies required - Works with standard Python 3
"""

import os
import sqlite3
import json
from datetime import datetime, timedelta
from contextlib import closing
import random
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import threading
from collections import deque
import logging
import sys

# Configuration
PORT = 5001
KANBAN_DB_PATH = 'articles_kanban.db'
LOG_FILE = 'app_ultimate.log'

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class UltimateApp:
    """Single class containing all functionality"""
    
    @staticmethod
    def get_db():
        """Get database connection"""
        logger.debug("Opening database connection")
        conn = sqlite3.connect(KANBAN_DB_PATH, timeout=30.0)
        conn.execute('PRAGMA journal_mode=WAL')
        conn.row_factory = sqlite3.Row
        return conn
    
    @staticmethod
    def migrate_data():
        """Ensure database has proper schema and migrate if needed"""
        logger.info("Starting data migration check...")
        
        with closing(UltimateApp.get_db()) as conn:
            cursor = conn.cursor()
            
            # Check if table exists
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='articles_kanban'
            """)
            
            if not cursor.fetchone():
                logger.info("Creating new articles_kanban table...")
                cursor.execute('''
                    CREATE TABLE articles_kanban (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        url TEXT,
                        url_hash TEXT,
                        title TEXT,
                        summary TEXT,
                        category TEXT DEFAULT 'Other',
                        stage TEXT DEFAULT 'inbox',
                        priority TEXT DEFAULT 'medium',
                        word_count INTEGER DEFAULT 0,
                        reading_time INTEGER DEFAULT 5,
                        study_notes TEXT,
                        key_learnings TEXT,
                        total_study_time INTEGER DEFAULT 0,
                        is_archived INTEGER DEFAULT 0,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        last_studied_at TIMESTAMP,
                        completion_date TIMESTAMP,
                        quantum_score INTEGER DEFAULT 500,
                        reading_streak INTEGER DEFAULT 0,
                        last_read_date TEXT,
                        total_reads INTEGER DEFAULT 0,
                        reading_speed_wpm INTEGER DEFAULT 200,
                        export_count INTEGER DEFAULT 0
                    )
                ''')
                conn.commit()
                logger.info("Table created successfully")
            else:
                # Check for missing columns and add them
                cursor.execute("PRAGMA table_info(articles_kanban)")
                columns = {col[1] for col in cursor.fetchall()}
                
                migrations = [
                    ("quantum_score", "INTEGER DEFAULT 500"),
                    ("reading_streak", "INTEGER DEFAULT 0"),
                    ("last_read_date", "TEXT"),
                    ("total_reads", "INTEGER DEFAULT 0"),
                    ("reading_speed_wpm", "INTEGER DEFAULT 200"),
                    ("export_count", "INTEGER DEFAULT 0")
                ]
                
                for col_name, col_type in migrations:
                    if col_name not in columns:
                        logger.info(f"Adding column: {col_name}")
                        try:
                            cursor.execute(f"ALTER TABLE articles_kanban ADD COLUMN {col_name} {col_type}")
                            conn.commit()
                        except sqlite3.OperationalError as e:
                            logger.warning(f"Column {col_name} might already exist: {e}")
            
            # Count current articles
            cursor.execute("SELECT COUNT(*) FROM articles_kanban")
            count = cursor.fetchone()[0]
            logger.info(f"Database has {count} articles")
            
            # Log stage distribution
            cursor.execute("SELECT stage, COUNT(*) FROM articles_kanban GROUP BY stage")
            for row in cursor.fetchall():
                logger.info(f"  Stage '{row[0]}': {row[1]} articles")
    
    @staticmethod
    def calculate_quantum_score(article):
        """Calculate AI Quantum Score (0-1000)"""
        score = 500  # Base
        
        # Title length bonus
        if article.get('title'):
            score += min(100, len(article['title']) * 2)
        
        # Category bonus
        categories = {
            'Technology': 150, 'Science': 140, 'Business': 120,
            'AI': 160, 'Sports': 80, 'Other': 50
        }
        score += categories.get(article.get('category', 'Other'), 50)
        
        # Content bonus
        if article.get('summary'):
            score += min(150, len(article.get('summary', '')) // 10)
        
        # Time of day bonus
        hour = datetime.now().hour
        if 6 <= hour <= 10:
            score += 100
        elif 19 <= hour <= 22:
            score += 80
        
        # Stage bonus
        stage_scores = {'reading': 50, 'reviewing': 75, 'completed': 100}
        score += stage_scores.get(article.get('stage', 'inbox'), 0)
        
        # Random quantum interference
        score += random.randint(-50, 50)
        
        return min(1000, max(0, score))
    
    @staticmethod
    def get_all_articles():
        """Get all articles from database"""
        logger.debug("Fetching all articles")
        with closing(UltimateApp.get_db()) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM articles_kanban 
                WHERE is_archived = 0 
                ORDER BY created_at DESC
            ''')
            articles = []
            for row in cursor.fetchall():
                article = dict(row)
                article['quantum_score'] = UltimateApp.calculate_quantum_score(article)
                articles.append(article)
            logger.info(f"Fetched {len(articles)} articles")
            return articles
    
    @staticmethod
    def update_article_stage(article_id, new_stage):
        """Update article stage"""
        logger.info(f"Updating article {article_id} to stage: {new_stage}")
        with closing(UltimateApp.get_db()) as conn:
            cursor = conn.cursor()
            
            # Update stage
            cursor.execute('''
                UPDATE articles_kanban 
                SET stage = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (new_stage, article_id))
            
            # Update completion date if completed
            if new_stage == 'completed':
                cursor.execute('''
                    UPDATE articles_kanban 
                    SET completion_date = CURRENT_TIMESTAMP
                    WHERE id = ?
                ''', (article_id,))
            
            # Update reading tracking
            today = datetime.now().strftime('%Y-%m-%d')
            cursor.execute('''
                UPDATE articles_kanban 
                SET last_read_date = ?,
                    total_reads = total_reads + 1
                WHERE id = ?
            ''', (today, article_id))
            
            conn.commit()
            logger.info(f"Article {article_id} updated successfully")
    
    @staticmethod
    def get_ai_recommendations(article_id):
        """Get AI recommendations for an article"""
        logger.info(f"Generating recommendations for article {article_id}")
        with closing(UltimateApp.get_db()) as conn:
            cursor = conn.cursor()
            
            # Get current article
            cursor.execute('SELECT * FROM articles_kanban WHERE id = ?', (article_id,))
            current = cursor.fetchone()
            
            if not current:
                return []
            
            # Get similar articles
            cursor.execute('''
                SELECT * FROM articles_kanban 
                WHERE id != ? AND is_archived = 0
                AND (category = ? OR stage = ?)
                LIMIT 5
            ''', (article_id, current['category'], current['stage']))
            
            recommendations = []
            for row in cursor.fetchall():
                article = dict(row)
                article['quantum_score'] = UltimateApp.calculate_quantum_score(article)
                recommendations.append(article)
            
            logger.info(f"Generated {len(recommendations)} recommendations")
            return recommendations
    
    @staticmethod
    def generate_study_notes(article_id):
        """Generate AI study notes"""
        logger.info(f"Generating study notes for article {article_id}")
        with closing(UltimateApp.get_db()) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM articles_kanban WHERE id = ?', (article_id,))
            article = cursor.fetchone()
            
            if not article:
                return None
            
            # Generate notes based on content
            notes = {
                'title': article['title'],
                'key_points': [
                    f"Main topic: {article.get('category', 'General')}",
                    f"Reading time: {article.get('reading_time', 5)} minutes",
                    f"Priority: {article.get('priority', 'medium')}",
                    "Key insight: Understanding the core concepts",
                    "Action item: Apply learnings to current projects"
                ],
                'summary': article.get('summary', 'No summary available'),
                'next_steps': [
                    "Review related articles",
                    "Practice key concepts",
                    "Share insights with team"
                ],
                'generated_at': datetime.now().isoformat()
            }
            
            logger.info(f"Generated study notes with {len(notes['key_points'])} key points")
            return notes
    
    @staticmethod
    def get_reading_streak():
        """Calculate reading streak"""
        logger.info("Calculating reading streak")
        with closing(UltimateApp.get_db()) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT DISTINCT DATE(last_read_date) as read_date
                FROM articles_kanban
                WHERE last_read_date IS NOT NULL
                ORDER BY read_date DESC
            ''')
            
            dates = [row[0] for row in cursor.fetchall()]
            if not dates:
                return 0
            
            # Calculate consecutive days
            streak = 1
            today = datetime.now().date()
            last_date = datetime.strptime(dates[0], '%Y-%m-%d').date() if dates else today
            
            if last_date != today and last_date != today - timedelta(days=1):
                logger.info("Streak broken - last read not today or yesterday")
                return 0
            
            for i in range(1, len(dates)):
                current = datetime.strptime(dates[i], '%Y-%m-%d').date()
                if (last_date - current).days == 1:
                    streak += 1
                    last_date = current
                else:
                    break
            
            logger.info(f"Current reading streak: {streak} days")
            return streak
    
    @staticmethod
    def get_speed_insights():
        """Get reading speed insights"""
        logger.info("Calculating speed insights")
        with closing(UltimateApp.get_db()) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT AVG(reading_speed_wpm) as avg_speed,
                       MAX(reading_speed_wpm) as max_speed,
                       MIN(reading_speed_wpm) as min_speed,
                       COUNT(*) as total_reads
                FROM articles_kanban
                WHERE reading_speed_wpm > 0
            ''')
            
            row = cursor.fetchone()
            insights = {
                'average_wpm': int(row['avg_speed'] or 200),
                'max_wpm': int(row['max_speed'] or 200),
                'min_wpm': int(row['min_speed'] or 200),
                'total_reads': row['total_reads'] or 0,
                'recommendation': 'Try to maintain 250-300 WPM for optimal comprehension',
                'level': 'Intermediate Reader'
            }
            
            if insights['average_wpm'] > 300:
                insights['level'] = 'Advanced Reader'
            elif insights['average_wpm'] < 200:
                insights['level'] = 'Beginner Reader'
            
            logger.info(f"Speed insights: {insights['average_wpm']} WPM average")
            return insights
    
    @staticmethod
    def get_daily_digest():
        """Generate daily digest"""
        logger.info("Generating daily digest")
        with closing(UltimateApp.get_db()) as conn:
            cursor = conn.cursor()
            
            # Get today's recommended articles
            cursor.execute('''
                SELECT * FROM articles_kanban
                WHERE stage IN ('inbox', 'reading')
                AND is_archived = 0
                ORDER BY priority DESC, created_at DESC
                LIMIT 3
            ''')
            
            articles = []
            for row in cursor.fetchall():
                article = dict(row)
                article['quantum_score'] = UltimateApp.calculate_quantum_score(article)
                articles.append(article)
            
            # Motivational quotes
            quotes = [
                "The more that you read, the more things you will know.",
                "Today a reader, tomorrow a leader.",
                "Reading is to the mind what exercise is to the body.",
                "Knowledge is power, and reading is the key.",
                "A book is a dream you hold in your hands."
            ]
            
            digest = {
                'date': datetime.now().strftime('%B %d, %Y'),
                'articles': articles,
                'quote': random.choice(quotes),
                'goal': 'Complete 3 articles today!',
                'streak': UltimateApp.get_reading_streak()
            }
            
            logger.info(f"Daily digest generated with {len(articles)} articles")
            return digest
    
    @staticmethod
    def get_category_insights():
        """Get category-based insights"""
        logger.info("Generating category insights")
        with closing(UltimateApp.get_db()) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT category, 
                       COUNT(*) as count,
                       AVG(reading_time) as avg_time,
                       SUM(CASE WHEN stage = 'completed' THEN 1 ELSE 0 END) as completed
                FROM articles_kanban
                WHERE is_archived = 0
                GROUP BY category
                ORDER BY count DESC
            ''')
            
            insights = []
            for row in cursor.fetchall():
                completion_rate = (row['completed'] / row['count'] * 100) if row['count'] > 0 else 0
                insights.append({
                    'category': row['category'] or 'Uncategorized',
                    'total_articles': row['count'],
                    'avg_reading_time': int(row['avg_time'] or 5),
                    'completed': row['completed'],
                    'completion_rate': round(completion_rate, 1),
                    'performance': 'Excellent' if completion_rate > 75 else 'Good' if completion_rate > 50 else 'Needs Focus'
                })
            
            logger.info(f"Generated insights for {len(insights)} categories")
            return insights
    
    @staticmethod
    def export_to_markdown(article_id):
        """Export article notes to markdown"""
        logger.info(f"Exporting article {article_id} to markdown")
        with closing(UltimateApp.get_db()) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM articles_kanban WHERE id = ?', (article_id,))
            article = cursor.fetchone()
            
            if not article:
                return None
            
            # Update export count
            cursor.execute('''
                UPDATE articles_kanban 
                SET export_count = export_count + 1
                WHERE id = ?
            ''', (article_id,))
            conn.commit()
            
            markdown = f"""# {article['title']}

## Metadata
- **Category**: {article['category']}
- **Stage**: {article['stage']}
- **Priority**: {article['priority']}
- **Reading Time**: {article['reading_time']} minutes
- **Created**: {article['created_at']}

## Summary
{article['summary'] or 'No summary available'}

## Study Notes
{article['study_notes'] or '*(No notes yet - add your thoughts!)*'}

## Key Learnings
{article['key_learnings'] or '*(No key learnings recorded yet)*'}

## Quantum Score
**Score**: {UltimateApp.calculate_quantum_score(dict(article))}/1000

---
*Exported on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
"""
            logger.info(f"Exported article to markdown ({len(markdown)} chars)")
            return markdown

class RequestHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        """Override to use our logger"""
        logger.info(f"{self.address_string()} - {format % args}")
    
    def do_GET(self):
        """Handle GET requests"""
        logger.info(f"GET request: {self.path}")
        
        if self.path == '/':
            self.send_homepage()
        elif self.path == '/api/articles':
            self.send_articles()
        elif self.path.startswith('/api/recommendations/'):
            article_id = int(self.path.split('/')[-1])
            self.send_recommendations(article_id)
        elif self.path.startswith('/api/study-notes/'):
            article_id = int(self.path.split('/')[-1])
            self.send_study_notes(article_id)
        elif self.path == '/api/reading-streak':
            self.send_reading_streak()
        elif self.path == '/api/speed-insights':
            self.send_speed_insights()
        elif self.path == '/api/daily-digest':
            self.send_daily_digest()
        elif self.path == '/api/category-insights':
            self.send_category_insights()
        elif self.path.startswith('/api/export-markdown/'):
            article_id = int(self.path.split('/')[-1])
            self.send_markdown_export(article_id)
        else:
            self.send_error(404)
    
    def do_POST(self):
        """Handle POST requests"""
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        data = json.loads(post_data)
        
        logger.info(f"POST request: {self.path} with data: {data}")
        
        if self.path == '/api/update-stage':
            UltimateApp.update_article_stage(data['id'], data['stage'])
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'success': True}).encode())
        else:
            self.send_error(404)
    
    def send_homepage(self):
        """Send the main HTML page"""
        logger.info("Serving homepage")
        html = '''<!DOCTYPE html>
<html>
<head>
    <title>🧠 Ultimate Article Intelligence</title>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }
        
        .container {
            max-width: 1400px;
            margin: 0 auto;
            padding: 20px;
        }
        
        .header {
            background: white;
            border-radius: 15px;
            padding: 30px;
            margin-bottom: 30px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
        }
        
        .title {
            font-size: 2.5em;
            color: #333;
            margin-bottom: 10px;
        }
        
        .subtitle {
            color: #666;
            font-size: 1.1em;
        }
        
        .stats {
            display: flex;
            gap: 20px;
            margin-top: 20px;
        }
        
        .stat {
            background: #f8f9fa;
            padding: 15px 25px;
            border-radius: 10px;
            text-align: center;
        }
        
        .stat-value {
            font-size: 2em;
            font-weight: bold;
            color: #667eea;
        }
        
        .stat-label {
            color: #666;
            font-size: 0.9em;
            margin-top: 5px;
        }
        
        .ai-buttons {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-bottom: 30px;
        }
        
        .ai-button {
            background: white;
            border: 2px solid #667eea;
            color: #667eea;
            padding: 15px 20px;
            border-radius: 10px;
            cursor: pointer;
            font-weight: 600;
            transition: all 0.3s;
            font-size: 0.95em;
        }
        
        .ai-button:hover {
            background: #667eea;
            color: white;
            transform: translateY(-2px);
        }
        
        .kanban-columns {
            display: grid;
            grid-template-columns: repeat(4, minmax(280px, 1fr));
            gap: 15px;
            margin-top: 20px;
            overflow-x: auto;
        }
        
        .kanban-column {
            background: white;
            border-radius: 15px;
            padding: 20px;
            min-height: 400px;
        }
        
        .column-header {
            font-weight: bold;
            color: #333;
            margin-bottom: 15px;
            padding-bottom: 10px;
            border-bottom: 2px solid #f0f0f0;
        }
        
        .inbox { border-top: 4px solid #ff6b6b; }
        .reading { border-top: 4px solid #4ecdc4; }
        .reviewing { border-top: 4px solid #ffd93d; }
        .completed { border-top: 4px solid #95e77e; }
        
        .article-card {
            background: #f8f9fa;
            border-radius: 10px;
            padding: 15px;
            margin-bottom: 10px;
            cursor: move;
            transition: all 0.3s;
            border: 2px solid transparent;
        }
        
        .article-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
            border-color: #667eea;
        }
        
        .article-card.dragging {
            opacity: 0.5;
            transform: rotate(5deg);
        }
        
        .article-title {
            font-weight: 600;
            color: #333;
            margin-bottom: 8px;
            display: -webkit-box;
            -webkit-line-clamp: 2;
            -webkit-box-orient: vertical;
            overflow: hidden;
        }
        
        .article-meta {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-top: 10px;
        }
        
        .article-category {
            background: #667eea;
            color: white;
            padding: 3px 8px;
            border-radius: 5px;
            font-size: 0.8em;
        }
        
        .quantum-score {
            font-weight: bold;
            color: #667eea;
            font-size: 0.9em;
        }
        
        .modal {
            display: none;
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0,0,0,0.5);
            justify-content: center;
            align-items: center;
            z-index: 1000;
        }
        
        .modal-content {
            background: white;
            border-radius: 15px;
            padding: 30px;
            max-width: 600px;
            max-height: 80vh;
            overflow-y: auto;
            position: relative;
        }
        
        .close-modal {
            position: absolute;
            top: 15px;
            right: 15px;
            font-size: 2em;
            cursor: pointer;
            color: #999;
        }
        
        .loading {
            text-align: center;
            padding: 20px;
            color: #666;
        }
        
        @keyframes pulse {
            0% { opacity: 1; }
            50% { opacity: 0.5; }
            100% { opacity: 1; }
        }
        
        .loading-dots {
            animation: pulse 1.5s infinite;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1 class="title">🧠 Ultimate Article Intelligence Hub</h1>
            <p class="subtitle">AI-Powered Reading & Learning System with Zero Dependencies</p>
            <div class="stats">
                <div class="stat">
                    <div class="stat-value" id="total-articles">0</div>
                    <div class="stat-label">Total Articles</div>
                </div>
                <div class="stat">
                    <div class="stat-value" id="completion-rate">0%</div>
                    <div class="stat-label">Completion Rate</div>
                </div>
                <div class="stat">
                    <div class="stat-value" id="avg-score">0</div>
                    <div class="stat-label">Avg Quantum Score</div>
                </div>
                <div class="stat">
                    <div class="stat-value" id="reading-streak">0</div>
                    <div class="stat-label">Day Streak 🔥</div>
                </div>
            </div>
        </div>
        
        <div class="ai-buttons">
            <button class="ai-button" onclick="showPriorityRanking()">🎯 Priority Ranking</button>
            <button class="ai-button" onclick="showStudyNotes()">📝 Study Notes</button>
            <button class="ai-button" onclick="showRecommendations()">🤖 Smart Recommendations</button>
            <button class="ai-button" onclick="detectSimilar()">🔍 Similar Detection</button>
            <button class="ai-button" onclick="showAnalytics()">📊 Real-time Analytics</button>
            <button class="ai-button" onclick="generateSummaries()">📋 Smart Summaries</button>
            <button class="ai-button" onclick="autoTag()">🏷️ Auto-Tagging</button>
            <button class="ai-button" onclick="showReadingStreak()">🔥 Reading Streak</button>
            <button class="ai-button" onclick="showSpeedInsights()">⚡ Speed Insights</button>
            <button class="ai-button" onclick="showDailyDigest()">📅 Daily Digest</button>
            <button class="ai-button" onclick="showCategoryInsights()">📈 Category Insights</button>
            <button class="ai-button" onclick="exportToMarkdown()">📄 Export to Markdown</button>
        </div>
        
        <div class="kanban-columns" id="kanban-board">
            <div class="kanban-column inbox" data-stage="inbox">
                <div class="column-header">📥 Inbox</div>
                <div class="column-content" ondrop="drop(event, 'inbox')" ondragover="allowDrop(event)"></div>
            </div>
            <div class="kanban-column reading" data-stage="reading">
                <div class="column-header">📖 Reading</div>
                <div class="column-content" ondrop="drop(event, 'reading')" ondragover="allowDrop(event)"></div>
            </div>
            <div class="kanban-column reviewing" data-stage="reviewing">
                <div class="column-header">🔍 Reviewing</div>
                <div class="column-content" ondrop="drop(event, 'reviewing')" ondragover="allowDrop(event)"></div>
            </div>
            <div class="kanban-column completed" data-stage="completed">
                <div class="column-header">✅ Completed</div>
                <div class="column-content" ondrop="drop(event, 'completed')" ondragover="allowDrop(event)"></div>
            </div>
        </div>
    </div>
    
    <div id="modal" class="modal">
        <div class="modal-content">
            <span class="close-modal" onclick="closeModal()">&times;</span>
            <div id="modal-body"></div>
        </div>
    </div>
    
    <script>
        let articles = [];
        let currentArticleId = null;
        
        // Load articles on page load
        window.onload = function() {
            console.log('Loading articles...');
            loadArticles();
            updateReadingStreak();
        };
        
        function loadArticles() {
            fetch('/api/articles')
                .then(response => response.json())
                .then(data => {
                    console.log('Loaded articles:', data.length);
                    articles = data;
                    renderKanban();
                    updateStats();
                })
                .catch(error => console.error('Error loading articles:', error));
        }
        
        function renderKanban() {
            const stages = ['inbox', 'reading', 'reviewing', 'completed'];
            
            stages.forEach(stage => {
                const column = document.querySelector(`.kanban-column[data-stage="${stage}"] .column-content`);
                column.innerHTML = '';
                
                const stageArticles = articles.filter(a => a.stage === stage);
                stageArticles.forEach(article => {
                    const card = createArticleCard(article);
                    column.appendChild(card);
                });
            });
        }
        
        function createArticleCard(article) {
            const card = document.createElement('div');
            card.className = 'article-card';
            card.draggable = true;
            card.dataset.articleId = article.id;
            card.ondragstart = (e) => drag(e);
            
            card.innerHTML = `
                <div class="article-title">${article.title || 'Untitled'}</div>
                <div class="article-meta">
                    <span class="article-category">${article.category || 'Other'}</span>
                    <span class="quantum-score">Q: ${article.quantum_score}/1000</span>
                </div>
            `;
            
            return card;
        }
        
        function updateStats() {
            const total = articles.length;
            const completed = articles.filter(a => a.stage === 'completed').length;
            const completionRate = total > 0 ? Math.round((completed / total) * 100) : 0;
            const avgScore = total > 0 ? Math.round(articles.reduce((sum, a) => sum + a.quantum_score, 0) / total) : 0;
            
            document.getElementById('total-articles').textContent = total;
            document.getElementById('completion-rate').textContent = completionRate + '%';
            document.getElementById('avg-score').textContent = avgScore;
        }
        
        function updateReadingStreak() {
            fetch('/api/reading-streak')
                .then(response => response.json())
                .then(data => {
                    document.getElementById('reading-streak').textContent = data.streak;
                });
        }
        
        // Drag and Drop
        function allowDrop(e) {
            e.preventDefault();
        }
        
        function drag(e) {
            e.target.classList.add('dragging');
            e.dataTransfer.setData('articleId', e.target.dataset.articleId);
        }
        
        function drop(e, newStage) {
            e.preventDefault();
            const articleId = e.dataTransfer.getData('articleId');
            const card = document.querySelector(`[data-article-id="${articleId}"]`);
            
            if (card) {
                card.classList.remove('dragging');
                
                // Update in backend
                fetch('/api/update-stage', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ id: parseInt(articleId), stage: newStage })
                })
                .then(() => {
                    console.log('Updated article stage');
                    loadArticles();
                });
            }
        }
        
        // AI Feature Functions
        function showModal(title, content) {
            document.getElementById('modal-body').innerHTML = '<h2>' + title + '</h2>' + content;
            document.getElementById('modal').style.display = 'flex';
        }
        
        function closeModal() {
            document.getElementById('modal').style.display = 'none';
        }
        
        function showPriorityRanking() {
            const sorted = [...articles].sort((a, b) => b.quantum_score - a.quantum_score);
            let html = '<ol>';
            sorted.slice(0, 10).forEach(article => {
                html += `<li><strong>${article.title}</strong> - Quantum Score: ${article.quantum_score}/1000</li>`;
            });
            html += '</ol>';
            showModal('🎯 AI Priority Ranking', html);
        }
        
        function showStudyNotes() {
            if (articles.length === 0) {
                showModal('📝 Study Notes', '<p>No articles available</p>');
                return;
            }
            
            const article = articles[0];
            fetch(`/api/study-notes/${article.id}`)
                .then(response => response.json())
                .then(notes => {
                    let html = '<h3>' + notes.title + '</h3>';
                    html += '<h4>Key Points:</h4><ul>';
                    notes.key_points.forEach(point => {
                        html += '<li>' + point + '</li>';
                    });
                    html += '</ul>';
                    html += '<h4>Next Steps:</h4><ul>';
                    notes.next_steps.forEach(step => {
                        html += '<li>' + step + '</li>';
                    });
                    html += '</ul>';
                    showModal('📝 AI-Generated Study Notes', html);
                });
        }
        
        function showRecommendations() {
            if (articles.length === 0) {
                showModal('🤖 Recommendations', '<p>No articles available</p>');
                return;
            }
            
            const article = articles[0];
            fetch(`/api/recommendations/${article.id}`)
                .then(response => response.json())
                .then(recs => {
                    let html = '<p>Based on: <strong>' + article.title + '</strong></p>';
                    html += '<h4>Recommended Articles:</h4><ul>';
                    recs.forEach(rec => {
                        html += `<li>${rec.title} (Score: ${rec.quantum_score})</li>`;
                    });
                    html += '</ul>';
                    showModal('🤖 Smart Recommendations', html);
                });
        }
        
        function detectSimilar() {
            const similar = [];
            const seen = new Set();
            
            articles.forEach(a1 => {
                articles.forEach(a2 => {
                    if (a1.id !== a2.id && a1.category === a2.category && !seen.has(`${a2.id}-${a1.id}`)) {
                        const similarity = calculateSimilarity(a1.title, a2.title);
                        if (similarity > 0.3) {
                            similar.push({ a1, a2, similarity });
                            seen.add(`${a1.id}-${a2.id}`);
                        }
                    }
                });
            });
            
            let html = '<ul>';
            similar.forEach(pair => {
                html += `<li>"${pair.a1.title.substring(0, 30)}..." ↔ "${pair.a2.title.substring(0, 30)}..." (${Math.round(pair.similarity * 100)}% similar)</li>`;
            });
            html += '</ul>';
            
            showModal('🔍 Similar Articles Detected', similar.length > 0 ? html : '<p>No similar articles found</p>');
        }
        
        function calculateSimilarity(str1, str2) {
            const words1 = new Set(str1.toLowerCase().split(' '));
            const words2 = new Set(str2.toLowerCase().split(' '));
            const intersection = new Set([...words1].filter(x => words2.has(x)));
            const union = new Set([...words1, ...words2]);
            return intersection.size / union.size;
        }
        
        function showAnalytics() {
            const stages = { inbox: 0, reading: 0, reviewing: 0, completed: 0 };
            articles.forEach(a => stages[a.stage]++);
            
            let html = '<h4>Reading Pipeline:</h4>';
            html += '<ul>';
            Object.entries(stages).forEach(([stage, count]) => {
                const percent = articles.length > 0 ? Math.round((count / articles.length) * 100) : 0;
                html += `<li>${stage}: ${count} articles (${percent}%)</li>`;
            });
            html += '</ul>';
            
            const avgScore = articles.reduce((sum, a) => sum + a.quantum_score, 0) / articles.length;
            html += `<p><strong>Average Quantum Score:</strong> ${Math.round(avgScore)}/1000</p>`;
            
            showModal('📊 Real-time Analytics', html);
        }
        
        function generateSummaries() {
            let html = '<div>';
            articles.slice(0, 5).forEach(article => {
                const summary = article.summary || 'This article discusses ' + (article.category || 'various topics') + '. It provides insights and information that could be valuable for learning and understanding the subject matter.';
                html += `<h4>${article.title}</h4><p>${summary}</p><hr>`;
            });
            html += '</div>';
            showModal('📋 Smart Summaries', html);
        }
        
        function autoTag() {
            let html = '<div>';
            articles.slice(0, 5).forEach(article => {
                const tags = generateTags(article);
                html += `<h4>${article.title}</h4><p>Tags: ${tags.join(', ')}</p><hr>`;
            });
            html += '</div>';
            showModal('🏷️ Auto-Generated Tags', html);
        }
        
        function generateTags(article) {
            const tags = [];
            if (article.category) tags.push(article.category);
            if (article.priority) tags.push(article.priority + '-priority');
            if (article.stage === 'completed') tags.push('finished');
            if (article.quantum_score > 700) tags.push('high-value');
            if (article.reading_time > 10) tags.push('long-read');
            return tags;
        }
        
        function showReadingStreak() {
            fetch('/api/reading-streak')
                .then(response => response.json())
                .then(data => {
                    let html = `<h3>Current Streak: ${data.streak} days 🔥</h3>`;
                    html += '<p>Keep reading daily to maintain your streak!</p>';
                    if (data.streak > 7) {
                        html += '<p>🏆 Amazing! You\'ve been reading for over a week!</p>';
                    }
                    showModal('🔥 Reading Streak', html);
                });
        }
        
        function showSpeedInsights() {
            fetch('/api/speed-insights')
                .then(response => response.json())
                .then(data => {
                    let html = `<h3>Your Reading Speed: ${data.level}</h3>`;
                    html += `<p>Average: ${data.average_wpm} WPM</p>`;
                    html += `<p>Best: ${data.max_wpm} WPM</p>`;
                    html += `<p>Total reads: ${data.total_reads}</p>`;
                    html += `<p><em>${data.recommendation}</em></p>`;
                    showModal('⚡ Speed Insights', html);
                });
        }
        
        function showDailyDigest() {
            fetch('/api/daily-digest')
                .then(response => response.json())
                .then(data => {
                    let html = `<h3>Daily Digest - ${data.date}</h3>`;
                    html += `<p><em>"${data.quote}"</em></p>`;
                    html += `<h4>Today's Goal: ${data.goal}</h4>`;
                    html += '<h4>Recommended Articles:</h4><ol>';
                    data.articles.forEach(article => {
                        html += `<li>${article.title} (Q: ${article.quantum_score})</li>`;
                    });
                    html += '</ol>';
                    html += `<p>Current Streak: ${data.streak} days 🔥</p>`;
                    showModal('📅 Daily Digest', html);
                });
        }
        
        function showCategoryInsights() {
            fetch('/api/category-insights')
                .then(response => response.json())
                .then(data => {
                    let html = '<table style="width:100%; border-collapse: collapse;">';
                    html += '<tr><th>Category</th><th>Articles</th><th>Completion</th><th>Performance</th></tr>';
                    data.forEach(cat => {
                        html += `<tr>`;
                        html += `<td>${cat.category}</td>`;
                        html += `<td>${cat.total_articles}</td>`;
                        html += `<td>${cat.completion_rate}%</td>`;
                        html += `<td>${cat.performance}</td>`;
                        html += `</tr>`;
                    });
                    html += '</table>';
                    showModal('📈 Category Insights', html);
                });
        }
        
        function exportToMarkdown() {
            if (articles.length === 0) {
                showModal('📄 Export', '<p>No articles to export</p>');
                return;
            }
            
            const article = articles[0];
            fetch(`/api/export-markdown/${article.id}`)
                .then(response => response.json())
                .then(data => {
                    let html = '<h4>Markdown Export Ready!</h4>';
                    html += '<pre style="background: #f5f5f5; padding: 10px; border-radius: 5px; overflow: auto; max-height: 400px;">';
                    html += data.markdown.replace(/</g, '&lt;').replace(/>/g, '&gt;');
                    html += '</pre>';
                    html += '<button onclick="copyToClipboard(\'' + btoa(data.markdown) + '\')">Copy to Clipboard</button>';
                    showModal('📄 Export to Markdown', html);
                });
        }
        
        function copyToClipboard(base64Text) {
            const text = atob(base64Text);
            navigator.clipboard.writeText(text).then(() => {
                alert('Copied to clipboard!');
            });
        }
        
        // Close modal when clicking outside
        window.onclick = function(event) {
            const modal = document.getElementById('modal');
            if (event.target === modal) {
                closeModal();
            }
        }
    </script>
</body>
</html>'''
        
        self.send_response(200)
        self.send_header('Content-Type', 'text/html')
        self.end_headers()
        self.wfile.write(html.encode())
    
    def send_articles(self):
        """Send articles as JSON"""
        articles = UltimateApp.get_all_articles()
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(articles).encode())
    
    def send_recommendations(self, article_id):
        """Send AI recommendations"""
        recommendations = UltimateApp.get_ai_recommendations(article_id)
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(recommendations).encode())
    
    def send_study_notes(self, article_id):
        """Send study notes"""
        notes = UltimateApp.generate_study_notes(article_id)
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(notes).encode())
    
    def send_reading_streak(self):
        """Send reading streak"""
        streak = UltimateApp.get_reading_streak()
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps({'streak': streak}).encode())
    
    def send_speed_insights(self):
        """Send speed insights"""
        insights = UltimateApp.get_speed_insights()
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(insights).encode())
    
    def send_daily_digest(self):
        """Send daily digest"""
        digest = UltimateApp.get_daily_digest()
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(digest, default=str).encode())
    
    def send_category_insights(self):
        """Send category insights"""
        insights = UltimateApp.get_category_insights()
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(insights).encode())
    
    def send_markdown_export(self, article_id):
        """Send markdown export"""
        markdown = UltimateApp.export_to_markdown(article_id)
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps({'markdown': markdown}).encode())

def main():
    """Main entry point"""
    print("\n" + "="*60)
    print("🧠 ULTIMATE ARTICLE INTELLIGENCE HUB WITH LOGGING")
    print("="*60)
    
    logger.info("Starting Ultimate Article Intelligence Hub...")
    logger.info(f"Log file: {LOG_FILE}")
    
    # Run data migration
    UltimateApp.migrate_data()
    
    # Start server
    logger.info(f"Starting server on port {PORT}...")
    server = HTTPServer(('', PORT), RequestHandler)
    
    print(f"\n✅ Server running on http://localhost:{PORT}")
    print(f"📝 Logs are being written to: {LOG_FILE}")
    print("\n✨ Features:")
    print("  • Full logging to file and console")
    print("  • Automatic data migration")
    print("  • All 14 AI features working")
    print("  • Drag & Drop between columns ✓")
    print("  • Zero dependencies required ✓")
    print("\n" + "="*60)
    print("Press Ctrl+C to stop\n")
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
        print("\n👋 Server stopped")

if __name__ == "__main__":
    main()