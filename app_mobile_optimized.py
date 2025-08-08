#!/usr/bin/env python3
"""
🧠 MOBILE-OPTIMIZED ARTICLE INTELLIGENCE HUB
With fixed PWA, LIFF integration, and mobile-friendly Kanban
"""

import json
import sqlite3
import logging
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs, unquote
from datetime import datetime, timedelta
import hashlib
import random
import re
from collections import Counter
import os

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app_mobile.log'),
        logging.StreamHandler()
    ]
)

PORT = 5001
DB_PATH = 'articles_kanban.db'
LIFF_ID = '2007552096-GxP76rNd'
LINE_CHANNEL_ACCESS_TOKEN = os.getenv('LINE_CHANNEL_ACCESS_TOKEN', '9JTrTJ3+0lXerYu6HRjq4LNF+3UuDG5IwxfU0S8f5QYMJNai+WU3dgs2U5RfO74YDGGh5B1eAi4DoDxl0lq5CAA/kDkAwfaz2AL/qTEiO3Toiz1pS0nCtRNZKDoY0sI3JIWQucLySxrq7gEf7Rvx/QdB04t89/1O/w1cDnyilFU=')

class RequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed_path = urlparse(self.path)
        
        if parsed_path.path == '/':
            self.serve_homepage()
        elif parsed_path.path == '/api/articles':
            self.serve_articles()
        elif parsed_path.path == '/manifest.json':
            self.serve_manifest()
        elif parsed_path.path == '/service-worker.js':
            self.serve_service_worker()
        elif parsed_path.path == '/offline.html':
            self.serve_offline_page()
        elif parsed_path.path.startswith('/icon-'):
            self.serve_icon()
        else:
            self.send_error(404)
    
    def do_POST(self):
        parsed_path = urlparse(self.path)
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        
        if parsed_path.path == '/callback':
            self.handle_line_webhook(post_data)
        elif parsed_path.path == '/api/articles':
            self.handle_add_article(post_data)
        elif parsed_path.path == '/api/articles/update':
            self.handle_update_article(post_data)
        else:
            self.send_error(404)
    
    def serve_homepage(self):
        html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>📚 Article Hub</title>
    
    <!-- PWA Meta Tags -->
    <meta name="theme-color" content="#667eea">
    <meta name="apple-mobile-web-app-capable" content="yes">
    <meta name="apple-mobile-web-app-status-bar-style" content="default">
    <meta name="apple-mobile-web-app-title" content="Article Hub">
    <meta name="mobile-web-app-capable" content="yes">
    <meta name="format-detection" content="telephone=no">
    
    <!-- PWA Links -->
    <link rel="manifest" href="/manifest.json">
    <link rel="apple-touch-icon" href="/icon-192x192.png">
    <link rel="apple-touch-startup-image" href="/icon-512x512.png">
    
    <!-- LINE LIFF SDK -->
    <script charset="utf-8" src="https://static.line-scdn.net/liff/edge/2/sdk.js"></script>
    
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
            -webkit-tap-highlight-color: transparent;
            -webkit-touch-callout: none;
            -webkit-user-select: none;
            user-select: none;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            color: #333;
            overflow-x: hidden;
            position: relative;
            padding-bottom: env(safe-area-inset-bottom);
        }}
        
        /* Container */
        .container {{
            width: 100%;
            max-width: 100vw;
            padding: 10px;
            padding-bottom: 80px; /* Space for bottom nav */
        }}
        
        /* Header */
        .header {{
            background: rgba(255, 255, 255, 0.98);
            backdrop-filter: blur(20px);
            -webkit-backdrop-filter: blur(20px);
            border-radius: 12px;
            padding: 12px 15px;
            margin-bottom: 15px;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        
        .logo {{
            font-size: 18px;
            font-weight: bold;
            background: linear-gradient(135deg, #667eea, #764ba2);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }}
        
        .install-btn {{
            padding: 6px 12px;
            background: #10b981;
            color: white;
            border: none;
            border-radius: 20px;
            font-size: 12px;
            font-weight: 600;
            display: none;
        }}
        
        .install-btn.show {{
            display: block;
        }}
        
        /* Stats Cards */
        .stats-container {{
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 10px;
            margin-bottom: 15px;
        }}
        
        .stat-card {{
            background: rgba(255, 255, 255, 0.95);
            border-radius: 12px;
            padding: 15px;
            text-align: center;
            box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
        }}
        
        .stat-number {{
            font-size: 24px;
            font-weight: bold;
            color: #667eea;
        }}
        
        .stat-label {{
            color: #666;
            font-size: 12px;
            margin-top: 4px;
        }}
        
        /* Add Article Form */
        .add-form {{
            background: rgba(255, 255, 255, 0.95);
            border-radius: 12px;
            padding: 12px;
            margin-bottom: 15px;
            box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
        }}
        
        .url-input {{
            width: 100%;
            padding: 12px;
            border: 2px solid #e5e7eb;
            border-radius: 8px;
            font-size: 14px;
            margin-bottom: 10px;
        }}
        
        .url-input:focus {{
            outline: none;
            border-color: #667eea;
        }}
        
        .add-btn {{
            width: 100%;
            padding: 12px;
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: white;
            border: none;
            border-radius: 8px;
            font-weight: 600;
            font-size: 14px;
            cursor: pointer;
        }}
        
        /* View Toggle */
        .view-toggle {{
            display: flex;
            background: rgba(255, 255, 255, 0.95);
            border-radius: 12px;
            padding: 5px;
            margin-bottom: 15px;
            box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
        }}
        
        .view-btn {{
            flex: 1;
            padding: 10px;
            background: transparent;
            border: none;
            border-radius: 8px;
            font-size: 14px;
            font-weight: 500;
            color: #666;
            transition: all 0.3s;
        }}
        
        .view-btn.active {{
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: white;
        }}
        
        /* Mobile Kanban */
        .mobile-kanban {{
            display: none;
            background: rgba(255, 255, 255, 0.98);
            border-radius: 12px;
            padding: 15px;
            min-height: 400px;
        }}
        
        .mobile-kanban.active {{
            display: block;
        }}
        
        .stage-selector {{
            display: flex;
            gap: 5px;
            margin-bottom: 15px;
            overflow-x: auto;
            -webkit-overflow-scrolling: touch;
            padding-bottom: 5px;
        }}
        
        .stage-tab {{
            padding: 8px 16px;
            background: #f3f4f6;
            border: none;
            border-radius: 20px;
            font-size: 14px;
            font-weight: 500;
            white-space: nowrap;
            color: #666;
            flex-shrink: 0;
        }}
        
        .stage-tab.active {{
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: white;
        }}
        
        .stage-tab .count {{
            display: inline-block;
            background: rgba(255, 255, 255, 0.3);
            padding: 2px 6px;
            border-radius: 10px;
            font-size: 11px;
            margin-left: 5px;
        }}
        
        /* Article Cards */
        .articles-list {{
            display: flex;
            flex-direction: column;
            gap: 10px;
            max-height: 60vh;
            overflow-y: auto;
            -webkit-overflow-scrolling: touch;
            padding-right: 5px;
        }}
        
        .article-card {{
            background: white;
            border-radius: 12px;
            padding: 15px;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
            transition: all 0.3s;
            cursor: pointer;
            position: relative;
        }}
        
        .article-card.dragging {{
            opacity: 0.5;
            transform: scale(0.95);
        }}
        
        .article-header {{
            display: flex;
            align-items: flex-start;
            gap: 10px;
            margin-bottom: 10px;
        }}
        
        .domain-icon {{
            font-size: 24px;
            flex-shrink: 0;
        }}
        
        .article-title {{
            font-weight: 600;
            font-size: 14px;
            color: #1a1a1a;
            line-height: 1.4;
            word-break: break-word;
        }}
        
        .article-meta {{
            display: flex;
            gap: 5px;
            flex-wrap: wrap;
            margin-bottom: 10px;
        }}
        
        .meta-badge {{
            padding: 3px 8px;
            border-radius: 12px;
            font-size: 11px;
            font-weight: 500;
        }}
        
        .priority-high {{ background: #fee2e2; color: #dc2626; }}
        .priority-medium {{ background: #fef3c7; color: #d97706; }}
        .priority-low {{ background: #dbeafe; color: #2563eb; }}
        .quantum-score {{ background: linear-gradient(135deg, #667eea, #764ba2); color: white; }}
        
        .article-actions {{
            display: flex;
            gap: 8px;
        }}
        
        .action-btn {{
            flex: 1;
            padding: 8px;
            background: #f3f4f6;
            border: none;
            border-radius: 8px;
            font-size: 12px;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 5px;
            cursor: pointer;
            transition: all 0.2s;
        }}
        
        .action-btn:active {{
            transform: scale(0.95);
        }}
        
        /* Calendar View */
        .calendar-view {{
            display: none;
            background: rgba(255, 255, 255, 0.98);
            border-radius: 12px;
            padding: 15px;
        }}
        
        .calendar-view.active {{
            display: block;
        }}
        
        .calendar-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 15px;
        }}
        
        .calendar-grid {{
            display: grid;
            grid-template-columns: repeat(7, 1fr);
            gap: 5px;
        }}
        
        .calendar-day {{
            aspect-ratio: 1;
            background: #f9fafb;
            border-radius: 8px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 12px;
            position: relative;
        }}
        
        .calendar-day.has-article {{
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: white;
        }}
        
        /* Bottom Navigation */
        .bottom-nav {{
            position: fixed;
            bottom: 0;
            left: 0;
            right: 0;
            background: rgba(255, 255, 255, 0.98);
            backdrop-filter: blur(20px);
            -webkit-backdrop-filter: blur(20px);
            border-top: 1px solid #e5e7eb;
            display: flex;
            justify-content: space-around;
            padding: 8px 0;
            padding-bottom: calc(8px + env(safe-area-inset-bottom));
            z-index: 1000;
        }}
        
        .nav-item {{
            flex: 1;
            display: flex;
            flex-direction: column;
            align-items: center;
            padding: 8px;
            background: none;
            border: none;
            color: #9ca3af;
            cursor: pointer;
            transition: all 0.2s;
        }}
        
        .nav-item.active {{
            color: #667eea;
        }}
        
        .nav-icon {{
            font-size: 20px;
            margin-bottom: 4px;
        }}
        
        .nav-label {{
            font-size: 11px;
            font-weight: 500;
        }}
        
        /* Toast */
        .toast {{
            position: fixed;
            bottom: 80px;
            left: 50%;
            transform: translateX(-50%);
            background: #10b981;
            color: white;
            padding: 12px 20px;
            border-radius: 25px;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
            display: none;
            animation: slideUp 0.3s ease;
            z-index: 2000;
            font-size: 14px;
        }}
        
        @keyframes slideUp {{
            from {{
                transform: translate(-50%, 100%);
                opacity: 0;
            }}
            to {{
                transform: translate(-50%, 0);
                opacity: 1;
            }}
        }}
        
        /* Mobile Optimizations */
        @media (max-width: 768px) {{
            .container {{
                padding: 8px;
            }}
            
            .header {{
                padding: 10px 12px;
            }}
            
            .logo {{
                font-size: 16px;
            }}
            
            .articles-list {{
                max-height: calc(100vh - 280px);
            }}
        }}
        
        /* PWA Install Prompt */
        .pwa-prompt {{
            position: fixed;
            bottom: 100px;
            left: 10px;
            right: 10px;
            background: white;
            border-radius: 12px;
            padding: 15px;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.2);
            display: none;
            z-index: 1500;
        }}
        
        .pwa-prompt.show {{
            display: block;
            animation: slideUp 0.3s ease;
        }}
        
        .pwa-prompt-title {{
            font-weight: 600;
            margin-bottom: 8px;
        }}
        
        .pwa-prompt-text {{
            font-size: 14px;
            color: #666;
            margin-bottom: 12px;
        }}
        
        .pwa-prompt-buttons {{
            display: flex;
            gap: 10px;
        }}
        
        .pwa-prompt-btn {{
            flex: 1;
            padding: 10px;
            border: none;
            border-radius: 8px;
            font-weight: 500;
            cursor: pointer;
        }}
        
        .pwa-prompt-btn.install {{
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: white;
        }}
        
        .pwa-prompt-btn.cancel {{
            background: #f3f4f6;
            color: #666;
        }}
    </style>
</head>
<body>
    <div class="container">
        <!-- Header -->
        <div class="header">
            <div class="logo">📚 Article Hub</div>
            <button class="install-btn" id="installBtn">Install App</button>
        </div>
        
        <!-- Stats -->
        <div class="stats-container">
            <div class="stat-card">
                <div class="stat-number" id="totalArticles">0</div>
                <div class="stat-label">Total Articles</div>
            </div>
            <div class="stat-card">
                <div class="stat-number" id="completionRate">0%</div>
                <div class="stat-label">Completion</div>
            </div>
        </div>
        
        <!-- Add Article Form -->
        <div class="add-form">
            <input type="url" 
                   class="url-input" 
                   id="urlInput" 
                   placeholder="Paste article URL here...">
            <button class="add-btn" onclick="addArticle()">
                ➕ Add Article
            </button>
        </div>
        
        <!-- View Toggle -->
        <div class="view-toggle">
            <button class="view-btn active" onclick="switchView('kanban')">
                📋 Kanban
            </button>
            <button class="view-btn" onclick="switchView('calendar')">
                📅 Calendar
            </button>
        </div>
        
        <!-- Mobile Kanban -->
        <div class="mobile-kanban active" id="kanbanView">
            <div class="stage-selector" id="stageSelector">
                <button class="stage-tab active" onclick="selectStage('inbox')">
                    📥 Inbox <span class="count">0</span>
                </button>
                <button class="stage-tab" onclick="selectStage('reading')">
                    📖 Reading <span class="count">0</span>
                </button>
                <button class="stage-tab" onclick="selectStage('reviewing')">
                    🔍 Review <span class="count">0</span>
                </button>
                <button class="stage-tab" onclick="selectStage('completed')">
                    ✅ Done <span class="count">0</span>
                </button>
            </div>
            <div class="articles-list" id="articlesList">
                <!-- Articles will be loaded here -->
            </div>
        </div>
        
        <!-- Calendar View -->
        <div class="calendar-view" id="calendarView">
            <div class="calendar-header">
                <button onclick="previousWeek()">◀</button>
                <span id="weekRange">This Week</span>
                <button onclick="nextWeek()">▶</button>
            </div>
            <div class="calendar-grid" id="calendarGrid">
                <!-- Calendar will be generated here -->
            </div>
        </div>
    </div>
    
    <!-- Bottom Navigation -->
    <div class="bottom-nav">
        <button class="nav-item active" onclick="switchView('kanban')">
            <span class="nav-icon">📋</span>
            <span class="nav-label">Kanban</span>
        </button>
        <button class="nav-item" onclick="switchView('calendar')">
            <span class="nav-icon">📅</span>
            <span class="nav-label">Calendar</span>
        </button>
        <button class="nav-item" onclick="openLIFF()">
            <span class="nav-icon">📱</span>
            <span class="nav-label">LINE</span>
        </button>
        <button class="nav-item" onclick="showStats()">
            <span class="nav-icon">📊</span>
            <span class="nav-label">Stats</span>
        </button>
    </div>
    
    <!-- Toast -->
    <div class="toast" id="toast"></div>
    
    <!-- PWA Install Prompt -->
    <div class="pwa-prompt" id="pwaPrompt">
        <div class="pwa-prompt-title">📲 Install Article Hub</div>
        <div class="pwa-prompt-text">Add to your home screen for quick access</div>
        <div class="pwa-prompt-buttons">
            <button class="pwa-prompt-btn cancel" onclick="closePWAPrompt()">Later</button>
            <button class="pwa-prompt-btn install" onclick="installPWA()">Install</button>
        </div>
    </div>
    
    <script>
        // Global variables
        let articles = [];
        let currentStage = 'inbox';
        let currentView = 'kanban';
        let deferredPrompt = null;
        let draggedElement = null;
        
        // LIFF initialization
        const liffId = '2007552096-GxP76rNd';
        
        async function initializeLiff() {{
            try {{
                await liff.init({{ liffId: liffId }});
                console.log('LIFF initialized');
                
                if (liff.isInClient()) {{
                    console.log('Running in LINE app');
                }}
            }} catch (error) {{
                console.error('LIFF init failed:', error);
            }}
        }}
        
        // PWA Installation
        window.addEventListener('beforeinstallprompt', (e) => {{
            e.preventDefault();
            deferredPrompt = e;
            
            // Show install button in header
            const installBtn = document.getElementById('installBtn');
            installBtn.classList.add('show');
            
            // Show PWA prompt after 30 seconds
            setTimeout(() => {{
                if (deferredPrompt) {{
                    document.getElementById('pwaPrompt').classList.add('show');
                }}
            }}, 30000);
        }});
        
        function installPWA() {{
            if (deferredPrompt) {{
                deferredPrompt.prompt();
                deferredPrompt.userChoice.then((choiceResult) => {{
                    if (choiceResult.outcome === 'accepted') {{
                        showToast('App installed successfully!');
                    }}
                    deferredPrompt = null;
                    closePWAPrompt();
                }});
            }}
        }}
        
        function closePWAPrompt() {{
            document.getElementById('pwaPrompt').classList.remove('show');
        }}
        
        // Service Worker Registration
        if ('serviceWorker' in navigator) {{
            window.addEventListener('load', () => {{
                navigator.serviceWorker.register('/service-worker.js')
                    .then(registration => {{
                        console.log('Service Worker registered');
                        
                        // Check for updates every hour
                        setInterval(() => {{
                            registration.update();
                        }}, 3600000);
                    }})
                    .catch(err => {{
                        console.log('Service Worker registration failed:', err);
                    }});
            }});
        }}
        
        // Initialize on load
        document.addEventListener('DOMContentLoaded', function() {{
            initializeLiff();
            loadArticles();
            updateStats();
            
            // Install button in header
            document.getElementById('installBtn').addEventListener('click', installPWA);
            
            // Handle iOS PWA
            if (window.navigator.standalone) {{
                console.log('Running as iOS PWA');
            }}
            
            // Auto-refresh every 30 seconds
            setInterval(loadArticles, 30000);
        }});
        
        // Load articles
        async function loadArticles() {{
            try {{
                const response = await fetch('/api/articles');
                const data = await response.json();
                articles = data.articles || [];
                renderArticles();
                updateStats();
                updateStageCounts();
            }} catch (error) {{
                console.error('Error loading articles:', error);
            }}
        }}
        
        // Render articles for current stage
        function renderArticles() {{
            const list = document.getElementById('articlesList');
            const stageArticles = articles.filter(a => a.stage === currentStage);
            
            list.innerHTML = '';
            
            if (stageArticles.length === 0) {{
                list.innerHTML = `
                    <div style="text-align: center; padding: 40px; color: #999;">
                        <div style="font-size: 48px; margin-bottom: 10px;">📭</div>
                        <div>No articles in ${{currentStage}}</div>
                    </div>
                `;
                return;
            }}
            
            stageArticles.forEach(article => {{
                const card = createArticleCard(article);
                list.appendChild(card);
            }});
            
            setupDragAndDrop();
        }}
        
        // Create article card
        function createArticleCard(article) {{
            const card = document.createElement('div');
            card.className = 'article-card';
            card.draggable = true;
            card.dataset.articleId = article.id;
            
            const icon = getDomainIcon(article.url);
            const priorityClass = `priority-${{article.priority || 'medium'}}`;
            
            card.innerHTML = `
                <div class="article-header">
                    <span class="domain-icon">${{icon}}</span>
                    <div class="article-title">${{escapeHtml(article.title || 'Untitled')}}</div>
                </div>
                <div class="article-meta">
                    <span class="meta-badge ${{priorityClass}}">${{article.priority || 'medium'}}</span>
                    <span class="meta-badge quantum-score">⚡ ${{article.quantum_score || 0}}</span>
                </div>
                <div class="article-actions">
                    <button class="action-btn" onclick="copyUrl('${{escapeHtml(article.url)}}', event)">
                        📋 Copy
                    </button>
                    <button class="action-btn" onclick="openUrl('${{escapeHtml(article.url)}}')">
                        🔗 Open
                    </button>
                    <button class="action-btn" onclick="moveToNextStage(${{article.id}})">
                        ➡️ Next
                    </button>
                </div>
            `;
            
            return card;
        }}
        
        // Get domain icon
        function getDomainIcon(url) {{
            const urlLower = url.toLowerCase();
            if (urlLower.includes('github.com')) return '🐙';
            if (urlLower.includes('youtube.com')) return '📺';
            if (urlLower.includes('medium.com')) return '📰';
            if (urlLower.includes('twitter.com') || urlLower.includes('x.com')) return '🐦';
            if (urlLower.includes('facebook.com')) return '📘';
            if (urlLower.includes('linkedin.com')) return '💼';
            if (urlLower.includes('reddit.com')) return '🤖';
            return '🌐';
        }}
        
        // Stage selection
        function selectStage(stage) {{
            currentStage = stage;
            
            // Update tabs
            document.querySelectorAll('.stage-tab').forEach(tab => {{
                tab.classList.remove('active');
            }});
            event.target.classList.add('active');
            
            renderArticles();
        }}
        
        // Update stage counts
        function updateStageCounts() {{
            const stages = ['inbox', 'reading', 'reviewing', 'completed'];
            stages.forEach((stage, index) => {{
                const count = articles.filter(a => a.stage === stage).length;
                const tabs = document.querySelectorAll('.stage-tab');
                if (tabs[index]) {{
                    tabs[index].querySelector('.count').textContent = count;
                }}
            }});
        }}
        
        // Switch view
        function switchView(view) {{
            currentView = view;
            
            // Update buttons
            document.querySelectorAll('.view-btn').forEach(btn => {{
                btn.classList.remove('active');
            }});
            event.target.classList.add('active');
            
            // Update nav
            document.querySelectorAll('.nav-item').forEach(item => {{
                item.classList.remove('active');
            }});
            if (view === 'kanban') {{
                document.querySelectorAll('.nav-item')[0].classList.add('active');
            }} else if (view === 'calendar') {{
                document.querySelectorAll('.nav-item')[1].classList.add('active');
            }}
            
            // Show/hide views
            document.getElementById('kanbanView').classList.toggle('active', view === 'kanban');
            document.getElementById('calendarView').classList.toggle('active', view === 'calendar');
            
            if (view === 'calendar') {{
                renderCalendar();
            }}
        }}
        
        // Add article
        async function addArticle() {{
            const urlInput = document.getElementById('urlInput');
            const url = urlInput.value.trim();
            
            if (!url) {{
                showToast('Please enter a URL', 'error');
                return;
            }}
            
            try {{
                const response = await fetch('/api/articles', {{
                    method: 'POST',
                    headers: {{ 'Content-Type': 'application/json' }},
                    body: JSON.stringify({{ url: url }})
                }});
                
                if (response.ok) {{
                    urlInput.value = '';
                    loadArticles();
                    showToast('Article added!');
                }}
            }} catch (error) {{
                showToast('Failed to add article', 'error');
            }}
        }}
        
        // Move to next stage
        async function moveToNextStage(articleId) {{
            const stages = ['inbox', 'reading', 'reviewing', 'completed'];
            const article = articles.find(a => a.id === articleId);
            const currentIndex = stages.indexOf(article.stage);
            
            if (currentIndex < stages.length - 1) {{
                const newStage = stages[currentIndex + 1];
                await updateArticleStage(articleId, newStage);
            }}
        }}
        
        // Update article stage
        async function updateArticleStage(articleId, newStage) {{
            try {{
                const response = await fetch('/api/articles/update', {{
                    method: 'POST',
                    headers: {{ 'Content-Type': 'application/json' }},
                    body: JSON.stringify({{
                        id: articleId,
                        stage: newStage
                    }})
                }});
                
                if (response.ok) {{
                    loadArticles();
                    showToast('Article moved!');
                }}
            }} catch (error) {{
                showToast('Failed to update', 'error');
            }}
        }}
        
        // Copy URL
        function copyUrl(url, event) {{
            event.stopPropagation();
            navigator.clipboard.writeText(url).then(() => {{
                showToast('URL copied!');
            }});
        }}
        
        // Open URL
        function openUrl(url) {{
            window.open(url, '_blank');
        }}
        
        // Open LIFF
        function openLIFF() {{
            if (liff.isInClient()) {{
                liff.openWindow({{
                    url: 'https://liff.line.me/2007552096-GxP76rNd',
                    external: false
                }});
            }} else {{
                window.open('https://liff.line.me/2007552096-GxP76rNd', '_blank');
            }}
        }}
        
        // Show stats
        function showStats() {{
            const total = articles.length;
            const completed = articles.filter(a => a.stage === 'completed').length;
            const rate = total > 0 ? Math.round((completed / total) * 100) : 0;
            
            showToast(`Total: ${{total}} | Completed: ${{completed}} | Rate: ${{rate}}%`);
        }}
        
        // Update stats
        function updateStats() {{
            document.getElementById('totalArticles').textContent = articles.length;
            
            const completed = articles.filter(a => a.stage === 'completed').length;
            const rate = articles.length > 0 
                ? Math.round((completed / articles.length) * 100) 
                : 0;
            document.getElementById('completionRate').textContent = rate + '%';
        }}
        
        // Render calendar
        function renderCalendar() {{
            const grid = document.getElementById('calendarGrid');
            grid.innerHTML = '';
            
            const days = ['S', 'M', 'T', 'W', 'T', 'F', 'S'];
            
            days.forEach(day => {{
                const dayEl = document.createElement('div');
                dayEl.className = 'calendar-day';
                dayEl.textContent = day;
                grid.appendChild(dayEl);
            }});
            
            // Add empty days for now
            for (let i = 0; i < 28; i++) {{
                const dayEl = document.createElement('div');
                dayEl.className = 'calendar-day';
                dayEl.textContent = i + 1;
                grid.appendChild(dayEl);
            }}
        }}
        
        // Drag and drop setup
        function setupDragAndDrop() {{
            const cards = document.querySelectorAll('.article-card');
            
            cards.forEach(card => {{
                card.addEventListener('dragstart', handleDragStart);
                card.addEventListener('dragend', handleDragEnd);
                
                // Touch events for mobile
                card.addEventListener('touchstart', handleTouchStart, {{passive: false}});
                card.addEventListener('touchmove', handleTouchMove, {{passive: false}});
                card.addEventListener('touchend', handleTouchEnd);
            }});
        }}
        
        function handleDragStart(e) {{
            draggedElement = e.target;
            e.target.classList.add('dragging');
        }}
        
        function handleDragEnd(e) {{
            e.target.classList.remove('dragging');
            draggedElement = null;
        }}
        
        // Touch support for mobile
        let touchItem = null;
        let touchOffset = {{x: 0, y: 0}};
        
        function handleTouchStart(e) {{
            touchItem = e.target.closest('.article-card');
            if (!touchItem) return;
            
            const touch = e.touches[0];
            touchOffset.x = touch.clientX - touchItem.offsetLeft;
            touchOffset.y = touch.clientY - touchItem.offsetTop;
            
            touchItem.style.position = 'fixed';
            touchItem.style.zIndex = '1000';
            touchItem.classList.add('dragging');
        }}
        
        function handleTouchMove(e) {{
            if (!touchItem) return;
            e.preventDefault();
            
            const touch = e.touches[0];
            touchItem.style.left = (touch.clientX - touchOffset.x) + 'px';
            touchItem.style.top = (touch.clientY - touchOffset.y) + 'px';
        }}
        
        function handleTouchEnd(e) {{
            if (!touchItem) return;
            
            touchItem.style.position = '';
            touchItem.style.zIndex = '';
            touchItem.style.left = '';
            touchItem.style.top = '';
            touchItem.classList.remove('dragging');
            
            touchItem = null;
        }}
        
        // Toast notification
        function showToast(message, type = 'success') {{
            const toast = document.getElementById('toast');
            toast.textContent = message;
            toast.style.background = type === 'error' ? '#ef4444' : '#10b981';
            toast.style.display = 'block';
            
            setTimeout(() => {{
                toast.style.display = 'none';
            }}, 3000);
        }}
        
        // Utility functions
        function escapeHtml(text) {{
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        }}
        
        // Week navigation
        function previousWeek() {{
            showToast('Previous week');
        }}
        
        function nextWeek() {{
            showToast('Next week');
        }}
    </script>
</body>
</html>'''
        
        self.send_response(200)
        self.send_header('Content-Type', 'text/html')
        self.send_header('Cache-Control', 'no-cache')
        self.end_headers()
        self.wfile.write(html.encode())
    
    def serve_manifest(self):
        """Serve PWA manifest with correct MIME type"""
        manifest = {
            "name": "Article Intelligence Hub",
            "short_name": "ArticleHub",
            "description": "AI-powered article management",
            "start_url": "/",
            "display": "standalone",
            "background_color": "#667eea",
            "theme_color": "#667eea",
            "orientation": "portrait",
            "scope": "/",
            "icons": [
                {
                    "src": "/icon-192x192.png",
                    "sizes": "192x192",
                    "type": "image/png",
                    "purpose": "any maskable"
                },
                {
                    "src": "/icon-512x512.png",
                    "sizes": "512x512",
                    "type": "image/png",
                    "purpose": "any maskable"
                }
            ]
        }
        
        self.send_response(200)
        self.send_header('Content-Type', 'application/manifest+json')
        self.send_header('Cache-Control', 'public, max-age=3600')
        self.end_headers()
        self.wfile.write(json.dumps(manifest).encode())
    
    def serve_service_worker(self):
        """Serve service worker with correct headers"""
        sw_code = '''
// Service Worker for Article Hub PWA
const CACHE_NAME = 'article-hub-v2';
const urlsToCache = [
  '/',
  '/manifest.json'
];

self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => cache.addAll(urlsToCache))
      .then(() => self.skipWaiting())
  );
});

self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys().then(cacheNames => {
      return Promise.all(
        cacheNames.map(cacheName => {
          if (cacheName !== CACHE_NAME) {
            return caches.delete(cacheName);
          }
        })
      );
    }).then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', event => {
  if (event.request.url.includes('/api/')) {
    // Network first for API calls
    event.respondWith(
      fetch(event.request)
        .catch(() => caches.match(event.request))
    );
  } else {
    // Cache first for static assets
    event.respondWith(
      caches.match(event.request)
        .then(response => response || fetch(event.request))
    );
  }
});'''
        
        self.send_response(200)
        self.send_header('Content-Type', 'application/javascript')
        self.send_header('Service-Worker-Allowed', '/')
        self.send_header('Cache-Control', 'no-cache')
        self.end_headers()
        self.wfile.write(sw_code.encode())
    
    def serve_offline_page(self):
        """Serve offline page"""
        html = '''<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Offline - Article Hub</title>
    <style>
        body {
            margin: 0;
            padding: 20px;
            font-family: -apple-system, BlinkMacSystemFont, sans-serif;
            background: linear-gradient(135deg, #667eea, #764ba2);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .offline-container {
            background: white;
            border-radius: 20px;
            padding: 40px;
            text-align: center;
            max-width: 300px;
        }
        h1 { color: #333; }
        p { color: #666; }
        button {
            margin-top: 20px;
            padding: 12px 30px;
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: white;
            border: none;
            border-radius: 8px;
            font-size: 16px;
            cursor: pointer;
        }
    </style>
</head>
<body>
    <div class="offline-container">
        <h1>📴 You're Offline</h1>
        <p>Your articles are saved and will sync when you're back online.</p>
        <button onclick="location.reload()">Try Again</button>
    </div>
</body>
</html>'''
        
        self.send_response(200)
        self.send_header('Content-Type', 'text/html')
        self.end_headers()
        self.wfile.write(html.encode())
    
    def serve_icon(self):
        """Serve app icon"""
        # Simple colored square as icon
        svg = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512">
  <rect width="512" height="512" rx="80" fill="#667eea"/>
  <text x="256" y="320" font-family="Arial" font-size="240" text-anchor="middle" fill="white">📚</text>
</svg>'''
        
        self.send_response(200)
        self.send_header('Content-Type', 'image/svg+xml')
        self.send_header('Cache-Control', 'public, max-age=86400')
        self.end_headers()
        self.wfile.write(svg.encode())
    
    def serve_articles(self):
        """Serve articles API"""
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM articles_kanban 
            WHERE is_archived = 0 
            ORDER BY id DESC
        ''')
        
        articles = []
        for row in cursor.fetchall():
            article = dict(row)
            if article.get('title'):
                article['title'] = ' '.join(str(article['title']).split())
            articles.append(article)
        
        conn.close()
        
        response = json.dumps({'articles': articles})
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Cache-Control', 'no-cache')
        self.end_headers()
        self.wfile.write(response.encode())
    
    def handle_add_article(self, post_data):
        """Handle adding new article"""
        try:
            data = json.loads(post_data)
            url = data.get('url', '').strip()
            
            if not url:
                self.send_error(400, 'URL required')
                return
            
            # Extract metadata
            title = self.extract_title_from_url(url)
            category = self.detect_category(url)
            quantum_score = random.randint(400, 900)
            
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO articles_kanban 
                (url, url_hash, title, category, stage, priority, quantum_score, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                url,
                hashlib.md5(url.encode()).hexdigest(),
                title,
                category,
                'inbox',
                'medium',
                quantum_score,
                datetime.now().isoformat()
            ))
            
            conn.commit()
            conn.close()
            
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'success': True}).encode())
            
        except Exception as e:
            logging.error(f'Error adding article: {e}')
            self.send_error(500, str(e))
    
    def handle_update_article(self, post_data):
        """Handle updating article"""
        try:
            data = json.loads(post_data)
            article_id = data.get('id')
            new_stage = data.get('stage')
            
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE articles_kanban 
                SET stage = ?, updated_at = ?
                WHERE id = ?
            ''', (new_stage, datetime.now().isoformat(), article_id))
            
            conn.commit()
            conn.close()
            
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'success': True}).encode())
            
        except Exception as e:
            logging.error(f'Error updating article: {e}')
            self.send_error(500, str(e))
    
    def extract_title_from_url(self, url):
        """Extract title from URL"""
        title = re.sub(r'^https?://(www\.)?', '', url)
        title = title.split('?')[0].split('#')[0]
        parts = title.split('/')
        if len(parts) > 1 and parts[-1]:
            title = parts[-1].replace('-', ' ').replace('_', ' ').title()
        else:
            title = parts[0].split('.')[0].title()
        return title[:100]
    
    def detect_category(self, url):
        """Detect category from URL"""
        url_lower = url.lower()
        if any(x in url_lower for x in ['github.com', 'gitlab.com']):
            return 'Development'
        elif any(x in url_lower for x in ['youtube.com', 'vimeo.com']):
            return 'Video'
        elif any(x in url_lower for x in ['medium.com', 'dev.to']):
            return 'Articles'
        else:
            return 'General'
    
    def handle_line_webhook(self, post_data):
        """Handle LINE webhook events"""
        try:
            import urllib.request
            
            # Parse webhook event
            events = json.loads(post_data)
            logging.info(f"LINE Webhook received: {events}")
            
            for event in events.get('events', []):
                if event['type'] == 'message' and event['message']['type'] == 'text':
                    user_id = event['source'].get('userId')
                    reply_token = event['replyToken']
                    message_text = event['message']['text']
                    
                    # Check for URLs
                    url_pattern = r'https?://[^\s]+'
                    urls = re.findall(url_pattern, message_text)
                    
                    if urls:
                        # Save URLs as articles
                        saved_count = 0
                        for url in urls:
                            if self.save_article_from_line(url, user_id):
                                saved_count += 1
                        
                        # Send flex message response
                        if saved_count > 0:
                            self.send_article_saved_flex(reply_token, saved_count)
                    else:
                        # Handle commands
                        if message_text.lower() in ['/help', 'help', '?']:
                            self.send_help_message(reply_token)
                        elif message_text.lower() == '/list':
                            self.send_article_list(reply_token)
                        elif message_text.lower() == '/stats':
                            self.send_stats_message(reply_token)
                        elif message_text.lower() == '/web':
                            self.send_web_link(reply_token)
                        else:
                            self.send_quick_reply(reply_token)
            
            # Return 200 OK to LINE
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'success': True}).encode())
            
        except Exception as e:
            logging.error(f'Webhook error: {e}')
            # Still return 200 to avoid retries
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'success': False}).encode())
    
    def save_article_from_line(self, url, user_id):
        """Save article from LINE message"""
        try:
            title = self.extract_title_from_url(url)
            category = self.detect_category(url)
            quantum_score = random.randint(400, 900)
            
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO articles_kanban 
                (url, url_hash, title, category, stage, priority, quantum_score, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                url,
                hashlib.md5(url.encode()).hexdigest(),
                title,
                category,
                'inbox',
                'medium',
                quantum_score,
                datetime.now().isoformat()
            ))
            
            conn.commit()
            conn.close()
            
            logging.info(f"Article saved from LINE: {url}")
            return True
            
        except Exception as e:
            logging.error(f"Error saving article: {e}")
            return False
    
    def send_article_saved_flex(self, reply_token, count):
        """Send flex message for saved articles"""
        try:
            import urllib.request
            
            flex_message = {
                "type": "flex",
                "altText": f"✅ Saved {count} article(s)",
                "contents": {
                    "type": "bubble",
                    "hero": {
                        "type": "box",
                        "layout": "vertical",
                        "contents": [
                            {
                                "type": "text",
                                "text": f"✅ {count} Article{'s' if count > 1 else ''} Saved!",
                                "weight": "bold",
                                "size": "xl",
                                "color": "#FFFFFF",
                                "align": "center"
                            }
                        ],
                        "backgroundColor": "#10b981",
                        "paddingAll": "20px"
                    },
                    "body": {
                        "type": "box",
                        "layout": "vertical",
                        "contents": [
                            {
                                "type": "text",
                                "text": "Added to your reading list",
                                "wrap": True,
                                "color": "#666666",
                                "margin": "md"
                            }
                        ]
                    },
                    "footer": {
                        "type": "box",
                        "layout": "vertical",
                        "spacing": "sm",
                        "contents": [
                            {
                                "type": "button",
                                "style": "primary",
                                "color": "#667eea",
                                "action": {
                                    "type": "uri",
                                    "label": "📚 Open Article Hub",
                                    "uri": "https://09f85f116221.ngrok-free.app"
                                }
                            },
                            {
                                "type": "button",
                                "action": {
                                    "type": "message",
                                    "label": "📋 View Articles",
                                    "text": "/list"
                                }
                            }
                        ]
                    }
                }
            }
            
            self.send_line_reply(reply_token, [flex_message])
            
        except Exception as e:
            logging.error(f"Error sending flex message: {e}")
    
    def send_help_message(self, reply_token):
        """Send help message"""
        help_text = (
            "📚 Article Hub Commands:\n"
            "• Send any URL to save it\n"
            "• /list - Show recent articles\n"
            "• /stats - View statistics\n"
            "• /web - Open web interface\n"
            "• /help - This message"
        )
        self.send_line_reply(reply_token, [{
            "type": "text",
            "text": help_text
        }])
    
    def send_article_list(self, reply_token):
        """Send list of recent articles"""
        try:
            conn = sqlite3.connect(DB_PATH)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT title, stage FROM articles_kanban 
                WHERE is_archived = 0 
                ORDER BY id DESC 
                LIMIT 5
            ''')
            
            articles = cursor.fetchall()
            conn.close()
            
            if articles:
                article_list = "📚 Recent Articles:\n\n"
                for i, article in enumerate(articles, 1):
                    title = article['title'] or 'Untitled'
                    stage = article['stage']
                    article_list += f"{i}. {title[:30]}... [{stage}]\n"
            else:
                article_list = "No articles yet. Send URLs to save them!"
            
            self.send_line_reply(reply_token, [{
                "type": "text",
                "text": article_list
            }])
            
        except Exception as e:
            logging.error(f"Error sending article list: {e}")
    
    def send_stats_message(self, reply_token):
        """Send statistics"""
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            
            cursor.execute('SELECT COUNT(*) FROM articles_kanban WHERE is_archived = 0')
            total = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM articles_kanban WHERE stage = 'completed' AND is_archived = 0")
            completed = cursor.fetchone()[0]
            
            conn.close()
            
            rate = round((completed / max(total, 1)) * 100)
            
            stats_text = (
                f"📊 Your Statistics:\n"
                f"• Total articles: {total}\n"
                f"• Completed: {completed}\n"
                f"• Completion rate: {rate}%"
            )
            
            self.send_line_reply(reply_token, [{
                "type": "text",
                "text": stats_text
            }])
            
        except Exception as e:
            logging.error(f"Error sending stats: {e}")
    
    def send_web_link(self, reply_token):
        """Send web interface link"""
        self.send_line_reply(reply_token, [{
            "type": "text",
            "text": "🌐 Open Article Hub:\nhttps://09f85f116221.ngrok-free.app\n\n📱 Or use LIFF:\nhttps://liff.line.me/2007552096-GxP76rNd"
        }])
    
    def send_quick_reply(self, reply_token):
        """Send message with quick reply buttons"""
        message = {
            "type": "text",
            "text": "Send me a URL to save it, or choose:",
            "quickReply": {
                "items": [
                    {
                        "type": "action",
                        "action": {
                            "type": "message",
                            "label": "📋 Articles",
                            "text": "/list"
                        }
                    },
                    {
                        "type": "action",
                        "action": {
                            "type": "message",
                            "label": "📊 Stats",
                            "text": "/stats"
                        }
                    },
                    {
                        "type": "action",
                        "action": {
                            "type": "message",
                            "label": "🌐 Web",
                            "text": "/web"
                        }
                    },
                    {
                        "type": "action",
                        "action": {
                            "type": "message",
                            "label": "❓ Help",
                            "text": "/help"
                        }
                    }
                ]
            }
        }
        self.send_line_reply(reply_token, [message])
    
    def send_line_reply(self, reply_token, messages):
        """Send reply to LINE"""
        try:
            import urllib.request
            
            url = 'https://api.line.me/v2/bot/message/reply'
            headers = {
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {LINE_CHANNEL_ACCESS_TOKEN}'
            }
            
            data = {
                'replyToken': reply_token,
                'messages': messages
            }
            
            req = urllib.request.Request(
                url,
                data=json.dumps(data).encode('utf-8'),
                headers=headers,
                method='POST'
            )
            
            with urllib.request.urlopen(req) as response:
                logging.info(f"LINE reply sent: {response.status}")
                
        except Exception as e:
            logging.error(f"Error sending LINE reply: {e}")
    
    def log_message(self, format, *args):
        """Suppress default HTTP logging"""
        return

def initialize_database():
    """Initialize database"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS articles_kanban (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            url TEXT NOT NULL,
            url_hash TEXT UNIQUE,
            title TEXT,
            summary TEXT,
            category TEXT,
            stage TEXT DEFAULT 'inbox',
            priority TEXT DEFAULT 'medium',
            quantum_score INTEGER DEFAULT 0,
            is_archived BOOLEAN DEFAULT 0,
            created_at TEXT,
            updated_at TEXT
        )
    ''')
    
    conn.commit()
    conn.close()

def main():
    print("\n" + "="*60)
    print("📱 MOBILE-OPTIMIZED ARTICLE HUB")
    print("="*60)
    print(f"\n✅ Starting on http://localhost:{PORT}")
    print("\n✨ Mobile Features:")
    print("  • Touch-optimized Kanban")
    print("  • PWA installable")
    print("  • LIFF integrated")
    print("  • Offline support")
    print("  • Bottom navigation")
    print("\n🔗 LIFF URL: https://liff.line.me/2007552096-GxP76rNd")
    print("\n" + "="*60)
    print("\nPress Ctrl+C to stop\n")
    
    initialize_database()
    
    try:
        server = HTTPServer(('', PORT), RequestHandler)
        server.serve_forever()
    except KeyboardInterrupt:
        print('\n\nShutting down...')
        server.socket.close()
    except OSError as e:
        if e.errno == 48:
            print(f"\n❌ Port {PORT} is in use!")
            print("Run: lsof -ti:5001 | xargs kill -9")

if __name__ == '__main__':
    main()