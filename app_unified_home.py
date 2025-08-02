#!/usr/bin/env python3
"""Unified Homepage with Kanban Board and Live Logs"""

import os
import sqlite3
import json
from flask import Flask, request, jsonify, render_template_string
from datetime import datetime, timedelta
from contextlib import closing
import hashlib
from collections import deque
import threading
import time

app = Flask(__name__)

DATABASE_PATH = 'articles_enhanced.db'
KANBAN_DB_PATH = 'articles_kanban.db'

# Store recent logs in memory for real-time display
recent_logs = deque(maxlen=100)
log_lock = threading.Lock()

def get_db(db_path=DATABASE_PATH):
    """Get database connection"""
    conn = sqlite3.connect(db_path, timeout=30.0, isolation_level=None)
    conn.execute('PRAGMA journal_mode=WAL')
    conn.row_factory = sqlite3.Row
    return conn

def monitor_logs():
    """Monitor log files for updates"""
    log_files = ['server.log', 'ultra_server.log']
    last_positions = {}
    
    while True:
        try:
            for log_file in log_files:
                if os.path.exists(log_file):
                    with open(log_file, 'r') as f:
                        # Get last position
                        if log_file not in last_positions:
                            last_positions[log_file] = 0
                        
                        f.seek(last_positions[log_file])
                        new_lines = f.readlines()
                        
                        if new_lines:
                            with log_lock:
                                for line in new_lines[-10:]:  # Last 10 lines
                                    timestamp = datetime.now().strftime('%H:%M:%S')
                                    log_entry = {
                                        'time': timestamp,
                                        'source': log_file.replace('.log', ''),
                                        'message': line.strip(),
                                        'type': 'error' if 'ERROR' in line else 
                                               'success' if '✅' in line or 'success' in line.lower() else
                                               'warning' if 'WARNING' in line else 'info'
                                    }
                                    recent_logs.append(log_entry)
                        
                        last_positions[log_file] = f.tell()
        except Exception as e:
            print(f"Log monitor error: {e}")
        
        time.sleep(2)  # Check every 2 seconds

# Start log monitoring in background
log_thread = threading.Thread(target=monitor_logs, daemon=True)
log_thread.start()

@app.route('/')
def unified_home():
    """Render unified homepage with navigation, Kanban, and logs"""
    return render_template_string('''
<!DOCTYPE html>
<html>
<head>
    <title>🧠 Article Intelligence Hub</title>
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
            background: #f5f7fa;
            min-height: 100vh;
        }
        
        /* Navigation Bar */
        .navbar {
            background: linear-gradient(135deg, var(--primary) 0%, var(--secondary) 100%);
            padding: 15px 30px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            position: sticky;
            top: 0;
            z-index: 1000;
        }
        
        .nav-container {
            max-width: 1400px;
            margin: 0 auto;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .nav-brand {
            color: white;
            font-size: 1.5em;
            font-weight: bold;
            text-decoration: none;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        
        .nav-menu {
            display: flex;
            gap: 25px;
            list-style: none;
        }
        
        .nav-link {
            color: white;
            text-decoration: none;
            padding: 8px 16px;
            border-radius: 20px;
            transition: background 0.3s;
            cursor: pointer;
        }
        
        .nav-link:hover, .nav-link.active {
            background: rgba(255,255,255,0.2);
        }
        
        .nav-stats {
            display: flex;
            gap: 20px;
            color: white;
        }
        
        .nav-stat {
            text-align: center;
        }
        
        .nav-stat-value {
            font-size: 1.2em;
            font-weight: bold;
        }
        
        .nav-stat-label {
            font-size: 0.8em;
            opacity: 0.9;
        }
        
        /* Main Container */
        .main-container {
            max-width: 1400px;
            margin: 20px auto;
            padding: 0 20px;
        }
        
        /* Tab Content */
        .tab-content {
            display: none;
        }
        
        .tab-content.active {
            display: block;
        }
        
        /* Dashboard Grid */
        .dashboard-grid {
            margin-bottom: 20px;
        }
        
        /* Kanban Section */
        .kanban-section {
            background: white;
            border-radius: 15px;
            padding: 20px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.05);
        }
        
        .kanban-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
            padding-bottom: 15px;
            border-bottom: 2px solid #f0f0f0;
        }
        
        .kanban-columns {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 15px;
            min-height: 400px;
        }
        
        @media (max-width: 1200px) {
            .kanban-columns {
                grid-template-columns: repeat(2, 1fr);
            }
        }
        
        @media (max-width: 768px) {
            .kanban-columns {
                grid-template-columns: 1fr;
            }
        }
        
        .kanban-column {
            background: #f8f9fa;
            border-radius: 12px;
            padding: 15px;
            min-height: 300px;
            transition: all 0.3s;
            border: 2px dashed transparent;
        }
        
        .kanban-column.drag-over {
            background: #e8f4fd;
            border: 2px dashed var(--primary);
            transform: scale(1.02);
        }
        
        .column-header {
            font-weight: bold;
            margin-bottom: 15px;
            padding-bottom: 10px;
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
            border-radius: 10px;
            padding: 12px;
            margin-bottom: 10px;
            cursor: grab;
            transition: all 0.3s;
            border-left: 4px solid;
            user-select: none;
            -webkit-user-select: none;
        }
        
        .article-card:active {
            cursor: grabbing;
            opacity: 0.9;
        }
        
        .article-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        }
        
        .article-card.dragging {
            opacity: 0.5;
            cursor: grabbing;
        }
        
        .card-inbox { border-left-color: var(--warning); }
        .card-reading { border-left-color: var(--info); }
        .card-reviewing { border-left-color: #AB47BC; }
        .card-completed { border-left-color: var(--success); }
        
        .card-title {
            font-weight: 600;
            font-size: 0.9em;
            margin-bottom: 5px;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }
        
        .card-meta {
            font-size: 0.75em;
            color: #666;
        }
        
        /* Logs Section */
        .logs-section {
            background: white;
            border-radius: 15px;
            padding: 20px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.05);
            max-height: 500px;
            overflow-y: auto;
            margin-top: 20px;
        }
        
        .logs-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 15px;
            padding-bottom: 10px;
            border-bottom: 2px solid #f0f0f0;
        }
        
        .log-filters {
            display: flex;
            gap: 10px;
        }
        
        .log-filter {
            padding: 5px 12px;
            border: 1px solid #ddd;
            border-radius: 15px;
            background: white;
            cursor: pointer;
            font-size: 0.85em;
            transition: all 0.3s;
        }
        
        .log-filter:hover, .log-filter.active {
            background: var(--primary);
            color: white;
            border-color: var(--primary);
        }
        
        .log-entries {
            font-family: 'Courier New', monospace;
            font-size: 0.85em;
        }
        
        .log-entry {
            padding: 8px 12px;
            margin-bottom: 5px;
            border-radius: 8px;
            display: flex;
            align-items: center;
            gap: 10px;
            animation: slideIn 0.3s ease;
        }
        
        @keyframes slideIn {
            from { transform: translateX(-20px); opacity: 0; }
            to { transform: translateX(0); opacity: 1; }
        }
        
        .log-info { background: #e3f2fd; color: #1976d2; }
        .log-success { background: #e8f5e9; color: #2e7d32; }
        .log-warning { background: #fff3e0; color: #f57c00; }
        .log-error { background: #ffebee; color: #c62828; }
        
        .log-time {
            font-weight: bold;
            min-width: 80px;
        }
        
        .log-source {
            background: rgba(0,0,0,0.1);
            padding: 2px 6px;
            border-radius: 4px;
            font-size: 0.8em;
            min-width: 60px;
            text-align: center;
        }
        
        /* Quick Stats */
        .quick-stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-bottom: 20px;
        }
        
        .stat-card {
            background: white;
            border-radius: 12px;
            padding: 20px;
            text-align: center;
            box-shadow: 0 2px 10px rgba(0,0,0,0.05);
            transition: transform 0.3s;
        }
        
        .stat-card:hover {
            transform: translateY(-5px);
        }
        
        .stat-icon {
            font-size: 2em;
            margin-bottom: 10px;
        }
        
        .stat-value {
            font-size: 2em;
            font-weight: bold;
            background: linear-gradient(135deg, var(--primary), var(--secondary));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        
        .stat-label {
            color: #666;
            font-size: 0.9em;
            margin-top: 5px;
        }
        
        /* Recent Activity */
        .activity-section {
            background: white;
            border-radius: 15px;
            padding: 20px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.05);
            margin-top: 20px;
        }
        
        @media (min-width: 1400px) {
            .activity-section {
                padding: 25px;
            }
        }
        
        
        .activity-item {
            display: flex;
            align-items: center;
            gap: 15px;
            padding: 12px;
            border-bottom: 1px solid #f0f0f0;
        }
        
        .activity-icon {
            width: 40px;
            height: 40px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.2em;
        }
        
        .activity-icon.saved { background: #e8f5e9; color: var(--success); }
        .activity-icon.reading { background: #e3f2fd; color: var(--info); }
        .activity-icon.completed { background: #f3e5f5; color: #9c27b0; }
        
        .activity-details {
            flex: 1;
        }
        
        .activity-title {
            font-weight: 600;
            margin-bottom: 3px;
        }
        
        .activity-time {
            font-size: 0.85em;
            color: #999;
        }
        
        /* Action Buttons */
        .action-buttons {
            position: fixed;
            bottom: 30px;
            right: 30px;
            display: flex;
            flex-direction: column;
            gap: 15px;
        }
        
        .action-btn {
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
        }
        
        .action-btn:hover {
            transform: scale(1.1);
            box-shadow: 0 6px 20px rgba(102, 126, 234, 0.6);
        }
        
        /* Loading Animation */
        .loading {
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
        
        .empty-state-icon {
            font-size: 3em;
            margin-bottom: 15px;
            opacity: 0.5;
        }
    </style>
</head>
<body>
    <!-- Navigation Bar -->
    <nav class="navbar">
        <div class="nav-container">
            <a href="#" class="nav-brand">
                🧠 Article Intelligence Hub
            </a>
            
            <ul class="nav-menu">
                <li><a class="nav-link active" onclick="showTab('dashboard')">📊 Dashboard</a></li>
                <li><a class="nav-link" onclick="showTab('kanban')">📋 Kanban</a></li>
                <li><a class="nav-link" onclick="showTab('articles')">📚 Articles</a></li>
                <li><a class="nav-link" onclick="showTab('analytics')">📈 Analytics</a></li>
                <li><a class="nav-link" onclick="showTab('settings')">⚙️ Settings</a></li>
            </ul>
            
            <div class="nav-stats">
                <div class="nav-stat">
                    <div class="nav-stat-value" id="nav-total">0</div>
                    <div class="nav-stat-label">Articles</div>
                </div>
                <div class="nav-stat">
                    <div class="nav-stat-value" id="nav-studied">0</div>
                    <div class="nav-stat-label">Studied</div>
                </div>
            </div>
        </div>
    </nav>
    
    <!-- Main Container -->
    <div class="main-container">
        
        <!-- Dashboard Tab -->
        <div id="dashboard" class="tab-content active">
            <!-- Quick Stats -->
            <div class="quick-stats">
                <div class="stat-card">
                    <div class="stat-icon">📚</div>
                    <div class="stat-value" id="total-articles">0</div>
                    <div class="stat-label">Total Articles</div>
                </div>
                <div class="stat-card">
                    <div class="stat-icon">📖</div>
                    <div class="stat-value" id="reading-count">0</div>
                    <div class="stat-label">Currently Reading</div>
                </div>
                <div class="stat-card">
                    <div class="stat-icon">✅</div>
                    <div class="stat-value" id="completed-count">0</div>
                    <div class="stat-label">Completed</div>
                </div>
                <div class="stat-card">
                    <div class="stat-icon">⏱️</div>
                    <div class="stat-value" id="study-hours">0</div>
                    <div class="stat-label">Study Hours</div>
                </div>
            </div>
            
            <!-- Kanban Section -->
            <div class="kanban-section">
                <div class="kanban-header">
                    <h2>📋 Study Progress</h2>
                    <button onclick="showTab('kanban')" style="padding: 8px 16px; background: var(--primary); color: white; border: none; border-radius: 20px; cursor: pointer;">
                        View Full Board →
                    </button>
                </div>
                <div class="kanban-columns">
                    <div class="kanban-column" ondrop="drop(event, 'inbox')" ondragover="allowDrop(event)">
                        <div class="column-header column-inbox">
                            📥 Inbox
                            <span class="column-count" id="inbox-count">0</span>
                        </div>
                        <div id="inbox-cards">
                            <!-- Cards loaded here -->
                        </div>
                    </div>
                    <div class="kanban-column" ondrop="drop(event, 'reading')" ondragover="allowDrop(event)">
                        <div class="column-header column-reading">
                            📖 Reading
                            <span class="column-count" id="reading-count-col">0</span>
                        </div>
                        <div id="reading-cards">
                            <!-- Cards loaded here -->
                        </div>
                    </div>
                    <div class="kanban-column" ondrop="drop(event, 'reviewing')" ondragover="allowDrop(event)">
                        <div class="column-header column-reviewing">
                            🔍 Reviewing
                            <span class="column-count" id="reviewing-count">0</span>
                        </div>
                        <div id="reviewing-cards">
                            <!-- Cards loaded here -->
                        </div>
                    </div>
                    <div class="kanban-column" ondrop="drop(event, 'completed')" ondragover="allowDrop(event)">
                        <div class="column-header column-completed">
                            ✅ Studied
                            <span class="column-count" id="completed-count-col">0</span>
                        </div>
                        <div id="completed-cards">
                            <!-- Cards loaded here -->
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- Recent Activity -->
            <div class="activity-section">
                <h3>🕐 Recent Activity</h3>
                <div id="recent-activity">
                    <!-- Activity items loaded here -->
                </div>
            </div>
        </div>
        
        <!-- Kanban Tab (Full View) -->
        <div id="kanban" class="tab-content">
            <h2>📋 Full Kanban Board</h2>
            <p>Full Kanban implementation here...</p>
        </div>
        
        <!-- Articles Tab -->
        <div id="articles" class="tab-content">
            <h2>📚 Article Library</h2>
            <p>Article list and search here...</p>
        </div>
        
        <!-- Analytics Tab -->
        <div id="analytics" class="tab-content">
            <h2>📈 Analytics & Insights</h2>
            <p>Charts and analytics here...</p>
        </div>
        
        <!-- Settings Tab -->
        <div id="settings" class="tab-content">
            <h2>⚙️ Settings</h2>
            <p>Configuration options here...</p>
        </div>
    </div>
    
    <!-- Action Buttons -->
    <div class="action-buttons">
        <button class="action-btn" onclick="refreshData()" title="Refresh">
            🔄
        </button>
        <button class="action-btn" onclick="addArticle()" title="Add Article">
            ➕
        </button>
    </div>
    
    <script>
        let articles = {};
        let currentFilter = 'all';
        
        // Initialize
        window.onload = function() {
            loadArticles();
            loadLogs();
            loadActivity();
            
            // Auto-refresh logs every 3 seconds
            setInterval(loadLogs, 3000);
            
            // Auto-refresh articles every 10 seconds
            setInterval(loadArticles, 10000);
        };
        
        // Tab Navigation
        function showTab(tabName) {
            // Hide all tabs
            document.querySelectorAll('.tab-content').forEach(tab => {
                tab.classList.remove('active');
            });
            
            // Remove active from nav links
            document.querySelectorAll('.nav-link').forEach(link => {
                link.classList.remove('active');
            });
            
            // Show selected tab
            document.getElementById(tabName).classList.add('active');
            
            // Mark nav link as active
            event.target.classList.add('active');
        }
        
        // Load Articles for Kanban
        function loadArticles() {
            fetch('/api/articles')
                .then(response => response.json())
                .then(data => {
                    articles = {};
                    
                    // Clear columns
                    ['inbox', 'reading', 'reviewing', 'completed'].forEach(stage => {
                        const container = document.getElementById(stage + '-cards');
                        if (container) container.innerHTML = '';
                    });
                    
                    // Stats
                    let stats = {
                        total: 0,
                        inbox: 0,
                        reading: 0,
                        reviewing: 0,
                        completed: 0,
                        hours: 0
                    };
                    
                    // Add articles to columns
                    data.articles.forEach(article => {
                        articles[article.id] = article;
                        addArticleCard(article);
                        
                        // Update stats
                        stats.total++;
                        stats[article.stage]++;
                        stats.hours += (article.total_study_time || 0) / 60;
                    });
                    
                    // Update UI stats
                    updateStats(stats);
                })
                .catch(error => console.error('Error loading articles:', error));
        }
        
        function addArticleCard(article) {
            const card = document.createElement('div');
            card.className = 'article-card card-' + article.stage;
            card.draggable = true;
            card.id = 'article-' + article.id;
            
            // Add drag event handler
            card.addEventListener('dragstart', drag);
            
            const title = article.title || 'Untitled';
            const truncatedTitle = title.length > 40 ? title.substring(0, 40) + '...' : title;
            const wordCount = article.word_count || 0;
            const readingTime = article.reading_time || Math.max(1, Math.floor(wordCount / 200));
            
            // AI insights
            const category = article.category || 'Other';
            const difficulty = article.difficulty || 'intermediate';
            const sentiment = article.sentiment || 'neutral';
            const qualityScore = article.quality_score || 0;
            
            // Difficulty color
            const diffColor = {
                'elementary': '#4CAF50',
                'intermediate': '#FF9800',
                'advanced': '#F44336',
                'expert': '#9C27B0'
            }[difficulty] || '#757575';
            
            // Sentiment emoji
            const sentimentEmoji = sentiment.includes('positive') ? '😊' : 
                                  sentiment.includes('negative') ? '😟' : '😐';
            
            card.innerHTML = `
                <div class="card-title" title="${title}">
                    <span class="card-link" data-url="${article.url}" style="color: inherit; cursor: pointer;">
                        ${truncatedTitle}
                    </span>
                </div>
                <div class="card-meta">
                    📊 ${wordCount} words · ⏱️ ${readingTime} min
                </div>
                <div class="card-ai" style="margin-top: 8px; padding-top: 8px; border-top: 1px solid #eee; font-size: 0.7em;">
                    <span style="background: #e3f2fd; color: #1976d2; padding: 2px 6px; border-radius: 3px; margin-right: 5px;">
                        ${category}
                    </span>
                    <span style="background: ${diffColor}22; color: ${diffColor}; padding: 2px 6px; border-radius: 3px; margin-right: 5px;">
                        ${difficulty}
                    </span>
                    <span title="Sentiment: ${sentiment}">
                        ${sentimentEmoji}
                    </span>
                    ${qualityScore > 0 ? `<span style="float: right; color: #666;">⭐ ${qualityScore}/100</span>` : ''}
                </div>
            `;
            
            // Add drag event handlers
            card.addEventListener('dragstart', drag);
            card.addEventListener('dragend', function(e) {
                e.target.classList.remove('dragging');
            });
            
            // Add click handler for the link (but only on double-click to avoid conflict with drag)
            const linkElement = card.querySelector('.card-link');
            if (linkElement) {
                linkElement.addEventListener('dblclick', function(e) {
                    e.stopPropagation();
                    window.open(this.dataset.url, '_blank');
                });
                
                // Add tooltip to show double-click instruction
                linkElement.title = linkElement.title + ' (double-click to open)';
            }
            
            const container = document.getElementById(article.stage + '-cards');
            if (container) {
                container.appendChild(card);
            }
        }
        
        function updateStats(stats) {
            // Update all stat displays
            document.getElementById('total-articles').textContent = stats.total;
            document.getElementById('reading-count').textContent = stats.reading;
            document.getElementById('completed-count').textContent = stats.completed;
            document.getElementById('study-hours').textContent = Math.round(stats.hours);
            
            document.getElementById('nav-total').textContent = stats.total;
            document.getElementById('nav-studied').textContent = stats.completed;
            
            document.getElementById('inbox-count').textContent = stats.inbox;
            document.getElementById('reading-count-col').textContent = stats.reading;
            document.getElementById('reviewing-count').textContent = stats.reviewing;
            document.getElementById('completed-count-col').textContent = stats.completed;
        }
        
        // Load Logs
        function loadLogs() {
            fetch('/api/logs')
                .then(response => response.json())
                .then(data => {
                    const container = document.getElementById('log-entries');
                    
                    // Filter logs
                    let logs = data.logs;
                    if (currentFilter !== 'all') {
                        logs = logs.filter(log => log.type === currentFilter);
                    }
                    
                    // Display logs
                    container.innerHTML = logs.slice(-20).reverse().map(log => `
                        <div class="log-entry log-${log.type}">
                            <span class="log-time">${log.time}</span>
                            <span class="log-source">${log.source}</span>
                            <span>${log.message.substring(0, 100)}${log.message.length > 100 ? '...' : ''}</span>
                        </div>
                    `).join('');
                    
                    // Auto-scroll to bottom if near bottom
                    if (container.scrollHeight - container.scrollTop < container.clientHeight + 100) {
                        container.scrollTop = container.scrollHeight;
                    }
                })
                .catch(error => console.error('Error loading logs:', error));
        }
        
        // Load Recent Activity
        function loadActivity() {
            fetch('/api/activity')
                .then(response => response.json())
                .then(data => {
                    const container = document.getElementById('recent-activity');
                    
                    container.innerHTML = data.activities.map(activity => `
                        <div class="activity-item">
                            <div class="activity-icon ${activity.type}">
                                ${activity.icon}
                            </div>
                            <div class="activity-details">
                                <div class="activity-title">${activity.title}</div>
                                <div class="activity-time">${activity.time}</div>
                            </div>
                        </div>
                    `).join('');
                })
                .catch(error => {
                    // Fallback with dummy data
                    document.getElementById('recent-activity').innerHTML = `
                        <div class="empty-state">
                            <div class="empty-state-icon">📭</div>
                            <p>No recent activity</p>
                        </div>
                    `;
                });
        }
        
        // Filter logs
        function filterLogs(type) {
            currentFilter = type;
            
            // Update filter buttons
            document.querySelectorAll('.log-filter').forEach(btn => {
                btn.classList.remove('active');
            });
            event.target.classList.add('active');
            
            // Reload logs with filter
            loadLogs();
        }
        
        // Drag and Drop
        function allowDrop(ev) {
            ev.preventDefault();
            ev.dataTransfer.dropEffect = "move";
            
            // Add visual feedback to column
            const column = ev.currentTarget;
            if (column.classList.contains('kanban-column')) {
                column.classList.add('drag-over');
            }
        }
        
        // Add event listeners for drag leave to remove visual feedback
        document.addEventListener('DOMContentLoaded', function() {
            const columns = document.querySelectorAll('.kanban-column');
            columns.forEach(column => {
                column.addEventListener('dragleave', function(e) {
                    if (e.currentTarget === column) {
                        column.classList.remove('drag-over');
                    }
                });
                column.addEventListener('drop', function(e) {
                    column.classList.remove('drag-over');
                });
            });
        });
        
        function drag(ev) {
            ev.dataTransfer.setData("text", ev.target.id);
            ev.dataTransfer.effectAllowed = "move";
            ev.target.classList.add('dragging');
        }
        
        function drop(ev, newStage) {
            ev.preventDefault();
            ev.stopPropagation();
            
            // Remove visual feedback
            document.querySelectorAll('.kanban-column').forEach(col => {
                col.classList.remove('drag-over');
            });
            
            const data = ev.dataTransfer.getData("text");
            const element = document.getElementById(data);
            
            if (!element) return;
            
            element.classList.remove('dragging');
            const articleId = parseInt(data.replace('article-', ''));
            
            // Get the correct container for the new stage
            const targetContainer = document.getElementById(newStage + '-cards');
            
            // Update stage
            fetch('/api/update-stage', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    article_id: articleId,
                    stage: newStage
                })
            })
            .then(response => response.json())
            .then(data => {
                // Move the card to the new container
                targetContainer.appendChild(element);
                element.className = 'article-card card-' + newStage;
                articles[articleId].stage = newStage;
                
                // Update counts
                updateCounts();
            })
            .catch(error => console.error('Error updating stage:', error));
        }
        
        function updateCounts() {
            // Update column counts without reloading everything
            const counts = {inbox: 0, reading: 0, reviewing: 0, completed: 0};
            Object.values(articles).forEach(article => {
                if (counts.hasOwnProperty(article.stage)) {
                    counts[article.stage]++;
                }
            });
            
            document.getElementById('inbox-count').textContent = counts.inbox;
            document.getElementById('reading-count-col').textContent = counts.reading;
            document.getElementById('reviewing-count').textContent = counts.reviewing;
            document.getElementById('completed-count-col').textContent = counts.completed;
            
            // Update stats
            document.getElementById('reading-count').textContent = counts.reading;
            document.getElementById('completed-count').textContent = counts.completed;
        }
        
        // Actions
        function refreshData() {
            loadArticles();
            loadLogs();
            loadActivity();
        }
        
        function addArticle() {
            // Implement add article modal
            alert('Add article feature coming soon!');
        }
    </script>
</body>
</html>
    ''')

@app.route('/api/articles')
def get_articles():
    """Get articles for Kanban with AI insights"""
    try:
        # Try Kanban DB first
        with closing(get_db(KANBAN_DB_PATH)) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, url, title, stage, word_count, reading_time, total_study_time,
                       category, difficulty, topics
                FROM articles_kanban
                WHERE is_archived = 0
                ORDER BY id DESC
            ''')
            
            articles = []
            for row in cursor.fetchall():
                articles.append({
                    'id': row['id'],
                    'url': row['url'],
                    'title': row['title'],
                    'stage': row['stage'],
                    'word_count': row['word_count'] or 0,
                    'reading_time': row['reading_time'] or 0,
                    'total_study_time': row['total_study_time'] or 0,
                    'category': row['category'] or 'Other',
                    'sentiment': 'neutral',  # Default since column doesn't exist
                    'difficulty': row['difficulty'] or 'intermediate',
                    'quality_score': 0,  # Default since column doesn't exist
                    'topics': row['topics'] or ''
                })
            
            return jsonify({'articles': articles})
    except Exception as e:
        print(f"Kanban DB error: {e}")
        # Fallback to main DB
        with closing(get_db()) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, url, title, word_count, reading_time
                FROM articles
                LIMIT 20
            ''')
            
            articles = []
            for row in cursor.fetchall():
                articles.append({
                    'id': row['id'],
                    'title': row['title'],
                    'stage': 'inbox',  # Default stage
                    'word_count': row['word_count'],
                    'total_study_time': 0
                })
            
            return jsonify({'articles': articles})

@app.route('/api/logs')
def get_logs():
    """Get recent logs"""
    with log_lock:
        logs = list(recent_logs)
    
    return jsonify({'logs': logs})

@app.route('/api/activity')
def get_activity():
    """Get recent activity"""
    activities = [
        {
            'type': 'saved',
            'icon': '📥',
            'title': 'New article saved from LINE',
            'time': '5 minutes ago'
        },
        {
            'type': 'reading',
            'icon': '📖',
            'title': 'Started reading "SoccerSuck"',
            'time': '1 hour ago'
        },
        {
            'type': 'completed',
            'icon': '✅',
            'title': 'Completed "GitHub Potpie"',
            'time': '2 hours ago'
        }
    ]
    
    return jsonify({'activities': activities})

@app.route('/api/update-stage', methods=['POST'])
def update_stage():
    """Update article stage"""
    data = request.json
    article_id = data.get('article_id')
    new_stage = data.get('stage')
    
    try:
        with closing(get_db(KANBAN_DB_PATH)) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE articles_kanban 
                SET stage = ?, stage_updated = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (new_stage, article_id))
            conn.commit()
    except:
        pass  # Handle error
    
    return jsonify({'status': 'success'})

@app.route('/callback', methods=['POST'])
def line_webhook():
    """Forward LINE webhook to LINE bot server"""
    import requests
    try:
        # Forward to LINE bot on port 5005
        response = requests.post(
            'http://localhost:5005/callback',
            headers=request.headers,
            data=request.get_data()
        )
        return response.text, response.status_code
    except:
        return 'OK', 200

if __name__ == '__main__':
    port = 5003
    print("\n" + "="*60)
    print("🧠 UNIFIED ARTICLE INTELLIGENCE HUB")
    print("="*60)
    print(f"\nServer starting on http://localhost:{port}")
    print("\n✨ Features:")
    print("  • Unified homepage with navigation")
    print("  • Integrated Kanban board")
    print("  • Live activity logs")
    print("  • Real-time statistics")
    print("  • Drag & drop article management")
    print("  • Recent activity tracking")
    print("\n" + "="*60)
    
    app.run(host='0.0.0.0', port=port, debug=True)