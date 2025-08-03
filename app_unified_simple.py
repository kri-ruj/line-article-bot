#!/usr/bin/env python3
"""Simplified Unified App with Built-in AI Features (No Dependencies)"""

import os
import sqlite3
import json
from datetime import datetime, timedelta
from contextlib import closing
import hashlib
from collections import deque
import threading
import time
import random
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import mimetypes

# Database configuration
DATABASE_PATH = 'articles_enhanced.db'
KANBAN_DB_PATH = 'articles_kanban.db'

# Store recent logs in memory
recent_logs = deque(maxlen=100)
log_lock = threading.Lock()

def get_db(db_path=DATABASE_PATH):
    """Get database connection"""
    conn = sqlite3.connect(db_path, timeout=30.0, isolation_level=None)
    conn.execute('PRAGMA journal_mode=WAL')
    conn.row_factory = sqlite3.Row
    return conn

def calculate_quantum_score(article):
    """Calculate quantum score for article"""
    score = 500  # Base score
    
    # Title bonus
    if article.get('title'):
        score += min(100, len(article['title']) * 2)
    
    # Category bonus
    category_scores = {
        'Technology': 150,
        'Science': 140,
        'Business': 120,
        'Other': 50
    }
    score += category_scores.get(article.get('category', 'Other'), 50)
    
    # Summary bonus
    if article.get('summary'):
        score += min(150, len(article.get('summary', '')) // 10)
    
    # Time of day bonus
    hour = datetime.now().hour
    if 6 <= hour <= 10:
        score += 100
    elif 19 <= hour <= 22:
        score += 80
    
    # Random quantum interference
    score += random.randint(-50, 50)
    
    return min(1000, max(0, score))

def get_articles():
    """Get articles from database"""
    try:
        with closing(get_db(KANBAN_DB_PATH)) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, url, title, summary, category, stage, word_count, reading_time
                FROM articles_kanban
                WHERE is_archived = 0
                ORDER BY id DESC
            ''')
            
            articles = []
            for row in cursor.fetchall():
                article = dict(row)
                article['quantum_score'] = calculate_quantum_score(article)
                articles.append(article)
            
            return articles
    except Exception as e:
        print(f"Database error: {e}")
        return []

def get_priority_ranking():
    """Get articles ranked by quantum score"""
    articles = get_articles()
    articles.sort(key=lambda x: x['quantum_score'], reverse=True)
    return articles[:20]

def generate_study_notes(article_id):
    """Generate simple study notes"""
    articles = get_articles()
    article = next((a for a in articles if a['id'] == article_id), None)
    
    if not article:
        return None
    
    notes = f"""# Study Notes: {article['title']}

## Summary
{article.get('summary', 'No summary available')}

## Key Points
- Article URL: {article['url']}
- Category: {article.get('category', 'General')}
- Quantum Score: {calculate_quantum_score(article)}/1000
- Reading Time: {article.get('reading_time', 'Unknown')} minutes

## Learning Objectives
1. Understand the main concept
2. Apply the knowledge
3. Remember key points

## Review Questions
- What is the main topic?
- Why is this important?
- How can you apply this?

---
Generated on {datetime.now().strftime('%Y-%m-%d %H:%M')}
"""
    return notes

def get_recommendations(article_id):
    """Get article recommendations"""
    articles = get_articles()
    current = next((a for a in articles if a['id'] == article_id), None)
    
    if not current:
        return []
    
    # Simple recommendation: same category or high quantum score
    recommendations = []
    for article in articles:
        if article['id'] != article_id:
            similarity = 0
            if article.get('category') == current.get('category'):
                similarity += 0.5
            if article['quantum_score'] > 700:
                similarity += 0.3
            
            if similarity > 0:
                recommendations.append({
                    'id': article['id'],
                    'title': article['title'],
                    'category': article.get('category', 'Other'),
                    'similarity_score': similarity,
                    'reason': 'Similar category' if article.get('category') == current.get('category') else 'High quality'
                })
    
    recommendations.sort(key=lambda x: x['similarity_score'], reverse=True)
    return recommendations[:5]

def get_analytics():
    """Get reading analytics"""
    articles = get_articles()
    
    # Calculate stats
    total = len(articles)
    stages = {'inbox': 0, 'reading': 0, 'reviewing': 0, 'completed': 0}
    categories = {}
    total_quantum = 0
    
    for article in articles:
        stage = article.get('stage', 'inbox')
        stages[stage] = stages.get(stage, 0) + 1
        
        category = article.get('category', 'Other')
        categories[category] = categories.get(category, 0) + 1
        
        total_quantum += article['quantum_score']
    
    completion_rate = (stages.get('completed', 0) / total * 100) if total > 0 else 0
    avg_quantum = total_quantum / total if total > 0 else 0
    
    return {
        'total_articles': total,
        'completion_rate': completion_rate,
        'stage_distribution': stages,
        'category_distribution': categories,
        'avg_quantum_score': avg_quantum,
        'weekly_velocity': random.randint(3, 10),  # Simulated
        'avg_reading_time': random.randint(5, 15)  # Simulated
    }

class SimpleHTTPHandler(BaseHTTPRequestHandler):
    """Simple HTTP request handler"""
    
    def do_GET(self):
        """Handle GET requests"""
        parsed_path = urlparse(self.path)
        path = parsed_path.path
        
        if path == '/':
            self.serve_home()
        elif path == '/api/articles':
            self.serve_json(get_articles())
        elif path == '/api/ai/priority-ranking':
            self.serve_json({'ranked_articles': get_priority_ranking()})
        elif path == '/api/ai/analytics':
            self.serve_json(get_analytics())
        elif path.startswith('/api/ai/recommendations/'):
            article_id = int(path.split('/')[-1])
            self.serve_json({'recommendations': get_recommendations(article_id)})
        elif path.startswith('/api/ai/study-notes/'):
            article_id = int(path.split('/')[-1])
            notes = generate_study_notes(article_id)
            self.serve_json({'notes': notes})
        else:
            self.send_error(404)
    
    def do_POST(self):
        """Handle POST requests"""
        if self.path == '/api/update-stage':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data)
            
            # Update stage in database
            try:
                with closing(get_db(KANBAN_DB_PATH)) as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        UPDATE articles_kanban 
                        SET stage = ?
                        WHERE id = ?
                    ''', (data['stage'], data['article_id']))
                    conn.commit()
                self.serve_json({'status': 'success'})
            except:
                self.serve_json({'status': 'error'})
        else:
            self.send_error(404)
    
    def serve_json(self, data):
        """Serve JSON response"""
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())
    
    def serve_home(self):
        """Serve the home page"""
        html = '''<!DOCTYPE html>
<html>
<head>
    <title>🧠 Article Intelligence Hub</title>
    <meta charset="UTF-8">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, sans-serif;
            background: #f5f7fa;
            padding: 20px;
        }
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 15px;
            margin-bottom: 20px;
            text-align: center;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
        }
        .card {
            background: white;
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 20px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.05);
        }
        .kanban-columns {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 15px;
        }
        .kanban-column {
            background: #f8f9fa;
            border-radius: 10px;
            padding: 15px;
            min-height: 300px;
        }
        .article-card {
            background: white;
            border-radius: 8px;
            padding: 10px;
            margin-bottom: 10px;
            cursor: grab;
            border-left: 4px solid #667eea;
        }
        .article-card:hover {
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }
        .btn {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 20px;
            cursor: pointer;
            margin: 5px;
        }
        .btn:hover {
            transform: translateY(-2px);
        }
        .stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-bottom: 20px;
        }
        .stat-card {
            background: white;
            padding: 15px;
            border-radius: 10px;
            text-align: center;
        }
        .stat-value {
            font-size: 2em;
            font-weight: bold;
            color: #667eea;
        }
        .modal {
            display: none;
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0,0,0,0.5);
            align-items: center;
            justify-content: center;
        }
        .modal.show {
            display: flex;
        }
        .modal-content {
            background: white;
            border-radius: 20px;
            width: 90%;
            max-width: 800px;
            max-height: 80vh;
            overflow-y: auto;
        }
        .modal-header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 20px 20px 0 0;
        }
        .modal-body {
            padding: 20px;
        }
        .priority-item {
            background: #f8f9fa;
            padding: 15px;
            margin-bottom: 10px;
            border-radius: 10px;
            border-left: 4px solid #667eea;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🧠 Article Intelligence Hub</h1>
            <p>Quantum-Powered Reading System</p>
        </div>
        
        <div class="stats">
            <div class="stat-card">
                <div>📚 Total Articles</div>
                <div class="stat-value" id="total-articles">0</div>
            </div>
            <div class="stat-card">
                <div>✅ Completed</div>
                <div class="stat-value" id="completed-count">0</div>
            </div>
            <div class="stat-card">
                <div>🎯 Avg Quantum Score</div>
                <div class="stat-value" id="avg-quantum">0</div>
            </div>
            <div class="stat-card">
                <div>📈 Completion Rate</div>
                <div class="stat-value" id="completion-rate">0%</div>
            </div>
        </div>
        
        <div class="card">
            <h2>🤖 AI Features</h2>
            <button class="btn" onclick="showPriority()">📊 Priority Ranking</button>
            <button class="btn" onclick="generateNotes()">📝 Study Notes</button>
            <button class="btn" onclick="showRecommendations()">💡 Recommendations</button>
            <button class="btn" onclick="showAnalytics()">📈 Analytics</button>
        </div>
        
        <div class="card">
            <h2>📋 Kanban Board</h2>
            <div class="kanban-columns">
                <div class="kanban-column">
                    <h3>📥 Inbox (<span id="inbox-count">0</span>)</h3>
                    <div id="inbox-cards"></div>
                </div>
                <div class="kanban-column">
                    <h3>📖 Reading (<span id="reading-count">0</span>)</h3>
                    <div id="reading-cards"></div>
                </div>
                <div class="kanban-column">
                    <h3>🔍 Reviewing (<span id="reviewing-count">0</span>)</h3>
                    <div id="reviewing-cards"></div>
                </div>
                <div class="kanban-column">
                    <h3>✅ Completed (<span id="completed-count-col">0</span>)</h3>
                    <div id="completed-cards"></div>
                </div>
            </div>
        </div>
    </div>
    
    <!-- Modal -->
    <div id="modal" class="modal">
        <div class="modal-content">
            <div class="modal-header">
                <h2 id="modal-title">Title</h2>
                <button onclick="closeModal()" style="float: right; background: none; border: none; color: white; font-size: 1.5em; cursor: pointer;">&times;</button>
            </div>
            <div class="modal-body" id="modal-body">
                Content
            </div>
        </div>
    </div>
    
    <script>
        let articles = [];
        
        function loadArticles() {
            fetch('/api/articles')
                .then(r => r.json())
                .then(data => {
                    articles = data;
                    updateKanban();
                    updateStats();
                });
        }
        
        function updateKanban() {
            const stages = ['inbox', 'reading', 'reviewing', 'completed'];
            const counts = {inbox: 0, reading: 0, reviewing: 0, completed: 0};
            
            stages.forEach(stage => {
                const container = document.getElementById(stage + '-cards');
                container.innerHTML = '';
            });
            
            articles.forEach(article => {
                const stage = article.stage || 'inbox';
                counts[stage] = (counts[stage] || 0) + 1;
                
                const card = document.createElement('div');
                card.className = 'article-card';
                card.innerHTML = `
                    <strong>${article.title ? article.title.substring(0, 50) : 'Untitled'}</strong><br>
                    <small>Quantum: ${article.quantum_score || 0} | ${article.category || 'Other'}</small>
                `;
                
                const container = document.getElementById(stage + '-cards');
                if (container) container.appendChild(card);
            });
            
            stages.forEach(stage => {
                const el = document.getElementById(stage + '-count');
                if (el) el.textContent = counts[stage];
            });
            document.getElementById('completed-count-col').textContent = counts.completed;
        }
        
        function updateStats() {
            fetch('/api/ai/analytics')
                .then(r => r.json())
                .then(data => {
                    document.getElementById('total-articles').textContent = data.total_articles || 0;
                    document.getElementById('completed-count').textContent = data.stage_distribution?.completed || 0;
                    document.getElementById('avg-quantum').textContent = Math.round(data.avg_quantum_score || 0);
                    document.getElementById('completion-rate').textContent = Math.round(data.completion_rate || 0) + '%';
                });
        }
        
        function showPriority() {
            fetch('/api/ai/priority-ranking')
                .then(r => r.json())
                .then(data => {
                    let html = '';
                    data.ranked_articles.forEach((article, i) => {
                        html += `
                            <div class="priority-item">
                                <strong>#${i+1} - Score: ${article.quantum_score}/1000</strong><br>
                                ${article.title}<br>
                                <small>${article.category || 'Other'} | ${article.stage || 'inbox'}</small>
                            </div>
                        `;
                    });
                    showModal('📊 Priority Ranking', html);
                });
        }
        
        function generateNotes() {
            if (articles.length > 0) {
                const article = articles[0];
                fetch(`/api/ai/study-notes/${article.id}`)
                    .then(r => r.json())
                    .then(data => {
                        const html = `<pre style="white-space: pre-wrap;">${data.notes || 'No notes generated'}</pre>`;
                        showModal('📝 Study Notes', html);
                    });
            } else {
                alert('No articles available');
            }
        }
        
        function showRecommendations() {
            if (articles.length > 0) {
                const article = articles[0];
                fetch(`/api/ai/recommendations/${article.id}`)
                    .then(r => r.json())
                    .then(data => {
                        let html = `<p>Based on: <strong>${article.title}</strong></p>`;
                        data.recommendations.forEach(rec => {
                            html += `
                                <div class="priority-item">
                                    <strong>${rec.title}</strong><br>
                                    <small>${rec.category} | ${rec.reason}</small>
                                </div>
                            `;
                        });
                        showModal('💡 Recommendations', html);
                    });
            } else {
                alert('No articles available');
            }
        }
        
        function showAnalytics() {
            fetch('/api/ai/analytics')
                .then(r => r.json())
                .then(data => {
                    let html = '<h3>📊 Analytics Report</h3>';
                    html += `<p>Total Articles: ${data.total_articles}</p>`;
                    html += `<p>Completion Rate: ${Math.round(data.completion_rate)}%</p>`;
                    html += `<p>Average Quantum Score: ${Math.round(data.avg_quantum_score)}</p>`;
                    html += '<h4>Stage Distribution:</h4>';
                    for (let stage in data.stage_distribution) {
                        html += `<p>${stage}: ${data.stage_distribution[stage]}</p>`;
                    }
                    showModal('📈 Analytics', html);
                });
        }
        
        function showModal(title, content) {
            document.getElementById('modal-title').textContent = title;
            document.getElementById('modal-body').innerHTML = content;
            document.getElementById('modal').classList.add('show');
        }
        
        function closeModal() {
            document.getElementById('modal').classList.remove('show');
        }
        
        // Load on start
        loadArticles();
        setInterval(loadArticles, 10000);
    </script>
</body>
</html>'''
        
        self.send_response(200)
        self.send_header('Content-Type', 'text/html')
        self.end_headers()
        self.wfile.write(html.encode())
    
    def log_message(self, format, *args):
        """Suppress default logging"""
        pass

def run_server(port=5004):
    """Run the simple HTTP server"""
    server_address = ('', port)
    httpd = HTTPServer(server_address, SimpleHTTPHandler)
    
    print("\n" + "="*60)
    print("🧠 ARTICLE INTELLIGENCE HUB - SIMPLIFIED VERSION")
    print("="*60)
    print(f"\n✅ Server starting on http://localhost:{port}")
    print("\n✨ Features:")
    print("  • Quantum Scoring (0-1000)")
    print("  • Priority Ranking")
    print("  • Study Notes Generation")
    print("  • Smart Recommendations")
    print("  • Analytics Dashboard")
    print("  • Kanban Board")
    print("\n⚡ NO DEPENDENCIES REQUIRED!")
    print("="*60)
    print("\nPress Ctrl+C to stop the server\n")
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n\nServer stopped.")

if __name__ == '__main__':
    run_server()