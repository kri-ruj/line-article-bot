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
            
            <!-- AI Insights Section -->
            <div class="ai-insights-section" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; border-radius: 15px; padding: 20px; margin-bottom: 20px;">
                <h3 style="color: white;">🤖 AI Intelligence Dashboard</h3>
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 15px; margin-top: 15px;">
                    <div class="ai-stat-card" style="background: rgba(255,255,255,0.2); padding: 15px; border-radius: 10px; text-align: center;">
                        <div style="font-size: 2em;">📊</div>
                        <div style="font-size: 0.85em; opacity: 0.9;">Completion Rate</div>
                        <div id="ai-completion-rate" style="font-size: 1.5em; font-weight: bold;">--%</div>
                    </div>
                    <div class="ai-stat-card" style="background: rgba(255,255,255,0.2); padding: 15px; border-radius: 10px; text-align: center;">
                        <div style="font-size: 2em;">🔍</div>
                        <div style="font-size: 0.85em; opacity: 0.9;">Similar Articles</div>
                        <div id="ai-similar-count" style="font-size: 1.5em; font-weight: bold;">0</div>
                    </div>
                    <div class="ai-stat-card" style="background: rgba(255,255,255,0.2); padding: 15px; border-radius: 10px; text-align: center;">
                        <div style="font-size: 2em;">🏷️</div>
                        <div style="font-size: 0.85em; opacity: 0.9;">Auto Tags</div>
                        <div id="ai-tags-generated" style="font-size: 1.5em; font-weight: bold;">Active</div>
                    </div>
                    <div class="ai-stat-card" style="background: rgba(255,255,255,0.2); padding: 15px; border-radius: 10px; text-align: center;">
                        <div style="font-size: 2em;">💡</div>
                        <div style="font-size: 0.85em; opacity: 0.9;">Smart Priority</div>
                        <div id="ai-priority-status" style="font-size: 1.5em; font-weight: bold;">ON</div>
                    </div>
                </div>
                
                <!-- Similar Articles Warning -->
                <div id="similar-articles-warning" style="margin-top: 15px; padding: 10px; background: rgba(255,193,7,0.2); border-radius: 8px; display: none;">
                    <strong>⚠️ Duplicate Alert:</strong> <span id="similar-articles-text"></span>
                </div>
                
                <!-- AI Actions -->
                <div style="display: flex; gap: 10px; margin-top: 15px; flex-wrap: wrap;">
                    <button onclick="showAIPriority()" style="padding: 8px 16px; background: rgba(255,255,255,0.3); color: white; border: 1px solid rgba(255,255,255,0.5); border-radius: 20px; cursor: pointer; font-size: 0.85em;">
                        📊 View Priority Ranking
                    </button>
                    <button onclick="generateAllNotes()" style="padding: 8px 16px; background: rgba(255,255,255,0.3); color: white; border: 1px solid rgba(255,255,255,0.5); border-radius: 20px; cursor: pointer; font-size: 0.85em;">
                        📝 Generate Study Notes
                    </button>
                    <button onclick="showRecommendations()" style="padding: 8px 16px; background: rgba(255,255,255,0.3); color: white; border: 1px solid rgba(255,255,255,0.5); border-radius: 20px; cursor: pointer; font-size: 0.85em;">
                        💡 Smart Recommendations
                    </button>
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
            
            <!-- Analytics Dashboard -->
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; margin-top: 20px;">
                <!-- Reading Progress Chart -->
                <div style="background: white; border-radius: 15px; padding: 20px; box-shadow: 0 2px 10px rgba(0,0,0,0.05);">
                    <h3 style="margin-bottom: 15px;">📊 Reading Progress</h3>
                    <canvas id="progressChart" width="300" height="200"></canvas>
                </div>
                
                <!-- Category Distribution -->
                <div style="background: white; border-radius: 15px; padding: 20px; box-shadow: 0 2px 10px rgba(0,0,0,0.05);">
                    <h3 style="margin-bottom: 15px;">📂 Category Distribution</h3>
                    <canvas id="categoryChart" width="300" height="200"></canvas>
                </div>
                
                <!-- Reading Velocity -->
                <div style="background: white; border-radius: 15px; padding: 20px; box-shadow: 0 2px 10px rgba(0,0,0,0.05);">
                    <h3 style="margin-bottom: 15px;">⚡ Weekly Velocity</h3>
                    <div id="velocity-stats">
                        <div style="text-align: center; padding: 40px;">
                            <div style="font-size: 3em; font-weight: bold; color: #667eea;" id="weekly-velocity">0</div>
                            <div style="color: #666;">Articles per Week</div>
                            <div style="margin-top: 20px; color: #999; font-size: 0.9em;">
                                Average Reading Time: <span id="avg-reading-time">0</span> min
                            </div>
                        </div>
                    </div>
                </div>
                
                <!-- AI Insights Summary -->
                <div style="background: linear-gradient(135deg, #667eea, #764ba2); color: white; border-radius: 15px; padding: 20px; box-shadow: 0 2px 10px rgba(0,0,0,0.05);">
                    <h3 style="color: white; margin-bottom: 15px;">🤖 AI Insights</h3>
                    <div id="ai-insights-summary">
                        <div style="margin-bottom: 10px;">
                            <strong>Top Category:</strong> <span id="top-category">Loading...</span>
                        </div>
                        <div style="margin-bottom: 10px;">
                            <strong>Reading Efficiency:</strong> <span id="reading-efficiency">0%</span>
                        </div>
                        <div style="margin-bottom: 10px;">
                            <strong>Recommended Focus:</strong> <span id="recommended-focus">Loading...</span>
                        </div>
                        <div>
                            <strong>Next Goal:</strong> <span id="next-goal">Loading...</span>
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- Detailed Stats Table -->
            <div style="background: white; border-radius: 15px; padding: 20px; margin-top: 20px; box-shadow: 0 2px 10px rgba(0,0,0,0.05);">
                <h3>📋 Detailed Statistics</h3>
                <table style="width: 100%; margin-top: 15px;">
                    <thead>
                        <tr style="border-bottom: 2px solid #f0f0f0;">
                            <th style="text-align: left; padding: 10px;">Metric</th>
                            <th style="text-align: right; padding: 10px;">Value</th>
                            <th style="text-align: right; padding: 10px;">Trend</th>
                        </tr>
                    </thead>
                    <tbody id="stats-table">
                        <tr>
                            <td style="padding: 10px;">Total Articles</td>
                            <td style="text-align: right; padding: 10px;" id="stat-total">0</td>
                            <td style="text-align: right; padding: 10px;">-</td>
                        </tr>
                        <tr style="background: #f8f9fa;">
                            <td style="padding: 10px;">Completion Rate</td>
                            <td style="text-align: right; padding: 10px;" id="stat-completion">0%</td>
                            <td style="text-align: right; padding: 10px;">📈</td>
                        </tr>
                        <tr>
                            <td style="padding: 10px;">Study Hours</td>
                            <td style="text-align: right; padding: 10px;" id="stat-hours">0</td>
                            <td style="text-align: right; padding: 10px;">📈</td>
                        </tr>
                        <tr style="background: #f8f9fa;">
                            <td style="padding: 10px;">Articles This Week</td>
                            <td style="text-align: right; padding: 10px;" id="stat-weekly">0</td>
                            <td style="text-align: right; padding: 10px;">-</td>
                        </tr>
                    </tbody>
                </table>
            </div>
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
        
        // Load AI Features
        function loadAIInsights() {
            // Load analytics
            fetch('/api/ai/analytics')
                .then(response => response.json())
                .then(data => {
                    // Update completion rate
                    const completionRate = data.completion_rate || 0;
                    document.getElementById('ai-completion-rate').textContent = Math.round(completionRate) + '%';
                })
                .catch(error => console.error('Error loading AI analytics:', error));
            
            // Check for similar articles
            fetch('/api/ai/similar-articles')
                .then(response => response.json())
                .then(data => {
                    const similarCount = data.similar_articles ? data.similar_articles.length : 0;
                    document.getElementById('ai-similar-count').textContent = similarCount;
                    
                    if (similarCount > 0) {
                        const warning = document.getElementById('similar-articles-warning');
                        const text = document.getElementById('similar-articles-text');
                        text.textContent = `Found ${similarCount} potentially duplicate articles in your collection`;
                        warning.style.display = 'block';
                    }
                })
                .catch(error => console.error('Error checking similar articles:', error));
        }
        
        // Initialize
        window.onload = function() {
            loadArticles();
            loadLogs();
            loadActivity();
            loadAIInsights();
            
            // Auto-refresh logs every 3 seconds
            setInterval(loadLogs, 3000);
            
            // Auto-refresh articles every 10 seconds
            setInterval(loadArticles, 10000);
            
            // Auto-refresh AI insights every 30 seconds
            setInterval(loadAIInsights, 30000);
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
            
            // Load analytics if analytics tab
            if (tabName === 'analytics') {
                loadAnalyticsCharts();
            }
        }
        
        // Load Analytics Charts
        function loadAnalyticsCharts() {
            // Fetch analytics data
            fetch('/api/ai/analytics')
                .then(response => response.json())
                .then(data => {
                    // Update velocity stats
                    document.getElementById('weekly-velocity').textContent = data.weekly_velocity || 0;
                    document.getElementById('avg-reading-time').textContent = data.avg_reading_time || 0;
                    
                    // Update detailed stats
                    document.getElementById('stat-total').textContent = data.total_articles || 0;
                    document.getElementById('stat-completion').textContent = (data.completion_rate || 0) + '%';
                    document.getElementById('stat-hours').textContent = Math.round((data.avg_reading_time || 0) * (data.total_articles || 0) / 60);
                    document.getElementById('stat-weekly').textContent = data.weekly_velocity || 0;
                    
                    // Draw progress chart
                    drawProgressChart(data.stage_distribution || {});
                    
                    // Draw category chart
                    drawCategoryChart(data.category_distribution || {});
                    
                    // Update AI insights
                    updateAIInsightsSummary(data);
                })
                .catch(error => {
                    console.error('Error loading analytics:', error);
                });
        }
        
        // Draw Progress Chart (Donut)
        function drawProgressChart(stageData) {
            const canvas = document.getElementById('progressChart');
            if (!canvas) return;
            
            const ctx = canvas.getContext('2d');
            const width = canvas.width;
            const height = canvas.height;
            const centerX = width / 2;
            const centerY = height / 2;
            const radius = Math.min(width, height) / 3;
            
            // Clear canvas
            ctx.clearRect(0, 0, width, height);
            
            // Data
            const stages = ['inbox', 'reading', 'reviewing', 'completed'];
            const colors = ['#FFA726', '#42A5F5', '#AB47BC', '#66BB6A'];
            const total = Object.values(stageData).reduce((a, b) => a + b, 0) || 1;
            
            let currentAngle = -Math.PI / 2;
            
            stages.forEach((stage, index) => {
                const value = stageData[stage] || 0;
                const sliceAngle = (value / total) * 2 * Math.PI;
                
                // Draw slice
                ctx.beginPath();
                ctx.arc(centerX, centerY, radius, currentAngle, currentAngle + sliceAngle);
                ctx.lineTo(centerX, centerY);
                ctx.fillStyle = colors[index];
                ctx.fill();
                
                // Draw label
                if (value > 0) {
                    const labelAngle = currentAngle + sliceAngle / 2;
                    const labelX = centerX + Math.cos(labelAngle) * (radius * 0.7);
                    const labelY = centerY + Math.sin(labelAngle) * (radius * 0.7);
                    
                    ctx.fillStyle = 'white';
                    ctx.font = 'bold 12px sans-serif';
                    ctx.textAlign = 'center';
                    ctx.textBaseline = 'middle';
                    ctx.fillText(value, labelX, labelY);
                }
                
                currentAngle += sliceAngle;
            });
            
            // Draw center hole for donut
            ctx.beginPath();
            ctx.arc(centerX, centerY, radius * 0.4, 0, 2 * Math.PI);
            ctx.fillStyle = 'white';
            ctx.fill();
            
            // Draw legend
            ctx.font = '10px sans-serif';
            stages.forEach((stage, index) => {
                const legendY = height - 30 + (index % 2) * 15;
                const legendX = 10 + Math.floor(index / 2) * 80;
                
                ctx.fillStyle = colors[index];
                ctx.fillRect(legendX, legendY, 10, 10);
                
                ctx.fillStyle = '#333';
                ctx.textAlign = 'left';
                ctx.fillText(stage, legendX + 15, legendY + 8);
            });
        }
        
        // Draw Category Chart (Bar)
        function drawCategoryChart(categoryData) {
            const canvas = document.getElementById('categoryChart');
            if (!canvas) return;
            
            const ctx = canvas.getContext('2d');
            const width = canvas.width;
            const height = canvas.height;
            
            // Clear canvas
            ctx.clearRect(0, 0, width, height);
            
            const categories = Object.keys(categoryData).slice(0, 5);
            const values = categories.map(cat => categoryData[cat]);
            const maxValue = Math.max(...values, 1);
            
            const barWidth = (width - 40) / categories.length;
            const chartHeight = height - 60;
            
            categories.forEach((category, index) => {
                const value = values[index];
                const barHeight = (value / maxValue) * chartHeight;
                const x = 20 + index * barWidth;
                const y = height - 40 - barHeight;
                
                // Draw bar
                ctx.fillStyle = `hsl(${index * 60}, 70%, 60%)`;
                ctx.fillRect(x + barWidth * 0.1, y, barWidth * 0.8, barHeight);
                
                // Draw value
                ctx.fillStyle = '#333';
                ctx.font = 'bold 12px sans-serif';
                ctx.textAlign = 'center';
                ctx.fillText(value, x + barWidth / 2, y - 5);
                
                // Draw label
                ctx.save();
                ctx.translate(x + barWidth / 2, height - 35);
                ctx.rotate(-Math.PI / 6);
                ctx.font = '10px sans-serif';
                ctx.textAlign = 'right';
                ctx.fillText(category.substring(0, 10), 0, 0);
                ctx.restore();
            });
        }
        
        // Update AI Insights Summary
        function updateAIInsightsSummary(data) {
            // Find top category
            const categories = data.category_distribution || {};
            const topCat = Object.keys(categories).reduce((a, b) => 
                categories[a] > categories[b] ? a : b, 'None');
            document.getElementById('top-category').textContent = topCat;
            
            // Calculate efficiency
            const efficiency = data.completion_rate || 0;
            document.getElementById('reading-efficiency').textContent = 
                efficiency > 70 ? 'Excellent' : efficiency > 40 ? 'Good' : 'Needs Improvement';
            
            // Recommended focus
            const inbox = data.stage_distribution?.inbox || 0;
            const reading = data.stage_distribution?.reading || 0;
            let focus = 'Start new articles';
            if (reading > 3) focus = 'Complete current reads';
            else if (inbox > 10) focus = 'Clear inbox backlog';
            document.getElementById('recommended-focus').textContent = focus;
            
            // Next goal
            const completed = data.stage_distribution?.completed || 0;
            const nextMilestone = Math.ceil((completed + 1) / 10) * 10;
            document.getElementById('next-goal').textContent = `Reach ${nextMilestone} completed articles`;
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
            loadAIInsights();
        }
        
        function addArticle() {
            // Implement add article modal
            alert('Add article feature coming soon!');
        }
        
        // AI Priority Ranking
        function showAIPriority() {
            const modal = document.createElement('div');
            modal.className = 'modal show';
            modal.innerHTML = `
                <div class="modal-content" style="background: white; border-radius: 20px; width: 90%; max-width: 800px; max-height: 90vh; overflow-y: auto;">
                    <div class="modal-header" style="background: linear-gradient(135deg, #667eea, #764ba2); color: white; padding: 20px; border-radius: 20px 20px 0 0; display: flex; justify-content: space-between;">
                        <h2>📊 AI Priority Ranking</h2>
                        <button onclick="this.closest('.modal').remove()" style="background: none; border: none; color: white; font-size: 1.5em; cursor: pointer;">&times;</button>
                    </div>
                    <div class="modal-body" style="padding: 20px;">
                        <div id="priority-loading" style="text-align: center; padding: 40px;">
                            <div class="loading"></div>
                            <p>Analyzing articles...</p>
                        </div>
                        <div id="priority-list" style="display: none;"></div>
                    </div>
                </div>
            `;
            document.body.appendChild(modal);
            
            // Load priority ranking
            fetch('/api/ai/priority-ranking')
                .then(response => response.json())
                .then(data => {
                    const list = document.getElementById('priority-list');
                    if (data.ranked_articles && data.ranked_articles.length > 0) {
                        list.innerHTML = data.ranked_articles.map((article, index) => {
                            const score = Math.round(article.priority_score || 0);
                            const borderColor = score >= 70 ? '#66BB6A' : score >= 40 ? '#FFA726' : '#EF5350';
                            return `
                                <div style="background: #f8f9fa; border-radius: 12px; padding: 15px; margin-bottom: 10px; border-left: 4px solid ${borderColor};">
                                    <div style="display: flex; align-items: center;">
                                        <div style="width: 40px; height: 40px; background: linear-gradient(135deg, #667eea, #764ba2); color: white; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: bold; margin-right: 15px;">
                                            ${index + 1}
                                        </div>
                                        <div style="flex: 1;">
                                            <div style="font-weight: 600;">${article.title || 'Untitled'}</div>
                                            <div style="font-size: 0.85em; color: #666;">
                                                📂 ${article.category || 'Other'} · 📋 ${article.stage} · ⏱️ ${article.reading_time || 'N/A'} min
                                            </div>
                                        </div>
                                        <div style="font-size: 1.2em; font-weight: bold; color: #667eea;">${score}/100</div>
                                    </div>
                                </div>
                            `;
                        }).join('');
                    } else {
                        list.innerHTML = '<p style="text-align: center; color: #999;">No articles to prioritize</p>';
                    }
                    document.getElementById('priority-loading').style.display = 'none';
                    document.getElementById('priority-list').style.display = 'block';
                })
                .catch(error => {
                    console.error('Error loading priority:', error);
                    document.getElementById('priority-list').innerHTML = '<p style="color: #EF5350;">Error loading rankings</p>';
                    document.getElementById('priority-loading').style.display = 'none';
                    document.getElementById('priority-list').style.display = 'block';
                });
        }
        
        // Generate All Notes
        function generateAllNotes() {
            if (!confirm('Generate study notes for all incomplete articles? This may take a moment.')) return;
            
            const incomplete = Object.values(articles).filter(a => a.stage !== 'completed');
            if (incomplete.length === 0) {
                alert('No incomplete articles found');
                return;
            }
            
            alert(`Generating notes for ${incomplete.length} articles...`);
            let completed = 0;
            
            incomplete.forEach(article => {
                fetch(`/api/ai/study-notes/${article.id}`)
                    .then(response => response.json())
                    .then(data => {
                        completed++;
                        if (completed === incomplete.length) {
                            alert('Study notes generated successfully!');
                            document.getElementById('ai-notes-generated').textContent = completed;
                        }
                    })
                    .catch(error => console.error(`Error generating notes for ${article.title}:`, error));
            });
        }
        
        // Show Recommendations
        function showRecommendations() {
            const firstArticle = Object.values(articles)[0];
            if (!firstArticle) {
                alert('No articles available for recommendations');
                return;
            }
            
            const modal = document.createElement('div');
            modal.className = 'modal show';
            modal.innerHTML = `
                <div class="modal-content" style="background: white; border-radius: 20px; width: 90%; max-width: 800px; max-height: 90vh; overflow-y: auto;">
                    <div class="modal-header" style="background: linear-gradient(135deg, #667eea, #764ba2); color: white; padding: 20px; border-radius: 20px 20px 0 0; display: flex; justify-content: space-between;">
                        <h2>💡 Smart Recommendations</h2>
                        <button onclick="this.closest('.modal').remove()" style="background: none; border: none; color: white; font-size: 1.5em; cursor: pointer;">&times;</button>
                    </div>
                    <div class="modal-body" style="padding: 20px;">
                        <div id="rec-loading" style="text-align: center; padding: 40px;">
                            <div class="loading"></div>
                            <p>Finding recommendations...</p>
                        </div>
                        <div id="rec-content" style="display: none;"></div>
                    </div>
                </div>
            `;
            document.body.appendChild(modal);
            
            fetch(`/api/ai/recommendations/${firstArticle.id}`)
                .then(response => response.json())
                .then(data => {
                    const content = document.getElementById('rec-content');
                    if (data.recommendations && data.recommendations.length > 0) {
                        content.innerHTML = `
                            <p style="margin-bottom: 20px;">Based on: <strong>${firstArticle.title}</strong></p>
                            ${data.recommendations.map(rec => `
                                <div style="background: #f8f9fa; padding: 15px; border-radius: 12px; margin-bottom: 10px; border-left: 4px solid #667eea;">
                                    <h4 style="margin: 0 0 5px 0;">${rec.title}</h4>
                                    <p style="color: #666; font-size: 0.85em;">
                                        📂 ${rec.category} · Match: ${Math.round(rec.similarity_score * 100)}%
                                    </p>
                                    <p style="color: #667eea; font-size: 0.85em;">
                                        💡 ${rec.reason}
                                    </p>
                                </div>
                            `).join('')}
                        `;
                    } else {
                        content.innerHTML = '<p style="text-align: center; color: #999;">No recommendations available</p>';
                    }
                    document.getElementById('rec-loading').style.display = 'none';
                    document.getElementById('rec-content').style.display = 'block';
                })
                .catch(error => {
                    console.error('Error loading recommendations:', error);
                    document.getElementById('rec-content').innerHTML = '<p style="color: #EF5350;">Error loading recommendations</p>';
                    document.getElementById('rec-loading').style.display = 'none';
                    document.getElementById('rec-content').style.display = 'block';
                });
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

# Import AI features
try:
    from ai_features import ai_features
    AI_FEATURES_AVAILABLE = True
except ImportError:
    AI_FEATURES_AVAILABLE = False
    print("AI features not available")

@app.route('/api/ai/recommendations/<int:article_id>')
def get_recommendations(article_id):
    """Get AI recommendations for an article"""
    if not AI_FEATURES_AVAILABLE:
        return jsonify({'error': 'AI features not available'}), 503
    
    try:
        recommendations = ai_features.get_article_recommendations(article_id)
        return jsonify({'recommendations': recommendations})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/ai/similar-articles')
def get_similar_articles():
    """Get similar/duplicate articles"""
    if not AI_FEATURES_AVAILABLE:
        return jsonify({'error': 'AI features not available'}), 503
    
    try:
        similar_pairs = ai_features.detect_similar_articles(threshold=0.7)
        return jsonify({'similar_articles': [
            {
                'article1': pair[0],
                'article2': pair[1],
                'similarity': pair[2]
            } for pair in similar_pairs[:10]  # Limit to top 10
        ]})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/ai/analytics')
def get_reading_analytics():
    """Get reading analytics"""
    if not AI_FEATURES_AVAILABLE:
        return jsonify({'error': 'AI features not available'}), 503
    
    try:
        analytics = ai_features.get_reading_analytics()
        return jsonify(analytics)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/ai/generate-tags', methods=['POST'])
def generate_tags():
    """Generate tags for text"""
    if not AI_FEATURES_AVAILABLE:
        return jsonify({'error': 'AI features not available'}), 503
    
    try:
        data = request.json
        text = data.get('text', '')
        title = data.get('title', '')
        tags = ai_features.generate_auto_tags(text, title)
        return jsonify({'tags': tags})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/ai/priority-ranking')
def get_priority_ranking():
    """Get articles ranked by AI priority"""
    if not AI_FEATURES_AVAILABLE:
        return jsonify({'error': 'AI features not available'}), 503
    
    try:
        with closing(get_db(KANBAN_DB_PATH)) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, url, title, summary, category, reading_time, 
                       stage, added_date
                FROM articles_kanban
                WHERE is_archived = 0 AND stage != 'completed'
                ORDER BY added_date DESC
            ''')
            articles = cursor.fetchall()
            
            # Calculate priority for each article
            ranked_articles = []
            for article in articles:
                article_dict = dict(article)
                article_dict['quality_score'] = 0  # Default since column doesn't exist
                priority_score = ai_features.calculate_priority_score(article_dict)
                article_dict['priority_score'] = priority_score
                ranked_articles.append(article_dict)
            
            # Sort by priority score
            ranked_articles.sort(key=lambda x: x['priority_score'], reverse=True)
            
            return jsonify({'ranked_articles': ranked_articles[:20]})  # Top 20
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/ai/study-notes/<int:article_id>')
def generate_study_notes(article_id):
    """Generate study notes for an article"""
    if not AI_FEATURES_AVAILABLE:
        return jsonify({'error': 'AI features not available'}), 503
    
    try:
        with closing(get_db(KANBAN_DB_PATH)) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM articles_kanban WHERE id = ?
            ''', (article_id,))
            article = cursor.fetchone()
            
            if not article:
                return jsonify({'error': 'Article not found'}), 404
            
            article_dict = dict(article)
            article_dict['quality_score'] = 0  # Default
            notes = ai_features.generate_study_notes(article_dict)
            
            # Save notes to database
            cursor.execute('''
                UPDATE articles_kanban
                SET study_notes = ?
                WHERE id = ?
            ''', (notes, article_id))
            conn.commit()
            
            return jsonify({'notes': notes})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/ai/study-questions/<int:article_id>')
def generate_study_questions(article_id):
    """Generate study questions for an article"""
    if not AI_FEATURES_AVAILABLE:
        return jsonify({'error': 'AI features not available'}), 503
    
    try:
        with closing(get_db(KANBAN_DB_PATH)) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT title, summary, extracted_content
                FROM articles_kanban WHERE id = ?
            ''', (article_id,))
            article = cursor.fetchone()
            
            if not article:
                return jsonify({'error': 'Article not found'}), 404
            
            content = article['extracted_content'] or article['summary'] or ''
            questions = ai_features.generate_study_questions(content[:2000], article['title'])
            
            return jsonify({'questions': questions})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

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