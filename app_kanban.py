#!/usr/bin/env python3
"""Kanban Board for Article Study Progress Tracking"""

import os
import sqlite3
import json
from flask import Flask, request, jsonify, render_template_string
from datetime import datetime
from contextlib import closing
import hashlib

app = Flask(__name__)

DATABASE_PATH = 'articles_kanban.db'

def get_db():
    """Get database connection"""
    conn = sqlite3.connect(DATABASE_PATH, timeout=30.0, isolation_level=None)
    conn.execute('PRAGMA journal_mode=WAL')
    conn.row_factory = sqlite3.Row
    return conn

def init_kanban_db():
    """Initialize Kanban database with study stages"""
    with closing(get_db()) as conn:
        cursor = conn.cursor()
        
        # Enhanced articles table with Kanban stages
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS articles_kanban (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                article_id INTEGER,
                url TEXT NOT NULL,
                url_hash TEXT UNIQUE,
                title TEXT,
                summary TEXT,
                category TEXT,
                topics TEXT,
                word_count INTEGER,
                reading_time INTEGER,
                
                -- Kanban Stage Management
                stage TEXT DEFAULT 'inbox',  -- inbox/reading/reviewing/completed
                stage_updated TIMESTAMP,
                
                -- Study Progress Tracking
                study_status TEXT DEFAULT 'new',  -- new/in_progress/studied/mastered
                priority TEXT DEFAULT 'medium',  -- high/medium/low
                difficulty TEXT,  -- easy/medium/hard/expert
                
                -- Study Metrics
                times_read INTEGER DEFAULT 0,
                study_sessions INTEGER DEFAULT 0,
                total_study_time INTEGER DEFAULT 0,  -- in minutes
                comprehension_score INTEGER,  -- 0-100
                
                -- Notes and Learning
                study_notes TEXT,
                key_learnings TEXT,
                questions TEXT,
                action_items TEXT,
                related_topics TEXT,
                
                -- Timestamps
                added_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                first_read_date TIMESTAMP,
                last_read_date TIMESTAMP,
                completed_date TIMESTAMP,
                
                -- User Interaction
                is_favorite BOOLEAN DEFAULT 0,
                is_archived BOOLEAN DEFAULT 0,
                tags TEXT,
                rating INTEGER,  -- 1-5 stars
                
                -- Review Schedule
                next_review_date TIMESTAMP,
                review_count INTEGER DEFAULT 0,
                
                -- Source Info
                source_type TEXT,
                author TEXT,
                published_date TEXT
            )
        ''')
        
        # Study sessions tracking
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS study_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                article_id INTEGER,
                start_time TIMESTAMP,
                end_time TIMESTAMP,
                duration_minutes INTEGER,
                notes TEXT,
                progress_percentage INTEGER,
                FOREIGN KEY (article_id) REFERENCES articles_kanban(id)
            )
        ''')
        
        # Create indexes
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_stage ON articles_kanban(stage)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_priority ON articles_kanban(priority)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_study_status ON articles_kanban(study_status)')
        
        conn.commit()
    print("✅ Kanban database initialized")

# Import existing articles
def import_existing_articles():
    """Import articles from existing database"""
    try:
        # Connect to existing database
        existing_conn = sqlite3.connect('articles_enhanced.db', timeout=30.0)
        existing_conn.row_factory = sqlite3.Row
        
        with closing(existing_conn) as old_conn:
            cursor = old_conn.cursor()
            cursor.execute('''
                SELECT url, title, summary, category, topics, 
                       word_count, reading_time, saved_at
                FROM articles
            ''')
            articles = cursor.fetchall()
            
            # Import to Kanban database
            with closing(get_db()) as new_conn:
                new_cursor = new_conn.cursor()
                
                imported = 0
                for article in articles:
                    url_hash = hashlib.md5(article['url'].encode()).hexdigest()
                    
                    # Check if already exists
                    new_cursor.execute('SELECT id FROM articles_kanban WHERE url_hash = ?', (url_hash,))
                    if not new_cursor.fetchone():
                        new_cursor.execute('''
                            INSERT INTO articles_kanban (
                                url, url_hash, title, summary, category, 
                                topics, word_count, reading_time, added_date, stage
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ''', (
                            article['url'], url_hash, article['title'],
                            article['summary'], article['category'],
                            article['topics'], article['word_count'],
                            article['reading_time'], article['saved_at'],
                            'inbox'  # Start in inbox stage
                        ))
                        imported += 1
                
                new_conn.commit()
                print(f"✅ Imported {imported} articles to Kanban board")
                
    except Exception as e:
        print(f"Import error: {e}")

@app.route('/')
def kanban_board():
    """Render Kanban board interface"""
    return render_template_string('''
<!DOCTYPE html>
<html>
<head>
    <title>📚 Article Study Kanban Board</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        .header {
            background: white;
            border-radius: 20px;
            padding: 20px 30px;
            margin-bottom: 30px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.1);
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        h1 {
            color: #764ba2;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        .stats {
            display: flex;
            gap: 20px;
        }
        .stat {
            text-align: center;
        }
        .stat-value {
            font-size: 1.5em;
            font-weight: bold;
            color: #667eea;
        }
        .stat-label {
            font-size: 0.9em;
            color: #666;
        }
        .kanban-container {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 20px;
            min-height: 600px;
        }
        .kanban-column {
            background: white;
            border-radius: 15px;
            padding: 20px;
            box-shadow: 0 5px 20px rgba(0,0,0,0.1);
        }
        .column-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
            padding-bottom: 15px;
            border-bottom: 3px solid;
        }
        .column-inbox { border-bottom-color: #FFA726; }
        .column-reading { border-bottom-color: #42A5F5; }
        .column-reviewing { border-bottom-color: #AB47BC; }
        .column-completed { border-bottom-color: #66BB6A; }
        
        .column-title {
            font-size: 1.2em;
            font-weight: bold;
            display: flex;
            align-items: center;
            gap: 8px;
        }
        .column-count {
            background: #f0f0f0;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.9em;
        }
        .article-cards {
            display: flex;
            flex-direction: column;
            gap: 15px;
            min-height: 400px;
        }
        .article-card {
            background: #f8f9fa;
            border-radius: 12px;
            padding: 15px;
            cursor: move;
            transition: all 0.3s ease;
            border-left: 4px solid;
        }
        .article-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
        }
        .card-inbox { border-left-color: #FFA726; }
        .card-reading { border-left-color: #42A5F5; }
        .card-reviewing { border-left-color: #AB47BC; }
        .card-completed { border-left-color: #66BB6A; }
        
        .card-title {
            font-weight: 600;
            margin-bottom: 8px;
            color: #333;
            display: -webkit-box;
            -webkit-line-clamp: 2;
            -webkit-box-orient: vertical;
            overflow: hidden;
        }
        .card-meta {
            font-size: 0.85em;
            color: #666;
            margin-bottom: 10px;
        }
        .card-tags {
            display: flex;
            flex-wrap: wrap;
            gap: 5px;
            margin-bottom: 10px;
        }
        .tag {
            background: #e3f2fd;
            color: #1976d2;
            padding: 3px 8px;
            border-radius: 12px;
            font-size: 0.75em;
        }
        .priority-high { background: #ffebee; color: #c62828; }
        .priority-medium { background: #fff3e0; color: #ef6c00; }
        .priority-low { background: #e8f5e9; color: #2e7d32; }
        
        .card-actions {
            display: flex;
            gap: 10px;
            margin-top: 10px;
        }
        .card-action {
            padding: 5px 10px;
            border: none;
            border-radius: 8px;
            font-size: 0.85em;
            cursor: pointer;
            transition: background 0.3s;
        }
        .action-notes {
            background: #e3f2fd;
            color: #1976d2;
        }
        .action-notes:hover { background: #bbdefb; }
        .action-priority {
            background: #fce4ec;
            color: #c2185b;
        }
        .action-priority:hover { background: #f8bbd0; }
        
        .progress-bar {
            height: 4px;
            background: #e0e0e0;
            border-radius: 2px;
            margin: 10px 0;
            overflow: hidden;
        }
        .progress-fill {
            height: 100%;
            background: linear-gradient(90deg, #667eea, #764ba2);
            transition: width 0.3s;
        }
        
        .empty-state {
            text-align: center;
            padding: 40px 20px;
            color: #999;
            font-style: italic;
        }
        
        .dragging {
            opacity: 0.5;
        }
        .drag-over {
            background: #f0f0f0;
        }
        
        .modal {
            display: none;
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: rgba(0,0,0,0.5);
            z-index: 1000;
            align-items: center;
            justify-content: center;
        }
        .modal-content {
            background: white;
            border-radius: 20px;
            padding: 30px;
            max-width: 600px;
            width: 90%;
            max-height: 80vh;
            overflow-y: auto;
        }
        .modal-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
        }
        .close-modal {
            background: none;
            border: none;
            font-size: 1.5em;
            cursor: pointer;
            color: #999;
        }
        .notes-input {
            width: 100%;
            min-height: 150px;
            padding: 15px;
            border: 2px solid #e0e0e0;
            border-radius: 10px;
            font-size: 1em;
            resize: vertical;
        }
        .save-btn {
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: white;
            border: none;
            padding: 12px 30px;
            border-radius: 25px;
            font-size: 1em;
            cursor: pointer;
            margin-top: 20px;
        }
        .save-btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(102, 126, 234, 0.3);
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>📚 Article Study Kanban Board</h1>
        <div class="stats">
            <div class="stat">
                <div class="stat-value" id="total-articles">0</div>
                <div class="stat-label">Total Articles</div>
            </div>
            <div class="stat">
                <div class="stat-value" id="completed-count">0</div>
                <div class="stat-label">Completed</div>
            </div>
            <div class="stat">
                <div class="stat-value" id="study-hours">0</div>
                <div class="stat-label">Study Hours</div>
            </div>
        </div>
    </div>

    <div class="kanban-container">
        <!-- Inbox Column -->
        <div class="kanban-column">
            <div class="column-header column-inbox">
                <div class="column-title">
                    📥 Inbox
                    <span class="column-count" id="inbox-count">0</span>
                </div>
            </div>
            <div class="article-cards" id="inbox-cards" ondrop="drop(event, 'inbox')" ondragover="allowDrop(event)">
                <!-- Cards will be loaded here -->
            </div>
        </div>

        <!-- Reading Column -->
        <div class="kanban-column">
            <div class="column-header column-reading">
                <div class="column-title">
                    📖 Reading
                    <span class="column-count" id="reading-count">0</span>
                </div>
            </div>
            <div class="article-cards" id="reading-cards" ondrop="drop(event, 'reading')" ondragover="allowDrop(event)">
                <!-- Cards will be loaded here -->
            </div>
        </div>

        <!-- Reviewing Column -->
        <div class="kanban-column">
            <div class="column-header column-reviewing">
                <div class="column-title">
                    🔍 Reviewing
                    <span class="column-count" id="reviewing-count">0</span>
                </div>
            </div>
            <div class="article-cards" id="reviewing-cards" ondrop="drop(event, 'reviewing')" ondragover="allowDrop(event)">
                <!-- Cards will be loaded here -->
            </div>
        </div>

        <!-- Completed Column -->
        <div class="kanban-column">
            <div class="column-header column-completed">
                <div class="column-title">
                    ✅ Studied
                    <span class="column-count" id="completed-count-col">0</span>
                </div>
            </div>
            <div class="article-cards" id="completed-cards" ondrop="drop(event, 'completed')" ondragover="allowDrop(event)">
                <!-- Cards will be loaded here -->
            </div>
        </div>
    </div>

    <!-- Notes Modal -->
    <div id="notes-modal" class="modal">
        <div class="modal-content">
            <div class="modal-header">
                <h2>📝 Study Notes</h2>
                <button class="close-modal" onclick="closeModal()">&times;</button>
            </div>
            <h3 id="modal-title"></h3>
            <textarea class="notes-input" id="study-notes" placeholder="Add your study notes, key learnings, questions..."></textarea>
            <button class="save-btn" onclick="saveNotes()">Save Notes</button>
        </div>
    </div>

    <script>
        let articles = {};
        let currentArticleId = null;

        // Load articles on page load
        window.onload = function() {
            loadArticles();
        };

        function loadArticles() {
            fetch('/api/articles')
                .then(response => response.json())
                .then(data => {
                    articles = {};
                    // Clear all columns
                    ['inbox', 'reading', 'reviewing', 'completed'].forEach(stage => {
                        document.getElementById(stage + '-cards').innerHTML = '';
                    });
                    
                    // Add articles to appropriate columns
                    data.articles.forEach(article => {
                        articles[article.id] = article;
                        addArticleCard(article);
                    });
                    
                    updateStats();
                })
                .catch(error => console.error('Error loading articles:', error));
        }

        function addArticleCard(article) {
            const card = document.createElement('div');
            card.className = 'article-card card-' + article.stage;
            card.draggable = true;
            card.id = 'article-' + article.id;
            card.ondragstart = (e) => drag(e);
            
            const priority = article.priority || 'medium';
            const topics = article.topics ? JSON.parse(article.topics) : [];
            
            card.innerHTML = `
                <div class="card-title">${article.title || 'Untitled Article'}</div>
                <div class="card-meta">
                    📊 ${article.word_count || 0} words · ⏱️ ${article.reading_time || '?'} min
                </div>
                <div class="card-tags">
                    <span class="tag priority-${priority}">${priority} priority</span>
                    ${topics.slice(0, 2).map(t => `<span class="tag">${t}</span>`).join('')}
                </div>
                ${article.stage === 'reading' ? `
                    <div class="progress-bar">
                        <div class="progress-fill" style="width: ${article.progress || 0}%"></div>
                    </div>
                ` : ''}
                <div class="card-actions">
                    <button class="card-action action-notes" onclick="openNotes(${article.id})">
                        📝 Notes
                    </button>
                    <button class="card-action action-priority" onclick="cyclePriority(${article.id})">
                        ⚡ Priority
                    </button>
                </div>
            `;
            
            document.getElementById(article.stage + '-cards').appendChild(card);
        }

        function updateStats() {
            const stats = {
                inbox: 0,
                reading: 0,
                reviewing: 0,
                completed: 0,
                total: 0,
                hours: 0
            };
            
            Object.values(articles).forEach(article => {
                stats[article.stage]++;
                stats.total++;
                stats.hours += (article.total_study_time || 0) / 60;
            });
            
            document.getElementById('inbox-count').textContent = stats.inbox;
            document.getElementById('reading-count').textContent = stats.reading;
            document.getElementById('reviewing-count').textContent = stats.reviewing;
            document.getElementById('completed-count-col').textContent = stats.completed;
            document.getElementById('total-articles').textContent = stats.total;
            document.getElementById('completed-count').textContent = stats.completed;
            document.getElementById('study-hours').textContent = Math.round(stats.hours);
        }

        function allowDrop(ev) {
            ev.preventDefault();
            ev.currentTarget.classList.add('drag-over');
        }

        function drag(ev) {
            ev.dataTransfer.setData("text", ev.target.id);
            ev.target.classList.add('dragging');
        }

        function drop(ev, newStage) {
            ev.preventDefault();
            ev.currentTarget.classList.remove('drag-over');
            
            const data = ev.dataTransfer.getData("text");
            const element = document.getElementById(data);
            element.classList.remove('dragging');
            
            const articleId = parseInt(data.replace('article-', ''));
            
            // Update article stage
            updateArticleStage(articleId, newStage);
            
            // Move card to new column
            ev.currentTarget.appendChild(element);
            
            // Update card styling
            element.className = 'article-card card-' + newStage;
        }

        function updateArticleStage(articleId, newStage) {
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
                articles[articleId].stage = newStage;
                updateStats();
                
                // Show completion message
                if (newStage === 'completed') {
                    showNotification('🎉 Article marked as studied!');
                }
            })
            .catch(error => console.error('Error updating stage:', error));
        }

        function openNotes(articleId) {
            currentArticleId = articleId;
            const article = articles[articleId];
            
            document.getElementById('modal-title').textContent = article.title || 'Untitled';
            document.getElementById('study-notes').value = article.study_notes || '';
            document.getElementById('notes-modal').style.display = 'flex';
        }

        function closeModal() {
            document.getElementById('notes-modal').style.display = 'none';
        }

        function saveNotes() {
            const notes = document.getElementById('study-notes').value;
            
            fetch('/api/update-notes', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    article_id: currentArticleId,
                    notes: notes
                })
            })
            .then(response => response.json())
            .then(data => {
                articles[currentArticleId].study_notes = notes;
                closeModal();
                showNotification('📝 Notes saved!');
            })
            .catch(error => console.error('Error saving notes:', error));
        }

        function cyclePriority(articleId) {
            const article = articles[articleId];
            const priorities = ['low', 'medium', 'high'];
            const currentIndex = priorities.indexOf(article.priority || 'medium');
            const newPriority = priorities[(currentIndex + 1) % 3];
            
            fetch('/api/update-priority', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    article_id: articleId,
                    priority: newPriority
                })
            })
            .then(response => response.json())
            .then(data => {
                articles[articleId].priority = newPriority;
                loadArticles(); // Reload to update display
            })
            .catch(error => console.error('Error updating priority:', error));
        }

        function showNotification(message) {
            // Simple notification (you can enhance this)
            const notif = document.createElement('div');
            notif.style.cssText = `
                position: fixed;
                top: 20px;
                right: 20px;
                background: white;
                padding: 15px 25px;
                border-radius: 10px;
                box-shadow: 0 5px 15px rgba(0,0,0,0.2);
                z-index: 2000;
                animation: slideIn 0.3s ease;
            `;
            notif.textContent = message;
            document.body.appendChild(notif);
            
            setTimeout(() => {
                notif.remove();
            }, 3000);
        }
    </script>
</body>
</html>
    ''')

@app.route('/api/articles')
def get_articles():
    """Get all articles with their Kanban status"""
    with closing(get_db()) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, url, title, summary, category, topics,
                   word_count, reading_time, stage, priority,
                   study_notes, total_study_time, times_read
            FROM articles_kanban
            WHERE is_archived = 0
            ORDER BY 
                CASE priority 
                    WHEN 'high' THEN 1 
                    WHEN 'medium' THEN 2 
                    WHEN 'low' THEN 3 
                END,
                added_date DESC
        ''')
        
        articles = []
        for row in cursor.fetchall():
            articles.append({
                'id': row['id'],
                'url': row['url'],
                'title': row['title'],
                'summary': row['summary'],
                'category': row['category'],
                'topics': row['topics'],
                'word_count': row['word_count'],
                'reading_time': row['reading_time'],
                'stage': row['stage'],
                'priority': row['priority'],
                'study_notes': row['study_notes'],
                'total_study_time': row['total_study_time'],
                'times_read': row['times_read']
            })
        
        return jsonify({'articles': articles})

@app.route('/api/update-stage', methods=['POST'])
def update_stage():
    """Update article stage in Kanban"""
    data = request.json
    article_id = data.get('article_id')
    new_stage = data.get('stage')
    
    with closing(get_db()) as conn:
        cursor = conn.cursor()
        
        # Update stage and timestamps
        cursor.execute('''
            UPDATE articles_kanban 
            SET stage = ?, 
                stage_updated = CURRENT_TIMESTAMP,
                first_read_date = CASE 
                    WHEN first_read_date IS NULL AND ? = 'reading' 
                    THEN CURRENT_TIMESTAMP 
                    ELSE first_read_date 
                END,
                completed_date = CASE 
                    WHEN ? = 'completed' 
                    THEN CURRENT_TIMESTAMP 
                    ELSE completed_date 
                END
            WHERE id = ?
        ''', (new_stage, new_stage, new_stage, article_id))
        
        conn.commit()
        
    return jsonify({'status': 'success', 'stage': new_stage})

@app.route('/api/update-notes', methods=['POST'])
def update_notes():
    """Update study notes for an article"""
    data = request.json
    article_id = data.get('article_id')
    notes = data.get('notes')
    
    with closing(get_db()) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE articles_kanban 
            SET study_notes = ?,
                last_read_date = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (notes, article_id))
        conn.commit()
        
    return jsonify({'status': 'success'})

@app.route('/api/update-priority', methods=['POST'])
def update_priority():
    """Update article priority"""
    data = request.json
    article_id = data.get('article_id')
    priority = data.get('priority')
    
    with closing(get_db()) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE articles_kanban 
            SET priority = ?
            WHERE id = ?
        ''', (priority, article_id))
        conn.commit()
        
    return jsonify({'status': 'success', 'priority': priority})

if __name__ == '__main__':
    init_kanban_db()
    import_existing_articles()
    
    port = 5002
    print("\n" + "="*60)
    print("📚 ARTICLE STUDY KANBAN BOARD")
    print("="*60)
    print(f"\nServer starting on http://localhost:{port}")
    print("\n✨ Features:")
    print("  • 4 Study Stages: Inbox → Reading → Reviewing → Studied")
    print("  • Drag & Drop articles between stages")
    print("  • Priority levels (High/Medium/Low)")
    print("  • Study notes for each article")
    print("  • Progress tracking")
    print("  • Study time metrics")
    print("\n" + "="*60)
    
    app.run(host='0.0.0.0', port=port, debug=True)