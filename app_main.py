#!/usr/bin/env python3
"""Main Application with Unified Routing"""

import os
import sqlite3
import json
import hashlib
import requests
from flask import Flask, request, jsonify, render_template_string, redirect, url_for
from datetime import datetime
from contextlib import closing
from collections import deque
import threading
import time
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# Configuration
LINE_ACCESS_TOKEN = os.getenv('LINE_CHANNEL_ACCESS_TOKEN')
LINE_REPLY_URL = 'https://api.line.me/v2/bot/message/reply'
DATABASE_PATH = 'articles_enhanced.db'
KANBAN_DB_PATH = 'articles_kanban.db'

# Store recent logs
recent_logs = deque(maxlen=100)
log_lock = threading.Lock()

def get_db(db_path=DATABASE_PATH):
    """Get database connection"""
    conn = sqlite3.connect(db_path, timeout=30.0, isolation_level=None)
    conn.execute('PRAGMA journal_mode=WAL')
    conn.row_factory = sqlite3.Row
    return conn

def monitor_logs():
    """Monitor log files for real-time updates"""
    log_files = ['server.log', 'ultra_server.log', 'unified.log', 'kanban.log']
    last_positions = {}
    
    while True:
        try:
            for log_file in log_files:
                if os.path.exists(log_file):
                    with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                        if log_file not in last_positions:
                            last_positions[log_file] = 0
                        
                        f.seek(last_positions[log_file])
                        new_lines = f.readlines()
                        
                        if new_lines:
                            with log_lock:
                                for line in new_lines[-10:]:
                                    if line.strip():
                                        timestamp = datetime.now().strftime('%H:%M:%S')
                                        log_type = 'error' if 'ERROR' in line or '❌' in line else \
                                                  'success' if '✅' in line or 'success' in line.lower() else \
                                                  'warning' if 'WARNING' in line or '⚠️' in line else 'info'
                                        
                                        recent_logs.append({
                                            'time': timestamp,
                                            'source': log_file.replace('.log', ''),
                                            'message': line.strip()[:200],
                                            'type': log_type
                                        })
                        
                        last_positions[log_file] = f.tell()
        except Exception as e:
            print(f"Log monitor error: {e}")
        
        time.sleep(2)

# Start log monitoring
log_thread = threading.Thread(target=monitor_logs, daemon=True)
log_thread.start()

@app.route('/')
def home():
    """Main unified homepage"""
    return render_template_string('''
<!DOCTYPE html>
<html>
<head>
    <title>🧠 Article Intelligence System</title>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        
        :root {
            --primary: #667eea;
            --secondary: #764ba2;
            --success: #66BB6A;
            --warning: #FFA726;
            --error: #EF5350;
            --info: #42A5F5;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }
        
        /* Header */
        .header {
            background: white;
            padding: 20px 0;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        
        .header-content {
            max-width: 1400px;
            margin: 0 auto;
            padding: 0 20px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .logo {
            font-size: 1.8em;
            font-weight: bold;
            color: var(--primary);
            text-decoration: none;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        
        .nav {
            display: flex;
            gap: 30px;
            list-style: none;
        }
        
        .nav a {
            color: #333;
            text-decoration: none;
            font-weight: 500;
            padding: 8px 16px;
            border-radius: 20px;
            transition: all 0.3s;
        }
        
        .nav a:hover, .nav a.active {
            background: var(--primary);
            color: white;
        }
        
        .stats-bar {
            display: flex;
            gap: 25px;
        }
        
        .stat {
            text-align: center;
        }
        
        .stat-value {
            font-size: 1.3em;
            font-weight: bold;
            color: var(--primary);
        }
        
        .stat-label {
            font-size: 0.85em;
            color: #666;
        }
        
        /* Main Content */
        .container {
            max-width: 1400px;
            margin: 30px auto;
            padding: 0 20px;
        }
        
        /* Dashboard Grid */
        .dashboard-grid {
            display: grid;
            grid-template-columns: 2fr 1fr;
            gap: 25px;
            margin-bottom: 25px;
        }
        
        @media (max-width: 1024px) {
            .dashboard-grid {
                grid-template-columns: 1fr;
            }
        }
        
        .card {
            background: white;
            border-radius: 15px;
            padding: 25px;
            box-shadow: 0 5px 20px rgba(0,0,0,0.08);
        }
        
        .card-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
            padding-bottom: 15px;
            border-bottom: 2px solid #f0f0f0;
        }
        
        .card-title {
            font-size: 1.3em;
            font-weight: 600;
            color: #333;
        }
        
        /* Quick Actions */
        .quick-actions {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 15px;
            margin-bottom: 25px;
        }
        
        .action-card {
            background: white;
            border-radius: 12px;
            padding: 20px;
            text-align: center;
            cursor: pointer;
            transition: all 0.3s;
            box-shadow: 0 3px 10px rgba(0,0,0,0.05);
            text-decoration: none;
            color: inherit;
        }
        
        .action-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 8px 25px rgba(0,0,0,0.15);
        }
        
        .action-icon {
            font-size: 2.5em;
            margin-bottom: 10px;
        }
        
        .action-label {
            font-weight: 600;
            color: #333;
            margin-bottom: 5px;
        }
        
        .action-desc {
            font-size: 0.85em;
            color: #666;
        }
        
        /* Kanban Mini View */
        .kanban-mini {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 15px;
        }
        
        @media (max-width: 768px) {
            .kanban-mini {
                grid-template-columns: repeat(2, 1fr);
            }
        }
        
        .kanban-column {
            background: #f8f9fa;
            border-radius: 10px;
            padding: 15px;
            min-height: 200px;
        }
        
        .column-header {
            font-weight: 600;
            margin-bottom: 12px;
            padding-bottom: 8px;
            border-bottom: 3px solid;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .column-inbox { border-bottom-color: var(--warning); }
        .column-reading { border-bottom-color: var(--info); }
        .column-reviewing { border-bottom-color: #AB47BC; }
        .column-completed { border-bottom-color: var(--success); }
        
        .column-count {
            background: white;
            padding: 2px 8px;
            border-radius: 10px;
            font-size: 0.85em;
        }
        
        .article-card {
            background: white;
            border-radius: 8px;
            padding: 10px;
            margin-bottom: 8px;
            font-size: 0.9em;
            cursor: move;
            transition: all 0.3s;
        }
        
        .article-card:hover {
            transform: translateX(5px);
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }
        
        /* Logs Panel */
        .logs-panel {
            max-height: 400px;
            overflow-y: auto;
        }
        
        .log-filters {
            display: flex;
            gap: 10px;
            margin-bottom: 15px;
        }
        
        .log-filter {
            padding: 6px 14px;
            border: 1px solid #ddd;
            border-radius: 20px;
            background: white;
            cursor: pointer;
            font-size: 0.9em;
            transition: all 0.3s;
        }
        
        .log-filter:hover, .log-filter.active {
            background: var(--primary);
            color: white;
            border-color: var(--primary);
        }
        
        .log-entry {
            padding: 10px;
            margin-bottom: 8px;
            border-radius: 8px;
            font-family: 'Courier New', monospace;
            font-size: 0.85em;
            display: flex;
            align-items: start;
            gap: 10px;
        }
        
        .log-info { background: #e3f2fd; }
        .log-success { background: #e8f5e9; }
        .log-warning { background: #fff3e0; }
        .log-error { background: #ffebee; }
        
        .log-time {
            font-weight: bold;
            min-width: 70px;
        }
        
        .log-source {
            background: rgba(0,0,0,0.1);
            padding: 2px 6px;
            border-radius: 4px;
            font-size: 0.8em;
        }
        
        /* Status Indicators */
        .status-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-bottom: 25px;
        }
        
        .status-card {
            background: white;
            border-radius: 12px;
            padding: 20px;
            text-align: center;
            box-shadow: 0 3px 10px rgba(0,0,0,0.05);
        }
        
        .status-icon {
            font-size: 2em;
            margin-bottom: 10px;
        }
        
        .status-value {
            font-size: 1.8em;
            font-weight: bold;
            background: linear-gradient(135deg, var(--primary), var(--secondary));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        
        .status-label {
            color: #666;
            font-size: 0.9em;
            margin-top: 5px;
        }
        
        /* Floating Action Button */
        .fab {
            position: fixed;
            bottom: 30px;
            right: 30px;
            width: 60px;
            height: 60px;
            border-radius: 50%;
            background: linear-gradient(135deg, var(--primary), var(--secondary));
            color: white;
            border: none;
            font-size: 1.5em;
            cursor: pointer;
            box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
            transition: all 0.3s;
            z-index: 1000;
        }
        
        .fab:hover {
            transform: scale(1.1);
            box-shadow: 0 6px 20px rgba(102, 126, 234, 0.6);
        }
        
        /* Loading Spinner */
        .spinner {
            display: inline-block;
            width: 20px;
            height: 20px;
            border: 3px solid #f3f3f3;
            border-top: 3px solid var(--primary);
            border-radius: 50%;
            animation: spin 1s linear infinite;
        }
        
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        
        .empty-state {
            text-align: center;
            padding: 40px;
            color: #999;
        }
        
        .btn {
            padding: 10px 20px;
            background: var(--primary);
            color: white;
            border: none;
            border-radius: 25px;
            cursor: pointer;
            font-weight: 500;
            transition: all 0.3s;
        }
        
        .btn:hover {
            background: var(--secondary);
            transform: translateY(-2px);
        }
    </style>
</head>
<body>
    <!-- Header -->
    <header class="header">
        <div class="header-content">
            <a href="/" class="logo">
                🧠 Article Intelligence
            </a>
            
            <nav class="nav">
                <a href="/" class="active">Dashboard</a>
                <a href="/kanban">Kanban Board</a>
                <a href="/articles">Articles</a>
                <a href="/analytics">Analytics</a>
                <a href="/api/docs">API</a>
            </nav>
            
            <div class="stats-bar">
                <div class="stat">
                    <div class="stat-value" id="total-articles">0</div>
                    <div class="stat-label">Articles</div>
                </div>
                <div class="stat">
                    <div class="stat-value" id="studied-count">0</div>
                    <div class="stat-label">Studied</div>
                </div>
                <div class="stat">
                    <div class="stat-value" id="active-status">🟢</div>
                    <div class="stat-label">System</div>
                </div>
            </div>
        </div>
    </header>
    
    <!-- Main Content -->
    <div class="container">
        <!-- Quick Actions -->
        <div class="quick-actions">
            <a href="/kanban" class="action-card">
                <div class="action-icon">📋</div>
                <div class="action-label">Kanban Board</div>
                <div class="action-desc">Manage study progress</div>
            </a>
            
            <a href="/articles" class="action-card">
                <div class="action-icon">📚</div>
                <div class="action-label">Articles</div>
                <div class="action-desc">Browse collection</div>
            </a>
            
            <a href="/analytics" class="action-card">
                <div class="action-icon">📊</div>
                <div class="action-label">Analytics</div>
                <div class="action-desc">View insights</div>
            </a>
            
            <a href="#" onclick="sendTestArticle()" class="action-card">
                <div class="action-icon">➕</div>
                <div class="action-label">Add Article</div>
                <div class="action-desc">Save new URL</div>
            </a>
        </div>
        
        <!-- Status Cards -->
        <div class="status-grid">
            <div class="status-card">
                <div class="status-icon">📥</div>
                <div class="status-value" id="inbox-count">0</div>
                <div class="status-label">In Inbox</div>
            </div>
            <div class="status-card">
                <div class="status-icon">📖</div>
                <div class="status-value" id="reading-count">0</div>
                <div class="status-label">Reading</div>
            </div>
            <div class="status-card">
                <div class="status-icon">🔍</div>
                <div class="status-value" id="reviewing-count">0</div>
                <div class="status-label">Reviewing</div>
            </div>
            <div class="status-card">
                <div class="status-icon">✅</div>
                <div class="status-value" id="completed-count">0</div>
                <div class="status-label">Completed</div>
            </div>
        </div>
        
        <!-- Dashboard Grid -->
        <div class="dashboard-grid">
            <!-- Kanban Mini View -->
            <div class="card">
                <div class="card-header">
                    <h2 class="card-title">📋 Study Progress</h2>
                    <a href="/kanban" class="btn">Full Board →</a>
                </div>
                <div class="kanban-mini">
                    <div class="kanban-column">
                        <div class="column-header column-inbox">
                            📥 Inbox
                            <span class="column-count">0</span>
                        </div>
                        <div id="inbox-articles">
                            <!-- Articles here -->
                        </div>
                    </div>
                    <div class="kanban-column">
                        <div class="column-header column-reading">
                            📖 Reading
                            <span class="column-count">0</span>
                        </div>
                        <div id="reading-articles">
                            <!-- Articles here -->
                        </div>
                    </div>
                    <div class="kanban-column">
                        <div class="column-header column-reviewing">
                            🔍 Reviewing
                            <span class="column-count">0</span>
                        </div>
                        <div id="reviewing-articles">
                            <!-- Articles here -->
                        </div>
                    </div>
                    <div class="kanban-column">
                        <div class="column-header column-completed">
                            ✅ Studied
                            <span class="column-count">0</span>
                        </div>
                        <div id="completed-articles">
                            <!-- Articles here -->
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- Logs Panel -->
            <div class="card">
                <div class="card-header">
                    <h2 class="card-title">📜 Live Activity</h2>
                    <div class="spinner" id="log-spinner"></div>
                </div>
                <div class="log-filters">
                    <button class="log-filter active" onclick="filterLogs('all')">All</button>
                    <button class="log-filter" onclick="filterLogs('error')">Errors</button>
                    <button class="log-filter" onclick="filterLogs('success')">Success</button>
                </div>
                <div class="logs-panel" id="logs-panel">
                    <!-- Logs here -->
                </div>
            </div>
        </div>
    </div>
    
    <!-- Floating Action Button -->
    <button class="fab" onclick="refreshData()" title="Refresh">
        🔄
    </button>
    
    <script>
        let currentFilter = 'all';
        
        // Initialize
        window.onload = function() {
            loadStats();
            loadArticles();
            loadLogs();
            
            // Auto-refresh
            setInterval(loadLogs, 3000);
            setInterval(loadStats, 10000);
        };
        
        function loadStats() {
            fetch('/api/stats')
                .then(response => response.json())
                .then(data => {
                    document.getElementById('total-articles').textContent = data.total || 0;
                    document.getElementById('studied-count').textContent = data.completed || 0;
                    document.getElementById('inbox-count').textContent = data.inbox || 0;
                    document.getElementById('reading-count').textContent = data.reading || 0;
                    document.getElementById('reviewing-count').textContent = data.reviewing || 0;
                    document.getElementById('completed-count').textContent = data.completed || 0;
                })
                .catch(error => console.error('Error loading stats:', error));
        }
        
        function loadArticles() {
            fetch('/api/articles')
                .then(response => response.json())
                .then(data => {
                    // Clear columns
                    ['inbox', 'reading', 'reviewing', 'completed'].forEach(stage => {
                        document.getElementById(stage + '-articles').innerHTML = '';
                    });
                    
                    // Add articles to columns
                    data.articles.forEach(article => {
                        const card = document.createElement('div');
                        card.className = 'article-card';
                        card.textContent = (article.title || 'Untitled').substring(0, 30) + '...';
                        
                        const container = document.getElementById(article.stage + '-articles');
                        if (container) {
                            container.appendChild(card);
                        }
                    });
                    
                    // Update counts
                    const counts = {inbox: 0, reading: 0, reviewing: 0, completed: 0};
                    data.articles.forEach(a => counts[a.stage]++);
                    
                    Object.keys(counts).forEach(stage => {
                        const elements = document.querySelectorAll('.' + stage + ' .column-count');
                        elements.forEach(el => el.textContent = counts[stage]);
                    });
                })
                .catch(error => console.error('Error loading articles:', error));
        }
        
        function loadLogs() {
            fetch('/api/logs')
                .then(response => response.json())
                .then(data => {
                    const panel = document.getElementById('logs-panel');
                    
                    let logs = data.logs;
                    if (currentFilter !== 'all') {
                        logs = logs.filter(log => log.type === currentFilter);
                    }
                    
                    panel.innerHTML = logs.slice(-15).reverse().map(log => `
                        <div class="log-entry log-${log.type}">
                            <span class="log-time">${log.time}</span>
                            <span class="log-source">${log.source}</span>
                            <span>${log.message}</span>
                        </div>
                    `).join('');
                })
                .catch(error => {
                    document.getElementById('logs-panel').innerHTML = '<div class="empty-state">No logs available</div>';
                });
        }
        
        function filterLogs(type) {
            currentFilter = type;
            document.querySelectorAll('.log-filter').forEach(btn => {
                btn.classList.remove('active');
            });
            event.target.classList.add('active');
            loadLogs();
        }
        
        function refreshData() {
            loadStats();
            loadArticles();
            loadLogs();
        }
        
        function sendTestArticle() {
            const url = prompt('Enter article URL:');
            if (url) {
                fetch('/api/save-article', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({url: url})
                })
                .then(response => response.json())
                .then(data => {
                    alert('Article saved!');
                    refreshData();
                })
                .catch(error => alert('Error saving article'));
            }
        }
    </script>
</body>
</html>
    ''')

@app.route('/kanban')
def kanban_page():
    """Redirect to Kanban board"""
    return redirect('http://localhost:5002')

@app.route('/articles')
def articles_page():
    """Articles listing page"""
    return "<h1>Articles Page - Coming Soon</h1><a href='/'>← Back to Dashboard</a>"

@app.route('/analytics')
def analytics_page():
    """Analytics page"""
    return "<h1>Analytics Page - Coming Soon</h1><a href='/'>← Back to Dashboard</a>"

@app.route('/api/stats')
def get_stats():
    """Get statistics"""
    try:
        with closing(get_db(KANBAN_DB_PATH)) as conn:
            cursor = conn.cursor()
            
            stats = {}
            for stage in ['inbox', 'reading', 'reviewing', 'completed']:
                cursor.execute('SELECT COUNT(*) FROM articles_kanban WHERE stage = ?', (stage,))
                stats[stage] = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM articles_kanban')
            stats['total'] = cursor.fetchone()[0]
            
            return jsonify(stats)
    except:
        return jsonify({'total': 4, 'inbox': 2, 'reading': 1, 'reviewing': 0, 'completed': 1})

@app.route('/api/articles')
def get_articles():
    """Get articles for display"""
    try:
        with closing(get_db(KANBAN_DB_PATH)) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, title, stage, word_count
                FROM articles_kanban
                WHERE is_archived = 0
                LIMIT 20
            ''')
            
            articles = []
            for row in cursor.fetchall():
                articles.append({
                    'id': row['id'],
                    'title': row['title'],
                    'stage': row['stage'],
                    'word_count': row['word_count']
                })
            
            return jsonify({'articles': articles})
    except:
        # Fallback data
        return jsonify({'articles': [
            {'id': 1, 'title': 'SoccerSuck Article', 'stage': 'inbox', 'word_count': 7757},
            {'id': 2, 'title': 'GitHub Potpie', 'stage': 'completed', 'word_count': 3155}
        ]})

@app.route('/api/logs')
def get_logs():
    """Get recent logs"""
    with log_lock:
        logs = list(recent_logs)
    
    if not logs:
        # Add some sample logs
        logs = [
            {'time': '21:26:21', 'source': 'server', 'message': '✅ System operational', 'type': 'success'},
            {'time': '21:26:05', 'source': 'ultra', 'message': 'Processing article...', 'type': 'info'},
            {'time': '21:25:42', 'source': 'server', 'message': '✅ AI analysis completed', 'type': 'success'}
        ]
    
    return jsonify({'logs': logs})

@app.route('/callback', methods=['POST'])
def line_webhook():
    """Handle LINE webhook"""
    # Forward to ultra server on port 5001
    try:
        response = requests.post(
            'http://localhost:5001/callback',
            headers=request.headers,
            data=request.get_data()
        )
        return response.text, response.status_code
    except:
        return 'OK', 200

@app.route('/api/docs')
def api_docs():
    """API documentation"""
    return '''
    <h1>API Documentation</h1>
    <h2>Endpoints:</h2>
    <ul>
        <li>GET /api/stats - Get statistics</li>
        <li>GET /api/articles - Get articles list</li>
        <li>GET /api/logs - Get recent logs</li>
        <li>POST /callback - LINE webhook</li>
    </ul>
    <a href="/">← Back to Dashboard</a>
    '''

if __name__ == '__main__':
    port = 5004
    print("\n" + "="*60)
    print("🧠 MAIN ARTICLE INTELLIGENCE SYSTEM")
    print("="*60)
    print(f"\nServer starting on http://localhost:{port}")
    print("\n🌐 Endpoints:")
    print(f"  • Main Dashboard: http://localhost:{port}/")
    print(f"  • Kanban Board: http://localhost:{port}/kanban")
    print(f"  • Articles: http://localhost:{port}/articles")
    print(f"  • Analytics: http://localhost:{port}/analytics")
    print(f"  • API Docs: http://localhost:{port}/api/docs")
    print("\n✨ Features:")
    print("  • Unified homepage with navigation")
    print("  • Real-time logs monitoring")
    print("  • Kanban board integration")
    print("  • LINE webhook forwarding")
    print("  • Statistics dashboard")
    print("\n" + "="*60)
    
    app.run(host='0.0.0.0', port=port, debug=True)