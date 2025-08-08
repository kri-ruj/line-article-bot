#!/usr/bin/env python3
"""
🧠 ULTIMATE ARTICLE INTELLIGENCE WITH LIFF & LINE INTEGRATION
Full-width responsive layout with LINE Frontend Framework
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
        logging.FileHandler('app_liff.log'),
        logging.StreamHandler()
    ]
)

PORT = 5001
DB_PATH = 'articles_kanban.db'
LIFF_ID = os.getenv('LIFF_ID', '2007552096-GxP76rNd')
LINE_CHANNEL_ACCESS_TOKEN = os.getenv('LINE_CHANNEL_ACCESS_TOKEN', '')

class RequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed_path = urlparse(self.path)
        
        if parsed_path.path == '/':
            self.serve_homepage()
        elif parsed_path.path == '/api/articles':
            self.serve_articles()
        elif parsed_path.path == '/api/analytics':
            self.serve_analytics()
        elif parsed_path.path == '/liff':
            self.serve_liff_page()
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
        elif parsed_path.path == '/api/calendar/schedule':
            self.handle_schedule_article(post_data)
        elif parsed_path.path == '/api/line/send':
            self.handle_line_send(post_data)
        else:
            self.send_error(404)
    
    def serve_homepage(self):
        html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=no">
    <title>📚 Article Intelligence Hub</title>
    
    <!-- PWA Meta Tags -->
    <meta name="theme-color" content="#667eea">
    <meta name="apple-mobile-web-app-capable" content="yes">
    <meta name="apple-mobile-web-app-status-bar-style" content="default">
    <meta name="apple-mobile-web-app-title" content="Article Hub">
    <link rel="apple-touch-icon" href="/icon-192x192.png">
    
    <!-- PWA Manifest -->
    <link rel="manifest" href="/manifest.json">
    
    <!-- iOS PWA support -->
    <meta name="mobile-web-app-capable" content="yes">
    <meta name="apple-touch-icon" href="/icon-192x192.png">
    <link rel="apple-touch-startup-image" href="/icon-512x512.png">
    
    <!-- LINE LIFF SDK -->
    <script src="https://static.line-scdn.net/liff/edge/2/sdk.js"></script>
    
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            color: #333;
            overflow-x: hidden;
        }}
        
        /* Full-width container */
        .container {{
            width: 100%;
            max-width: 100vw;
            padding: 10px;
            margin: 0 auto;
        }}
        
        /* Header */
        .header {{
            background: rgba(255, 255, 255, 0.98);
            backdrop-filter: blur(20px);
            border-radius: 12px;
            padding: 15px 20px;
            margin-bottom: 15px;
            box-shadow: 0 8px 32px rgba(31, 38, 135, 0.15);
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 10px;
        }}
        
        .logo {{
            font-size: 24px;
            font-weight: bold;
            background: linear-gradient(135deg, #667eea, #764ba2);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            display: flex;
            align-items: center;
            gap: 10px;
        }}
        
        .line-status {{
            display: flex;
            align-items: center;
            gap: 10px;
            padding: 8px 16px;
            background: #00B900;
            color: white;
            border-radius: 20px;
            font-size: 14px;
        }}
        
        .line-status.disconnected {{
            background: #999;
        }}
        
        /* Stats Cards - Horizontal Layout */
        .stats-container {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-bottom: 20px;
        }}
        
        .stat-card {{
            background: rgba(255, 255, 255, 0.95);
            border-radius: 12px;
            padding: 20px;
            text-align: center;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
            transition: transform 0.3s;
        }}
        
        .stat-card:hover {{
            transform: translateY(-2px);
        }}
        
        .stat-number {{
            font-size: 32px;
            font-weight: bold;
            color: #667eea;
            margin-bottom: 5px;
        }}
        
        .stat-label {{
            color: #666;
            font-size: 14px;
        }}
        
        /* Main Layout - Side by Side */
        .main-layout {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
            margin-bottom: 20px;
        }}
        
        /* Kanban Board */
        .kanban-container {{
            background: rgba(255, 255, 255, 0.98);
            border-radius: 12px;
            padding: 20px;
            box-shadow: 0 8px 32px rgba(31, 38, 135, 0.15);
        }}
        
        .kanban-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
            padding-bottom: 15px;
            border-bottom: 2px solid #f0f0f0;
        }}
        
        .kanban-board {{
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 15px;
            min-height: 400px;
        }}
        
        .kanban-column {{
            background: #f8f9fa;
            border-radius: 8px;
            padding: 15px;
            min-height: 350px;
        }}
        
        .kanban-column.inbox {{ border-top: 3px solid #6366f1; }}
        .kanban-column.reading {{ border-top: 3px solid #f59e0b; }}
        .kanban-column.reviewing {{ border-top: 3px solid #8b5cf6; }}
        .kanban-column.completed {{ border-top: 3px solid #10b981; }}
        
        .column-header {{
            font-weight: 600;
            margin-bottom: 15px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        
        .column-count {{
            background: rgba(0,0,0,0.1);
            padding: 2px 8px;
            border-radius: 12px;
            font-size: 12px;
        }}
        
        /* Article Cards */
        .article-card {{
            background: white;
            border-radius: 8px;
            padding: 12px;
            margin-bottom: 10px;
            cursor: grab;
            transition: all 0.3s;
            border: 2px solid transparent;
            position: relative;
        }}
        
        .article-card:hover {{
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            transform: translateY(-2px);
        }}
        
        .article-card.dragging {{
            opacity: 0.5;
            cursor: grabbing;
            transform: rotate(2deg);
        }}
        
        .article-header {{
            display: flex;
            align-items: center;
            gap: 8px;
            margin-bottom: 8px;
        }}
        
        .domain-icon {{
            font-size: 20px;
        }}
        
        .article-title {{
            font-weight: 600;
            font-size: 14px;
            color: #1a1a1a;
            flex: 1;
            overflow: hidden;
            text-overflow: ellipsis;
            display: -webkit-box;
            -webkit-line-clamp: 2;
            -webkit-box-orient: vertical;
        }}
        
        .article-meta {{
            display: flex;
            gap: 5px;
            flex-wrap: wrap;
            margin-top: 8px;
        }}
        
        .meta-badge {{
            padding: 2px 8px;
            border-radius: 12px;
            font-size: 11px;
            font-weight: 500;
        }}
        
        .priority-high {{ background: #fee2e2; color: #dc2626; }}
        .priority-medium {{ background: #fef3c7; color: #d97706; }}
        .priority-low {{ background: #dbeafe; color: #2563eb; }}
        
        .quantum-score {{
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: white;
        }}
        
        /* Action Buttons */
        .article-actions {{
            display: flex;
            gap: 5px;
            margin-top: 10px;
        }}
        
        .action-btn {{
            background: #f3f4f6;
            border: none;
            padding: 6px 10px;
            border-radius: 6px;
            cursor: pointer;
            font-size: 14px;
            transition: all 0.2s;
            display: flex;
            align-items: center;
            gap: 5px;
        }}
        
        .action-btn:hover {{
            background: #e5e7eb;
            transform: scale(1.05);
        }}
        
        .action-btn.copy.copied {{
            background: #10b981;
            color: white;
        }}
        
        .action-btn.line {{
            background: #00B900;
            color: white;
        }}
        
        /* Calendar View */
        .calendar-container {{
            background: rgba(255, 255, 255, 0.98);
            border-radius: 12px;
            padding: 20px;
            box-shadow: 0 8px 32px rgba(31, 38, 135, 0.15);
        }}
        
        .calendar-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
            padding-bottom: 15px;
            border-bottom: 2px solid #f0f0f0;
        }}
        
        .calendar-grid {{
            display: grid;
            grid-template-columns: 80px repeat(7, 1fr);
            gap: 1px;
            background: #e5e7eb;
            border: 1px solid #e5e7eb;
            border-radius: 8px;
            overflow: hidden;
        }}
        
        .calendar-cell {{
            background: white;
            min-height: 50px;
            padding: 8px;
            position: relative;
        }}
        
        .calendar-cell.time-label {{
            background: #f9fafb;
            font-size: 12px;
            font-weight: 500;
            color: #6b7280;
            display: flex;
            align-items: center;
            justify-content: center;
        }}
        
        .calendar-cell.day-header {{
            background: #f3f4f6;
            font-weight: 600;
            text-align: center;
            padding: 12px;
        }}
        
        .calendar-cell.droppable {{
            transition: background 0.2s;
        }}
        
        .calendar-cell.drag-over {{
            background: #ede9fe;
            border: 2px dashed #8b5cf6;
        }}
        
        .scheduled-article {{
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: white;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 11px;
            margin-bottom: 4px;
            cursor: move;
        }}
        
        /* AI Features Panel */
        .ai-panel {{
            background: rgba(255, 255, 255, 0.98);
            border-radius: 12px;
            padding: 20px;
            margin-top: 20px;
            box-shadow: 0 8px 32px rgba(31, 38, 135, 0.15);
        }}
        
        .feature-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 10px;
            margin-top: 15px;
        }}
        
        .feature-btn {{
            padding: 12px 20px;
            border: none;
            border-radius: 8px;
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: white;
            cursor: pointer;
            font-weight: 500;
            transition: all 0.3s;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 8px;
        }}
        
        .feature-btn:hover {{
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
        }}
        
        /* Add Article Form */
        .add-article-form {{
            display: flex;
            gap: 10px;
            margin-bottom: 20px;
            padding: 15px;
            background: #f9fafb;
            border-radius: 8px;
        }}
        
        .url-input {{
            flex: 1;
            padding: 10px 15px;
            border: 2px solid #e5e7eb;
            border-radius: 8px;
            font-size: 14px;
            transition: border-color 0.3s;
        }}
        
        .url-input:focus {{
            outline: none;
            border-color: #667eea;
        }}
        
        .add-btn {{
            padding: 10px 20px;
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: white;
            border: none;
            border-radius: 8px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s;
        }}
        
        .add-btn:hover {{
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
        }}
        
        /* Mobile Responsive */
        @media (max-width: 1024px) {{
            .main-layout {{
                grid-template-columns: 1fr;
            }}
            
            .kanban-board {{
                grid-template-columns: repeat(2, 1fr);
            }}
            
            .stats-container {{
                grid-template-columns: repeat(2, 1fr);
            }}
        }}
        
        @media (max-width: 640px) {{
            .container {{
                padding: 5px;
            }}
            
            .kanban-board {{
                grid-template-columns: 1fr;
            }}
            
            .calendar-grid {{
                grid-template-columns: 60px repeat(7, 1fr);
                font-size: 12px;
            }}
            
            .feature-grid {{
                grid-template-columns: 1fr;
            }}
            
            .header {{
                flex-direction: column;
                text-align: center;
            }}
        }}
        
        /* Toast Notifications */
        .toast {{
            position: fixed;
            bottom: 20px;
            right: 20px;
            background: #10b981;
            color: white;
            padding: 12px 20px;
            border-radius: 8px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            display: none;
            animation: slideIn 0.3s ease;
            z-index: 1000;
        }}
        
        @keyframes slideIn {{
            from {{
                transform: translateY(100%);
                opacity: 0;
            }}
            to {{
                transform: translateY(0);
                opacity: 1;
            }}
        }}
        
        /* Loading Spinner */
        .spinner {{
            border: 3px solid #f3f3f3;
            border-top: 3px solid #667eea;
            border-radius: 50%;
            width: 40px;
            height: 40px;
            animation: spin 1s linear infinite;
            margin: 20px auto;
        }}
        
        @keyframes spin {{
            0% {{ transform: rotate(0deg); }}
            100% {{ transform: rotate(360deg); }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <!-- Header -->
        <div class="header">
            <div class="logo">
                🧠 Ultimate Article Intelligence Hub
            </div>
            <div class="line-status" id="lineStatus">
                <span>⚪</span>
                <span id="lineStatusText">Connecting to LINE...</span>
            </div>
        </div>
        
        <!-- Stats -->
        <div class="stats-container">
            <div class="stat-card">
                <div class="stat-number" id="totalArticles">0</div>
                <div class="stat-label">Total Articles</div>
            </div>
            <div class="stat-card">
                <div class="stat-number" id="avgScore">0</div>
                <div class="stat-label">Avg Quantum Score</div>
            </div>
            <div class="stat-card">
                <div class="stat-number" id="completionRate">0%</div>
                <div class="stat-label">Completion Rate</div>
            </div>
            <div class="stat-card">
                <div class="stat-number" id="weeklyArticles">0</div>
                <div class="stat-label">This Week</div>
            </div>
        </div>
        
        <!-- Add Article Form -->
        <div class="add-article-form">
            <input type="url" 
                   class="url-input" 
                   id="urlInput" 
                   placeholder="Paste article URL here..."
                   onkeypress="if(event.key==='Enter') addArticle()">
            <button class="add-btn" onclick="addArticle()">
                ➕ Add Article
            </button>
            <button class="add-btn" onclick="sendToLine()" style="background: #00B900;">
                📱 Send to LINE
            </button>
        </div>
        
        <!-- Main Layout -->
        <div class="main-layout">
            <!-- Kanban Board -->
            <div class="kanban-container">
                <div class="kanban-header">
                    <h2>📋 Kanban Board</h2>
                    <span>Drag articles to change status</span>
                </div>
                <div class="kanban-board" id="kanbanBoard">
                    <div class="kanban-column inbox" data-stage="inbox">
                        <div class="column-header">
                            <span>📥 Inbox</span>
                            <span class="column-count">0</span>
                        </div>
                        <div class="column-items"></div>
                    </div>
                    <div class="kanban-column reading" data-stage="reading">
                        <div class="column-header">
                            <span>📖 Reading</span>
                            <span class="column-count">0</span>
                        </div>
                        <div class="column-items"></div>
                    </div>
                    <div class="kanban-column reviewing" data-stage="reviewing">
                        <div class="column-header">
                            <span>🔍 Reviewing</span>
                            <span class="column-count">0</span>
                        </div>
                        <div class="column-items"></div>
                    </div>
                    <div class="kanban-column completed" data-stage="completed">
                        <div class="column-header">
                            <span>✅ Completed</span>
                            <span class="column-count">0</span>
                        </div>
                        <div class="column-items"></div>
                    </div>
                </div>
            </div>
            
            <!-- Calendar View -->
            <div class="calendar-container">
                <div class="calendar-header">
                    <h2>📅 Reading Schedule</h2>
                    <div>
                        <button class="action-btn" onclick="previousWeek()">◀</button>
                        <span id="weekRange">This Week</span>
                        <button class="action-btn" onclick="nextWeek()">▶</button>
                    </div>
                </div>
                <div class="calendar-grid" id="calendarGrid">
                    <!-- Calendar will be generated here -->
                </div>
            </div>
        </div>
        
        <!-- AI Features Panel -->
        <div class="ai-panel">
            <h2>🤖 AI Intelligence Features</h2>
            <div class="feature-grid">
                <button class="feature-btn" onclick="showFeature('priority')">
                    🎯 Priority Ranking
                </button>
                <button class="feature-btn" onclick="showFeature('notes')">
                    📝 Study Notes
                </button>
                <button class="feature-btn" onclick="showFeature('recommendations')">
                    💡 Smart Recommendations
                </button>
                <button class="feature-btn" onclick="showFeature('digest')">
                    📊 Daily Digest
                </button>
                <button class="feature-btn" onclick="showFeature('insights')">
                    🔮 Speed Insights
                </button>
                <button class="feature-btn" onclick="showFeature('refresh')">
                    🔄 Refresh
                </button>
                <button class="feature-btn" onclick="showFeature('export')">
                    📤 Export Notes
                </button>
                <button class="feature-btn" onclick="showFeature('category')">
                    🏷️ Category Analysis
                </button>
            </div>
        </div>
    </div>
    
    <!-- Toast Notification -->
    <div class="toast" id="toast"></div>
    
    <script>
        // LIFF Configuration
        const liffId = '2007552096-GxP76rNd';
        let liffInitialized = false;
        let userProfile = null;
        
        // Initialize LIFF
        async function initializeLiff() {{
            try {{
                await liff.init({{ liffId: liffId }});
                liffInitialized = true;
                
                if (liff.isLoggedIn()) {{
                    userProfile = await liff.getProfile();
                    updateLineStatus(true);
                    
                    // Get user's LINE ID for personalized features
                    console.log('LINE User:', userProfile);
                }} else {{
                    // Optionally prompt login
                    // liff.login();
                    updateLineStatus(false);
                }}
            }} catch (error) {{
                console.error('LIFF initialization failed:', error);
                updateLineStatus(false);
            }}
        }}
        
        function updateLineStatus(connected) {{
            const status = document.getElementById('lineStatus');
            const statusText = document.getElementById('lineStatusText');
            
            if (connected) {{
                status.className = 'line-status';
                statusText.textContent = userProfile ? `Connected as ${{userProfile.displayName}}` : 'Connected to LINE';
                status.innerHTML = '<span>🟢</span>' + statusText.outerHTML;
            }} else {{
                status.className = 'line-status disconnected';
                statusText.textContent = 'LINE not connected';
                status.innerHTML = '<span>⚪</span>' + statusText.outerHTML;
            }}
        }}
        
        // Send article to LINE
        async function sendToLine() {{
            const urlInput = document.getElementById('urlInput');
            const url = urlInput.value.trim();
            
            if (!url) {{
                showToast('Please enter a URL first', 'error');
                return;
            }}
            
            if (liffInitialized && liff.isLoggedIn()) {{
                try {{
                    await liff.sendMessages([
                        {{
                            type: 'text',
                            text: `📚 New article saved: ${{url}}`
                        }}
                    ]);
                    showToast('Sent to LINE chat!', 'success');
                }} catch (error) {{
                    console.error('Failed to send message:', error);
                    showToast('Failed to send to LINE', 'error');
                }}
            }} else {{
                // Fallback to server-side LINE API
                fetch('/api/line/send', {{
                    method: 'POST',
                    headers: {{ 'Content-Type': 'application/json' }},
                    body: JSON.stringify({{ url: url }})
                }})
                .then(response => response.json())
                .then(data => {{
                    if (data.success) {{
                        showToast('Article sent to LINE!', 'success');
                    }}
                }});
            }}
        }}
        
        // Global variables
        let articles = [];
        let draggedElement = null;
        let currentWeekOffset = 0;
        let calendarSchedule = {{}};
        
        // Load saved schedule from localStorage
        if (localStorage.getItem('calendarSchedule')) {{
            calendarSchedule = JSON.parse(localStorage.getItem('calendarSchedule'));
        }}
        
        // Initialize on page load
        document.addEventListener('DOMContentLoaded', function() {{
            // Register service worker for PWA
            if ('serviceWorker' in navigator) {{
                navigator.serviceWorker.register('/service-worker.js')
                    .then(registration => {{
                        console.log('Service Worker registered:', registration.scope);
                        
                        // Check for updates
                        registration.addEventListener('updatefound', () => {{
                            const newWorker = registration.installing;
                            newWorker.addEventListener('statechange', () => {{
                                if (newWorker.state === 'installed' && navigator.serviceWorker.controller) {{
                                    showToast('New version available! Refresh to update.', 'info');
                                }}
                            }});
                        }});
                    }})
                    .catch(error => {{
                        console.error('Service Worker registration failed:', error);
                    }});
                    
                // Listen for app install prompt
                let deferredPrompt;
                window.addEventListener('beforeinstallprompt', (e) => {{
                    e.preventDefault();
                    deferredPrompt = e;
                    
                    // Show install button
                    const installBtn = document.createElement('button');
                    installBtn.className = 'add-btn';
                    installBtn.innerHTML = '📲 Install App';
                    installBtn.style.background = '#10b981';
                    installBtn.onclick = async () => {{
                        if (deferredPrompt) {{
                            deferredPrompt.prompt();
                            const {{ outcome }} = await deferredPrompt.userChoice;
                            if (outcome === 'accepted') {{
                                showToast('App installed successfully!', 'success');
                            }}
                            deferredPrompt = null;
                            installBtn.remove();
                        }}
                    }};
                    
                    // Add install button to header
                    const header = document.querySelector('.header');
                    if (header && !document.querySelector('#installBtn')) {{
                        installBtn.id = 'installBtn';
                        header.appendChild(installBtn);
                    }}
                }});
                
                // Handle app installed event
                window.addEventListener('appinstalled', () => {{
                    showToast('Article Hub installed successfully!', 'success');
                    const installBtn = document.querySelector('#installBtn');
                    if (installBtn) installBtn.remove();
                }});
            }}
            
            // Initialize LIFF
            initializeLiff();
            loadArticles();
            renderCalendar();
            updateStats();
            
            // Setup auto-refresh
            setInterval(loadArticles, 30000); // Refresh every 30 seconds
            
            // Enable offline data sync
            if ('sync' in self.registration) {{
                self.registration.sync.register('sync-articles');
            }}
            
            // Request notification permission
            if ('Notification' in window && Notification.permission === 'default') {{
                Notification.requestPermission();
            }}
        }});
        
        // Load articles from API
        async function loadArticles() {{
            try {{
                const response = await fetch('/api/articles');
                const data = await response.json();
                articles = data.articles || [];
                renderKanban();
                updateStats();
            }} catch (error) {{
                console.error('Error loading articles:', error);
                showToast('Failed to load articles', 'error');
            }}
        }}
        
        // Render Kanban board
        function renderKanban() {{
            const stages = ['inbox', 'reading', 'reviewing', 'completed'];
            
            stages.forEach(stage => {{
                const column = document.querySelector(`.kanban-column.${{stage}} .column-items`);
                const countBadge = document.querySelector(`.kanban-column.${{stage}} .column-count`);
                
                if (!column) return;
                
                column.innerHTML = '';
                const stageArticles = articles.filter(a => a.stage === stage);
                countBadge.textContent = stageArticles.length;
                
                stageArticles.forEach(article => {{
                    const card = createArticleCard(article);
                    column.appendChild(card);
                }});
            }});
            
            setupDragAndDrop();
        }}
        
        // Create article card element
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
                    <button class="action-btn copy" onclick="copyToClipboard('${{escapeHtml(article.url)}}', this)">
                        📋 Copy
                    </button>
                    <button class="action-btn" onclick="window.open('${{escapeHtml(article.url)}}', '_blank')">
                        🔗 Open
                    </button>
                    <button class="action-btn line" onclick="shareToLine('${{escapeHtml(article.url)}}')">
                        📱 LINE
                    </button>
                </div>
            `;
            
            return card;
        }}
        
        // Get domain icon
        function getDomainIcon(url) {{
            const urlLower = url.toLowerCase();
            if (urlLower.includes('github.com')) return '🐙';
            if (urlLower.includes('facebook.com')) return '📘';
            if (urlLower.includes('twitter.com') || urlLower.includes('x.com')) return '🐦';
            if (urlLower.includes('youtube.com')) return '📺';
            if (urlLower.includes('medium.com')) return '📰';
            if (urlLower.includes('stackoverflow.com')) return '💡';
            if (urlLower.includes('reddit.com')) return '🤖';
            if (urlLower.includes('linkedin.com')) return '💼';
            if (urlLower.includes('google.com')) return '🔍';
            if (urlLower.includes('amazon.com')) return '📦';
            if (urlLower.includes('wikipedia.org')) return '📚';
            if (urlLower.includes('line.me')) return '💚';
            return '🌐';
        }}
        
        // Setup drag and drop
        function setupDragAndDrop() {{
            const cards = document.querySelectorAll('.article-card');
            const columns = document.querySelectorAll('.kanban-column');
            const calendarCells = document.querySelectorAll('.calendar-cell.droppable');
            
            cards.forEach(card => {{
                card.addEventListener('dragstart', handleDragStart);
                card.addEventListener('dragend', handleDragEnd);
            }});
            
            columns.forEach(column => {{
                column.addEventListener('dragover', handleDragOver);
                column.addEventListener('drop', handleDrop);
                column.addEventListener('dragleave', handleDragLeave);
                column.addEventListener('dragenter', handleDragEnter);
            }});
            
            calendarCells.forEach(cell => {{
                cell.addEventListener('dragover', handleCalendarDragOver);
                cell.addEventListener('drop', handleCalendarDrop);
                cell.addEventListener('dragleave', handleCalendarDragLeave);
            }});
        }}
        
        function handleDragStart(e) {{
            draggedElement = e.target;
            e.target.classList.add('dragging');
            e.dataTransfer.effectAllowed = 'move';
        }}
        
        function handleDragEnd(e) {{
            e.target.classList.remove('dragging');
            draggedElement = null;
        }}
        
        function handleDragOver(e) {{
            if (e.preventDefault) {{
                e.preventDefault();
            }}
            e.dataTransfer.dropEffect = 'move';
            return false;
        }}
        
        function handleDragEnter(e) {{
            if (e.target.classList.contains('kanban-column')) {{
                e.target.style.background = '#f0f0f0';
            }}
        }}
        
        function handleDragLeave(e) {{
            if (e.target.classList.contains('kanban-column')) {{
                e.target.style.background = '';
            }}
        }}
        
        function handleDrop(e) {{
            if (e.stopPropagation) {{
                e.stopPropagation();
            }}
            
            const column = e.target.closest('.kanban-column');
            if (column && draggedElement) {{
                const newStage = column.dataset.stage;
                const articleId = draggedElement.dataset.articleId;
                
                updateArticleStage(articleId, newStage);
                column.style.background = '';
            }}
            
            return false;
        }}
        
        function handleCalendarDragOver(e) {{
            e.preventDefault();
            e.target.classList.add('drag-over');
        }}
        
        function handleCalendarDragLeave(e) {{
            e.target.classList.remove('drag-over');
        }}
        
        function handleCalendarDrop(e) {{
            e.preventDefault();
            e.target.classList.remove('drag-over');
            
            if (draggedElement && e.target.classList.contains('droppable')) {{
                const articleId = draggedElement.dataset.articleId;
                const timeSlot = e.target.dataset.time;
                const day = e.target.dataset.day;
                
                scheduleArticle(articleId, day, timeSlot);
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
                    showToast('Article moved!', 'success');
                }}
            }} catch (error) {{
                console.error('Error updating article:', error);
                showToast('Failed to update article', 'error');
            }}
        }}
        
        // Schedule article in calendar
        function scheduleArticle(articleId, day, timeSlot) {{
            const key = `${{day}}_${{timeSlot}}`;
            calendarSchedule[key] = articleId;
            localStorage.setItem('calendarSchedule', JSON.stringify(calendarSchedule));
            renderCalendar();
            showToast('Article scheduled!', 'success');
        }}
        
        // Render calendar
        function renderCalendar() {{
            const grid = document.getElementById('calendarGrid');
            grid.innerHTML = '';
            
            const days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];
            const timeSlots = ['6:00', '7:00', '8:00', '9:00', '10:00', '11:00', '12:00', 
                             '13:00', '14:00', '15:00', '16:00', '17:00', '18:00', '19:00', '20:00', '21:00'];
            
            // Empty top-left cell
            const emptyCell = document.createElement('div');
            emptyCell.className = 'calendar-cell time-label';
            grid.appendChild(emptyCell);
            
            // Day headers
            days.forEach(day => {{
                const dayHeader = document.createElement('div');
                dayHeader.className = 'calendar-cell day-header';
                dayHeader.textContent = day;
                grid.appendChild(dayHeader);
            }});
            
            // Time slots and cells
            timeSlots.forEach(time => {{
                // Time label
                const timeLabel = document.createElement('div');
                timeLabel.className = 'calendar-cell time-label';
                timeLabel.textContent = time;
                grid.appendChild(timeLabel);
                
                // Day cells
                days.forEach(day => {{
                    const cell = document.createElement('div');
                    cell.className = 'calendar-cell droppable';
                    cell.dataset.time = time;
                    cell.dataset.day = day;
                    
                    // Check if there's a scheduled article
                    const key = `${{day}}_${{time}}`;
                    if (calendarSchedule[key]) {{
                        const article = articles.find(a => a.id == calendarSchedule[key]);
                        if (article) {{
                            const scheduled = document.createElement('div');
                            scheduled.className = 'scheduled-article';
                            scheduled.textContent = article.title ? article.title.substring(0, 20) + '...' : 'Article';
                            scheduled.draggable = true;
                            cell.appendChild(scheduled);
                        }}
                    }}
                    
                    grid.appendChild(cell);
                }});
            }});
        }}
        
        // Add new article
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
                    showToast('Article added successfully!', 'success');
                }} else {{
                    showToast('Failed to add article', 'error');
                }}
            }} catch (error) {{
                console.error('Error adding article:', error);
                showToast('Failed to add article', 'error');
            }}
        }}
        
        // Copy to clipboard
        function copyToClipboard(text, button) {{
            navigator.clipboard.writeText(text).then(() => {{
                const originalText = button.innerHTML;
                button.innerHTML = '✅ Copied!';
                button.classList.add('copied');
                
                setTimeout(() => {{
                    button.innerHTML = originalText;
                    button.classList.remove('copied');
                }}, 2000);
            }});
        }}
        
        // Share to LINE
        function shareToLine(url) {{
            if (liffInitialized && liff.isLoggedIn()) {{
                liff.shareTargetPicker([
                    {{
                        type: 'text',
                        text: `Check out this article: ${{url}}`
                    }}
                ]).then(() => {{
                    showToast('Shared to LINE!', 'success');
                }}).catch((error) => {{
                    console.error('Error sharing:', error);
                    showToast('Failed to share', 'error');
                }});
            }} else {{
                showToast('Please connect to LINE first', 'error');
            }}
        }}
        
        // Update statistics
        function updateStats() {{
            document.getElementById('totalArticles').textContent = articles.length;
            
            const avgScore = articles.length > 0 
                ? Math.round(articles.reduce((sum, a) => sum + (a.quantum_score || 0), 0) / articles.length)
                : 0;
            document.getElementById('avgScore').textContent = avgScore;
            
            const completed = articles.filter(a => a.stage === 'completed').length;
            const completionRate = articles.length > 0 
                ? Math.round((completed / articles.length) * 100)
                : 0;
            document.getElementById('completionRate').textContent = completionRate + '%';
            
            const weekAgo = new Date();
            weekAgo.setDate(weekAgo.getDate() - 7);
            const weeklyCount = articles.filter(a => {{
                const createdDate = new Date(a.created_at || 0);
                return createdDate > weekAgo;
            }}).length;
            document.getElementById('weeklyArticles').textContent = weeklyCount;
        }}
        
        // Show AI features
        function showFeature(feature) {{
            switch(feature) {{
                case 'priority':
                    showPriorityRanking();
                    break;
                case 'notes':
                    generateStudyNotes();
                    break;
                case 'recommendations':
                    showRecommendations();
                    break;
                case 'digest':
                    generateDailyDigest();
                    break;
                case 'insights':
                    showSpeedInsights();
                    break;
                case 'refresh':
                    loadArticles();
                    showToast('Articles refreshed!', 'success');
                    break;
                case 'export':
                    exportNotes();
                    break;
                case 'category':
                    analyzCategories();
                    break;
            }}
        }}
        
        function showPriorityRanking() {{
            const sorted = [...articles].sort((a, b) => (b.quantum_score || 0) - (a.quantum_score || 0));
            let ranking = 'Top Priority Articles:\\n\\n';
            sorted.slice(0, 5).forEach((article, index) => {{
                ranking += `${{index + 1}}. ${{article.title || 'Untitled'}} (Score: ${{article.quantum_score || 0}})\\n`;
            }});
            alert(ranking);
        }}
        
        function generateStudyNotes() {{
            const readingArticles = articles.filter(a => a.stage === 'reading');
            if (readingArticles.length === 0) {{
                showToast('No articles in reading stage', 'info');
                return;
            }}
            
            let notes = 'Study Notes for Current Reading:\\n\\n';
            readingArticles.forEach(article => {{
                notes += `📖 ${{article.title || 'Untitled'}}\\n`;
                notes += `   Priority: ${{article.priority || 'medium'}}\\n`;
                notes += `   Key Points: Focus on main concepts\\n\\n`;
            }});
            alert(notes);
        }}
        
        function showRecommendations() {{
            showToast('Analyzing your reading patterns...', 'info');
            setTimeout(() => {{
                alert('Recommended Articles:\\n\\n1. Focus on high-priority items first\\n2. Complete articles in reading stage\\n3. Review completed articles weekly');
            }}, 1000);
        }}
        
        function generateDailyDigest() {{
            const today = new Date().toDateString();
            const digest = `Daily Digest for ${{today}}\\n\\n` +
                         `Total Articles: ${{articles.length}}\\n` +
                         `Completed Today: ${{articles.filter(a => a.stage === 'completed').length}}\\n` +
                         `In Progress: ${{articles.filter(a => a.stage === 'reading').length}}\\n\\n` +
                         `Keep up the great work! 🎉`;
            alert(digest);
        }}
        
        function showSpeedInsights() {{
            const avgReadingTime = 15; // minutes
            const totalTime = articles.filter(a => a.stage === 'completed').length * avgReadingTime;
            alert(`Reading Speed Insights:\\n\\nAverage time per article: ${{avgReadingTime}} min\\nTotal reading time: ${{totalTime}} min\\nSuggestion: Try speed reading techniques!`);
        }}
        
        function exportNotes() {{
            const notes = articles.map(a => `${{a.title || 'Untitled'}}: ${{a.url}}`).join('\\n');
            const blob = new Blob([notes], {{ type: 'text/plain' }});
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'articles_export.txt';
            a.click();
            showToast('Notes exported!', 'success');
        }}
        
        function analyzCategories() {{
            const categories = {{}};
            articles.forEach(a => {{
                const cat = a.category || 'Uncategorized';
                categories[cat] = (categories[cat] || 0) + 1;
            }});
            
            let analysis = 'Category Analysis:\\n\\n';
            Object.entries(categories).forEach(([cat, count]) => {{
                analysis += `${{cat}}: ${{count}} articles\\n`;
            }});
            alert(analysis);
        }}
        
        // Utility functions
        function escapeHtml(text) {{
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        }}
        
        function showToast(message, type = 'success') {{
            const toast = document.getElementById('toast');
            toast.textContent = message;
            toast.style.background = type === 'error' ? '#ef4444' : type === 'info' ? '#3b82f6' : '#10b981';
            toast.style.display = 'block';
            
            setTimeout(() => {{
                toast.style.display = 'none';
            }}, 3000);
        }}
        
        // Calendar navigation
        function previousWeek() {{
            currentWeekOffset--;
            updateWeekDisplay();
        }}
        
        function nextWeek() {{
            currentWeekOffset++;
            updateWeekDisplay();
        }}
        
        function updateWeekDisplay() {{
            const weekRange = document.getElementById('weekRange');
            if (currentWeekOffset === 0) {{
                weekRange.textContent = 'This Week';
            }} else if (currentWeekOffset === 1) {{
                weekRange.textContent = 'Next Week';
            }} else if (currentWeekOffset === -1) {{
                weekRange.textContent = 'Last Week';
            }} else {{
                weekRange.textContent = `Week ${{currentWeekOffset > 0 ? '+' : ''}}${{currentWeekOffset}}`;
            }}
        }}
    </script>
</body>
</html>'''
        
        self.send_response(200)
        self.send_header('Content-Type', 'text/html')
        self.end_headers()
        self.wfile.write(html.encode())
    
    def serve_liff_page(self):
        """Serve LIFF-specific mobile page"""
        html = '''<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Article Hub - LINE</title>
    <script src="https://static.line-scdn.net/liff/edge/2/sdk.js"></script>
    <style>
        body {
            margin: 0;
            padding: 20px;
            font-family: -apple-system, BlinkMacSystemFont, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }
        
        .mobile-container {
            max-width: 100%;
            background: white;
            border-radius: 12px;
            padding: 20px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.1);
        }
        
        .article-list {
            display: flex;
            flex-direction: column;
            gap: 10px;
        }
        
        .article-item {
            padding: 15px;
            background: #f8f9fa;
            border-radius: 8px;
            border-left: 3px solid #667eea;
        }
        
        .article-title {
            font-weight: 600;
            margin-bottom: 5px;
        }
        
        .article-actions {
            display: flex;
            gap: 10px;
            margin-top: 10px;
        }
        
        .btn {
            padding: 8px 15px;
            border: none;
            border-radius: 6px;
            background: #667eea;
            color: white;
            font-size: 14px;
            cursor: pointer;
        }
    </style>
</head>
<body>
    <div class="mobile-container">
        <h2>📚 Your Articles</h2>
        <div class="article-list" id="articleList">
            Loading...
        </div>
    </div>
    
    <script>
        // Initialize LIFF
        liff.init({ liffId: '{LIFF_ID}' })
            .then(() => {
                if (!liff.isLoggedIn()) {
                    liff.login();
                } else {
                    loadArticles();
                }
            });
        
        async function loadArticles() {
            const response = await fetch('/api/articles');
            const data = await response.json();
            const articles = data.articles || [];
            
            const list = document.getElementById('articleList');
            list.innerHTML = '';
            
            articles.forEach(article => {
                const item = document.createElement('div');
                item.className = 'article-item';
                item.innerHTML = `
                    <div class="article-title">${article.title || 'Untitled'}</div>
                    <div>Stage: ${article.stage}</div>
                    <div class="article-actions">
                        <button class="btn" onclick="shareArticle('${article.url}')">Share</button>
                        <button class="btn" onclick="openArticle('${article.url}')">Open</button>
                    </div>
                `;
                list.appendChild(item);
            });
        }
        
        function shareArticle(url) {
            liff.shareTargetPicker([{
                type: 'text',
                text: 'Check out this article: ' + url
            }]);
        }
        
        function openArticle(url) {
            liff.openWindow({ url: url, external: true });
        }
    </script>
</body>
</html>'''
        
        self.send_response(200)
        self.send_header('Content-Type', 'text/html')
        self.end_headers()
        self.wfile.write(html.replace('{LIFF_ID}', LIFF_ID).encode())
    
    def serve_articles(self):
        """Serve articles JSON API"""
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM articles_kanban 
            WHERE is_archived = 0 
            ORDER BY created_at DESC
        ''')
        
        articles = []
        for row in cursor.fetchall():
            article = dict(row)
            # Clean title to prevent JavaScript errors
            if article.get('title'):
                article['title'] = ' '.join(str(article['title']).split())
            articles.append(article)
        
        conn.close()
        
        response = json.dumps({'articles': articles})
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(response.encode())
    
    def serve_analytics(self):
        """Serve analytics data"""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Get various analytics
        cursor.execute('SELECT COUNT(*) FROM articles_kanban WHERE is_archived = 0')
        total = cursor.fetchone()[0]
        
        cursor.execute('SELECT stage, COUNT(*) FROM articles_kanban WHERE is_archived = 0 GROUP BY stage')
        stages = dict(cursor.fetchall())
        
        cursor.execute('SELECT AVG(quantum_score) FROM articles_kanban WHERE is_archived = 0')
        avg_score = cursor.fetchone()[0] or 0
        
        conn.close()
        
        analytics = {
            'total_articles': total,
            'stages': stages,
            'avg_quantum_score': round(avg_score),
            'completion_rate': round((stages.get('completed', 0) / max(total, 1)) * 100)
        }
        
        response = json.dumps(analytics)
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
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
            
            # Extract metadata from URL
            title = self.extract_title_from_url(url)
            category = self.detect_category(url)
            quantum_score = self.calculate_quantum_score(url, title)
            
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
        """Handle updating article stage"""
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
    
    def handle_schedule_article(self, post_data):
        """Handle scheduling article in calendar"""
        try:
            data = json.loads(post_data)
            # Store in database or send to LINE
            
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'success': True}).encode())
            
        except Exception as e:
            logging.error(f'Error scheduling article: {e}')
            self.send_error(500, str(e))
    
    def handle_line_webhook(self, post_data):
        """Handle LINE webhook events (messages from users)"""
        try:
            # Parse LINE webhook event
            events = json.loads(post_data)
            logging.info(f"LINE Webhook received: {events}")
            
            for event in events.get('events', []):
                if event['type'] == 'message' and event['message']['type'] == 'text':
                    user_id = event['source'].get('userId')
                    reply_token = event['replyToken']
                    message_text = event['message']['text']
                    
                    # Check if message contains a URL
                    import re
                    url_pattern = r'https?://[^\s]+'
                    urls = re.findall(url_pattern, message_text)
                    
                    if urls:
                        # Send loading animation first
                        self.send_loading_animation(user_id, 5)
                        
                        # Save each URL as an article
                        saved_articles = []
                        for url in urls:
                            article_id = self.save_article_from_line(url, user_id)
                            if article_id:
                                saved_articles.append({'url': url, 'id': article_id})
                        
                        # Send flex message with saved articles
                        self.send_flex_article_saved(reply_token, saved_articles)
                    else:
                        # Send loading animation for commands
                        self.send_loading_animation(user_id, 3)
                        
                        # Handle commands or provide help
                        if message_text.lower() in ['/help', 'help', '?']:
                            self.send_help_flex_message(reply_token)
                        elif message_text.lower() == '/list':
                            articles = self.get_recent_articles(5)
                            self.send_article_list_flex(reply_token, articles)
                        elif message_text.lower() == '/stats':
                            stats = self.get_user_stats()
                            self.send_stats_flex_message(reply_token, stats)
                        elif message_text.lower() == '/web':
                            self.send_web_access_flex(reply_token)
                        else:
                            self.send_quick_reply_suggestions(reply_token)
            
            # Return 200 OK to LINE
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'success': True}).encode())
            
        except Exception as e:
            logging.error(f'Error handling LINE webhook: {e}')
            # Still return 200 to avoid LINE retrying
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'success': False}).encode())
    
    def save_article_from_line(self, url, user_id):
        """Save article from LINE message"""
        try:
            title = self.extract_title_from_url(url)
            category = self.detect_category(url)
            quantum_score = self.calculate_quantum_score(url, title)
            
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
            
            article_id = cursor.lastrowid
            conn.commit()
            conn.close()
            
            logging.info(f"Article saved from LINE user {user_id}: {url}")
            return article_id
            
        except Exception as e:
            logging.error(f"Error saving article from LINE: {e}")
            return None
    
    def send_loading_animation(self, user_id, duration_seconds=5):
        """Send loading animation to user"""
        try:
            token = LINE_CHANNEL_ACCESS_TOKEN or os.getenv('LINE_CHANNEL_ACCESS_TOKEN', '')
            if not token:
                return
            
            import urllib.request
            url = 'https://api.line.me/v2/bot/chat/loading/start'
            headers = {
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {token}'
            }
            
            data = {
                'chatId': user_id,
                'loadingSeconds': duration_seconds
            }
            
            req = urllib.request.Request(
                url,
                data=json.dumps(data).encode('utf-8'),
                headers=headers,
                method='POST'
            )
            
            with urllib.request.urlopen(req) as response:
                logging.info(f"Loading animation sent: {response.status}")
                
        except Exception as e:
            logging.error(f"Error sending loading animation: {e}")
    
    def send_flex_article_saved(self, reply_token, saved_articles):
        """Send flex message for saved articles"""
        try:
            token = LINE_CHANNEL_ACCESS_TOKEN or os.getenv('LINE_CHANNEL_ACCESS_TOKEN', '')
            if not token:
                return
            
            import urllib.request
            
            # Create flex message
            flex_message = {
                "type": "flex",
                "altText": f"✅ Saved {len(saved_articles)} article(s)",
                "contents": {
                    "type": "bubble",
                    "hero": {
                        "type": "box",
                        "layout": "vertical",
                        "contents": [
                            {
                                "type": "text",
                                "text": "✅ Articles Saved!",
                                "weight": "bold",
                                "size": "xl",
                                "color": "#FFFFFF",
                                "align": "center"
                            },
                            {
                                "type": "text",
                                "text": f"{len(saved_articles)} new article(s) added",
                                "size": "sm",
                                "color": "#FFFFFF",
                                "align": "center",
                                "margin": "md"
                            }
                        ],
                        "backgroundColor": "#667eea",
                        "paddingAll": "20px"
                    },
                    "body": {
                        "type": "box",
                        "layout": "vertical",
                        "contents": [
                            {
                                "type": "text",
                                "text": "What would you like to do?",
                                "wrap": True,
                                "margin": "lg"
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
                                "style": "secondary",
                                "action": {
                                    "type": "message",
                                    "label": "📖 View My Articles",
                                    "text": "/list"
                                }
                            },
                            {
                                "type": "button",
                                "style": "secondary",
                                "action": {
                                    "type": "message",
                                    "label": "📊 Check Stats",
                                    "text": "/stats"
                                }
                            }
                        ]
                    }
                },
                "quickReply": {
                    "items": [
                        {
                            "type": "action",
                            "action": {
                                "type": "message",
                                "label": "📱 Share LIFF",
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
                        },
                        {
                            "type": "action",
                            "action": {
                                "type": "message",
                                "label": "📋 List",
                                "text": "/list"
                            }
                        }
                    ]
                }
            }
            
            url = 'https://api.line.me/v2/bot/message/reply'
            headers = {
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {token}'
            }
            
            data = {
                'replyToken': reply_token,
                'messages': [flex_message]
            }
            
            req = urllib.request.Request(
                url,
                data=json.dumps(data).encode('utf-8'),
                headers=headers,
                method='POST'
            )
            
            with urllib.request.urlopen(req) as response:
                logging.info(f"Flex message sent: {response.status}")
                
        except Exception as e:
            logging.error(f"Error sending flex message: {e}")
    
    def send_help_flex_message(self, reply_token):
        """Send help message as flex message"""
        try:
            token = LINE_CHANNEL_ACCESS_TOKEN or os.getenv('LINE_CHANNEL_ACCESS_TOKEN', '')
            if not token:
                return
            
            import urllib.request
            
            flex_message = {
                "type": "flex",
                "altText": "📚 Article Hub Help",
                "contents": {
                    "type": "carousel",
                    "contents": [
                        {
                            "type": "bubble",
                            "header": {
                                "type": "box",
                                "layout": "vertical",
                                "contents": [
                                    {
                                        "type": "text",
                                        "text": "📚 Article Hub",
                                        "weight": "bold",
                                        "size": "lg",
                                        "color": "#FFFFFF"
                                    }
                                ],
                                "backgroundColor": "#667eea",
                                "paddingAll": "15px"
                            },
                            "body": {
                                "type": "box",
                                "layout": "vertical",
                                "contents": [
                                    {
                                        "type": "text",
                                        "text": "Save & Manage Articles",
                                        "weight": "bold",
                                        "margin": "md"
                                    },
                                    {
                                        "type": "text",
                                        "text": "Send any URL to save it instantly",
                                        "size": "sm",
                                        "color": "#666666",
                                        "wrap": True,
                                        "margin": "sm"
                                    }
                                ]
                            },
                            "footer": {
                                "type": "box",
                                "layout": "vertical",
                                "contents": [
                                    {
                                        "type": "button",
                                        "style": "primary",
                                        "color": "#667eea",
                                        "action": {
                                            "type": "uri",
                                            "label": "Open Web App",
                                            "uri": "https://09f85f116221.ngrok-free.app"
                                        }
                                    }
                                ]
                            }
                        },
                        {
                            "type": "bubble",
                            "header": {
                                "type": "box",
                                "layout": "vertical",
                                "contents": [
                                    {
                                        "type": "text",
                                        "text": "💬 Commands",
                                        "weight": "bold",
                                        "size": "lg",
                                        "color": "#FFFFFF"
                                    }
                                ],
                                "backgroundColor": "#764ba2",
                                "paddingAll": "15px"
                            },
                            "body": {
                                "type": "box",
                                "layout": "vertical",
                                "contents": [
                                    {
                                        "type": "text",
                                        "text": "/list - Recent articles",
                                        "margin": "md"
                                    },
                                    {
                                        "type": "text",
                                        "text": "/stats - Your statistics",
                                        "margin": "sm"
                                    },
                                    {
                                        "type": "text",
                                        "text": "/web - Open web interface",
                                        "margin": "sm"
                                    },
                                    {
                                        "type": "text",
                                        "text": "/help - This message",
                                        "margin": "sm"
                                    }
                                ]
                            }
                        }
                    ]
                },
                "quickReply": {
                    "items": [
                        {
                            "type": "action",
                            "action": {
                                "type": "message",
                                "label": "📋 My Articles",
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
                                "type": "uri",
                                "label": "🌐 Open Web",
                                "uri": "https://09f85f116221.ngrok-free.app"
                            }
                        }
                    ]
                }
            }
            
            self.send_line_message(reply_token, flex_message)
            
        except Exception as e:
            logging.error(f"Error sending help flex: {e}")
    
    def send_quick_reply_suggestions(self, reply_token):
        """Send message with quick reply suggestions"""
        try:
            token = LINE_CHANNEL_ACCESS_TOKEN or os.getenv('LINE_CHANNEL_ACCESS_TOKEN', '')
            if not token:
                return
            
            message = {
                "type": "text",
                "text": "Send me a URL to save it, or choose an option below:",
                "quickReply": {
                    "items": [
                        {
                            "type": "action",
                            "action": {
                                "type": "message",
                                "label": "📚 Open Hub",
                                "text": "/web"
                            }
                        },
                        {
                            "type": "action",
                            "action": {
                                "type": "message",
                                "label": "📋 My Articles",
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
                                "label": "❓ Help",
                                "text": "/help"
                            }
                        },
                        {
                            "type": "action",
                            "action": {
                                "type": "cameraRoll",
                                "label": "📷 Send Screenshot"
                            }
                        },
                        {
                            "type": "action",
                            "action": {
                                "type": "location",
                                "label": "📍 Location"
                            }
                        }
                    ]
                }
            }
            
            self.send_line_message(reply_token, message)
            
        except Exception as e:
            logging.error(f"Error sending quick reply: {e}")
    
    def send_line_message(self, reply_token, message):
        """Generic method to send LINE message"""
        try:
            token = LINE_CHANNEL_ACCESS_TOKEN or os.getenv('LINE_CHANNEL_ACCESS_TOKEN', '')
            if not token:
                logging.warning("LINE_CHANNEL_ACCESS_TOKEN not set")
                return
            
            import urllib.request
            
            url = 'https://api.line.me/v2/bot/message/reply'
            headers = {
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {token}'
            }
            
            data = {
                'replyToken': reply_token,
                'messages': [message] if isinstance(message, dict) else message
            }
            
            req = urllib.request.Request(
                url,
                data=json.dumps(data).encode('utf-8'),
                headers=headers,
                method='POST'
            )
            
            with urllib.request.urlopen(req) as response:
                logging.info(f"LINE message sent: {response.status}")
                
        except Exception as e:
            logging.error(f"Error sending LINE message: {e}")
    
    def send_article_list_flex(self, reply_token, articles):
        """Send article list as flex message"""
        if not articles:
            self.send_line_message(reply_token, {
                "type": "text",
                "text": "No articles yet! Send me URLs to save them."
            })
            return
        
        # Create article bubbles
        bubbles = []
        for article in articles[:5]:  # Limit to 5 for carousel
            bubble = {
                "type": "bubble",
                "body": {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                        {
                            "type": "text",
                            "text": article.get('title', 'Untitled')[:40],
                            "weight": "bold",
                            "wrap": True
                        },
                        {
                            "type": "text",
                            "text": f"Stage: {article.get('stage', 'inbox')}",
                            "size": "sm",
                            "color": "#666666",
                            "margin": "md"
                        }
                    ]
                },
                "footer": {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                        {
                            "type": "button",
                            "style": "link",
                            "action": {
                                "type": "uri",
                                "label": "Open Article",
                                "uri": article.get('url', '#')
                            }
                        }
                    ]
                }
            }
            bubbles.append(bubble)
        
        flex_message = {
            "type": "flex",
            "altText": "Your Recent Articles",
            "contents": {
                "type": "carousel",
                "contents": bubbles
            }
        }
        
        self.send_line_message(reply_token, flex_message)
    
    def send_stats_flex_message(self, reply_token, stats):
        """Send statistics as flex message"""
        flex_message = {
            "type": "flex",
            "altText": "Your Reading Statistics",
            "contents": {
                "type": "bubble",
                "header": {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                        {
                            "type": "text",
                            "text": "📊 Your Statistics",
                            "weight": "bold",
                            "size": "lg",
                            "color": "#FFFFFF"
                        }
                    ],
                    "backgroundColor": "#667eea",
                    "paddingAll": "15px"
                },
                "body": {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                        {
                            "type": "box",
                            "layout": "horizontal",
                            "contents": [
                                {
                                    "type": "text",
                                    "text": "Total Articles:",
                                    "flex": 1
                                },
                                {
                                    "type": "text",
                                    "text": str(stats['total']),
                                    "align": "end",
                                    "weight": "bold"
                                }
                            ],
                            "margin": "md"
                        },
                        {
                            "type": "box",
                            "layout": "horizontal",
                            "contents": [
                                {
                                    "type": "text",
                                    "text": "Completed:",
                                    "flex": 1
                                },
                                {
                                    "type": "text",
                                    "text": str(stats['completed']),
                                    "align": "end",
                                    "weight": "bold",
                                    "color": "#10b981"
                                }
                            ],
                            "margin": "sm"
                        },
                        {
                            "type": "box",
                            "layout": "horizontal",
                            "contents": [
                                {
                                    "type": "text",
                                    "text": "In Progress:",
                                    "flex": 1
                                },
                                {
                                    "type": "text",
                                    "text": str(stats['reading']),
                                    "align": "end",
                                    "weight": "bold",
                                    "color": "#f59e0b"
                                }
                            ],
                            "margin": "sm"
                        },
                        {
                            "type": "separator",
                            "margin": "lg"
                        },
                        {
                            "type": "box",
                            "layout": "horizontal",
                            "contents": [
                                {
                                    "type": "text",
                                    "text": "Completion Rate:",
                                    "flex": 1
                                },
                                {
                                    "type": "text",
                                    "text": f"{stats['completion_rate']}%",
                                    "align": "end",
                                    "weight": "bold",
                                    "color": "#667eea"
                                }
                            ],
                            "margin": "lg"
                        }
                    ]
                },
                "footer": {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                        {
                            "type": "button",
                            "style": "primary",
                            "color": "#667eea",
                            "action": {
                                "type": "uri",
                                "label": "View Details",
                                "uri": "https://09f85f116221.ngrok-free.app"
                            }
                        }
                    ]
                }
            }
        }
        
        self.send_line_message(reply_token, flex_message)
    
    def send_web_access_flex(self, reply_token):
        """Send web access flex message with LIFF"""
        flex_message = {
            "type": "flex",
            "altText": "Access Article Hub",
            "contents": {
                "type": "bubble",
                "hero": {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                        {
                            "type": "text",
                            "text": "🌐 Article Intelligence Hub",
                            "weight": "bold",
                            "size": "lg",
                            "color": "#FFFFFF",
                            "align": "center"
                        }
                    ],
                    "backgroundColor": "#667eea",
                    "paddingAll": "20px"
                },
                "body": {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                        {
                            "type": "text",
                            "text": "Access your articles from anywhere",
                            "wrap": True,
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
                                "label": "📱 Open in LINE (LIFF)",
                                "uri": "https://liff.line.me/2007552096-GxP76rNd"
                            }
                        },
                        {
                            "type": "button",
                            "style": "secondary",
                            "action": {
                                "type": "uri",
                                "label": "🌐 Open in Browser",
                                "uri": "https://09f85f116221.ngrok-free.app"
                            }
                        },
                        {
                            "type": "button",
                            "style": "secondary",
                            "action": {
                                "type": "uri",
                                "label": "📲 Install PWA",
                                "uri": "https://09f85f116221.ngrok-free.app"
                            }
                        }
                    ]
                }
            }
        }
        
        self.send_line_message(reply_token, flex_message)
    
    def get_recent_articles(self, limit=5):
        """Get recent articles for LINE user"""
        try:
            conn = sqlite3.connect(DB_PATH)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT title, url, stage FROM articles_kanban 
                WHERE is_archived = 0 
                ORDER BY id DESC 
                LIMIT ?
            ''', (limit,))
            
            articles = [dict(row) for row in cursor.fetchall()]
            conn.close()
            
            return articles
            
        except Exception as e:
            logging.error(f"Error getting recent articles: {e}")
            return []
    
    def get_user_stats(self):
        """Get statistics for LINE user"""
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            
            cursor.execute('SELECT COUNT(*) FROM articles_kanban WHERE is_archived = 0')
            total = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM articles_kanban WHERE stage = 'completed' AND is_archived = 0")
            completed = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM articles_kanban WHERE stage = 'reading' AND is_archived = 0")
            reading = cursor.fetchone()[0]
            
            conn.close()
            
            completion_rate = round((completed / max(total, 1)) * 100)
            
            return {
                'total': total,
                'completed': completed,
                'reading': reading,
                'completion_rate': completion_rate
            }
            
        except Exception as e:
            logging.error(f"Error getting user stats: {e}")
            return {'total': 0, 'completed': 0, 'reading': 0, 'completion_rate': 0}
    
    def handle_line_send(self, post_data):
        """Send article to LINE using Messaging API"""
        try:
            data = json.loads(post_data)
            url = data.get('url')
            
            # Here you would integrate with LINE Messaging API
            # For now, just return success
            
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'success': True}).encode())
            
        except Exception as e:
            logging.error(f'Error sending to LINE: {e}')
            self.send_error(500, str(e))
    
    def extract_title_from_url(self, url):
        """Extract title from URL"""
        # Remove protocol and www
        title = re.sub(r'^https?://(www\.)?', '', url)
        # Get domain and path
        title = title.split('?')[0]  # Remove query parameters
        title = title.split('#')[0]  # Remove fragments
        # Extract meaningful part
        parts = title.split('/')
        if len(parts) > 1 and parts[-1]:
            title = parts[-1].replace('-', ' ').replace('_', ' ').title()
        else:
            title = parts[0].split('.')[0].title()
        return title[:100]  # Limit length
    
    def detect_category(self, url):
        """Detect category from URL"""
        url_lower = url.lower()
        if any(x in url_lower for x in ['github.com', 'gitlab.com', 'bitbucket']):
            return 'Development'
        elif any(x in url_lower for x in ['youtube.com', 'vimeo.com', 'twitch']):
            return 'Video'
        elif any(x in url_lower for x in ['medium.com', 'dev.to', 'hackernews']):
            return 'Tech Articles'
        elif any(x in url_lower for x in ['twitter.com', 'x.com', 'facebook.com', 'linkedin']):
            return 'Social Media'
        elif any(x in url_lower for x in ['arxiv.org', 'scholar.google', 'pubmed']):
            return 'Research'
        else:
            return 'General'
    
    def calculate_quantum_score(self, url, title):
        """Calculate quantum reading score"""
        score = random.randint(400, 900)  # Base score
        
        # Adjust based on domain
        if 'github.com' in url:
            score += 50
        elif 'medium.com' in url:
            score += 30
        elif 'arxiv.org' in url:
            score += 80
        
        # Adjust based on title length (optimal 40-80 chars)
        title_len = len(title)
        if 40 <= title_len <= 80:
            score += 20
        
        return min(score, 1000)  # Cap at 1000
    
    def serve_manifest(self):
        """Serve PWA manifest"""
        try:
            with open('manifest.json', 'r') as f:
                content = f.read()
            self.send_response(200)
            self.send_header('Content-Type', 'application/manifest+json')
            self.send_header('Cache-Control', 'public, max-age=3600')
            self.end_headers()
            self.wfile.write(content.encode())
        except FileNotFoundError:
            self.send_error(404)
    
    def serve_service_worker(self):
        """Serve service worker"""
        try:
            with open('service-worker.js', 'r') as f:
                content = f.read()
            self.send_response(200)
            self.send_header('Content-Type', 'application/javascript')
            self.send_header('Service-Worker-Allowed', '/')
            self.send_header('Cache-Control', 'no-cache')
            self.end_headers()
            self.wfile.write(content.encode())
        except FileNotFoundError:
            self.send_error(404)
    
    def serve_offline_page(self):
        """Serve offline page"""
        try:
            with open('offline.html', 'r') as f:
                content = f.read()
            self.send_response(200)
            self.send_header('Content-Type', 'text/html')
            self.send_header('Cache-Control', 'public, max-age=3600')
            self.end_headers()
            self.wfile.write(content.encode())
        except FileNotFoundError:
            self.send_error(404)
    
    def serve_icon(self):
        """Serve PWA icons as colored squares with emoji"""
        # Generate a simple colored square icon as SVG
        svg = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512">
  <defs>
    <linearGradient id="grad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" style="stop-color:#667eea;stop-opacity:1" />
      <stop offset="100%" style="stop-color:#764ba2;stop-opacity:1" />
    </linearGradient>
  </defs>
  <rect width="512" height="512" rx="80" fill="url(#grad)"/>
  <text x="256" y="320" font-family="Arial" font-size="240" text-anchor="middle" fill="white">🧠</text>
</svg>'''
        
        self.send_response(200)
        self.send_header('Content-Type', 'image/svg+xml')
        self.send_header('Cache-Control', 'public, max-age=86400')
        self.end_headers()
        self.wfile.write(svg.encode())
    
    def log_message(self, format, *args):
        """Override to suppress default HTTP logging"""
        logging.info(f"{self.address_string()} - {format % args}")

def initialize_database():
    """Initialize database with proper schema"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Create table if not exists
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
            study_notes TEXT,
            key_learnings TEXT,
            quantum_score INTEGER DEFAULT 0,
            reading_streak INTEGER DEFAULT 0,
            total_reads INTEGER DEFAULT 0,
            reading_speed_wpm INTEGER DEFAULT 200,
            export_count INTEGER DEFAULT 0,
            total_study_time INTEGER DEFAULT 0,
            is_archived BOOLEAN DEFAULT 0,
            created_at TEXT,
            updated_at TEXT,
            completed_at TEXT
        )
    ''')
    
    conn.commit()
    
    # Log current stats
    cursor.execute('SELECT COUNT(*) FROM articles_kanban WHERE is_archived = 0')
    total = cursor.fetchone()[0]
    
    cursor.execute('SELECT stage, COUNT(*) FROM articles_kanban WHERE is_archived = 0 GROUP BY stage')
    for stage, count in cursor.fetchall():
        logging.info(f"  Stage '{stage}': {count} articles")
    
    logging.info(f"Database has {total} active articles")
    conn.close()

def main():
    print("\n" + "="*60)
    print("🧠 ULTIMATE ARTICLE INTELLIGENCE WITH LIFF & LINE")
    print("="*60)
    print(f"\n✅ Starting on http://localhost:{PORT}")
    print("\n✨ Features:")
    print("  • Full-width responsive layout ✓")
    print("  • LINE LIFF integration ✓")
    print("  • Mobile-optimized UI ✓")
    print("  • LINE Messaging API ✓")
    print("  • Drag & Drop Kanban ✓")
    print("  • Calendar scheduling ✓")
    print("  • Real-time sync ✓")
    print("\n📱 LIFF Setup:")
    print("  1. Create LIFF app at https://developers.line.biz")
    print("  2. Set LIFF_ID environment variable")
    print("  3. Add endpoint URL: http://your-domain/liff")
    print("\n" + "="*60)
    print("\nPress Ctrl+C to stop\n")
    
    initialize_database()
    
    try:
        server = HTTPServer(('', PORT), RequestHandler)
        logging.info(f"Server running on port {PORT}")
        server.serve_forever()
    except KeyboardInterrupt:
        print('\n\nShutting down server...')
        server.socket.close()
    except OSError as e:
        if e.errno == 48:  # Address already in use
            print(f"\n❌ Port {PORT} is already in use!")
            print("Try: lsof -ti:5001 | xargs kill -9")
        else:
            raise

if __name__ == '__main__':
    main()