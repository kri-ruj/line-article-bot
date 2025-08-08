#!/usr/bin/env python3
"""View your article summaries and logs"""

import sqlite3
import json
from datetime import datetime
from contextlib import closing

def view_summaries():
    """Display all your saved articles with summaries"""
    
    print("="*80)
    print("📚 YOUR ARTICLE COLLECTION SUMMARY")
    print("="*80)
    print(f"\nGenerated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # Try both databases
    databases = ['articles_enhanced.db', 'articles_ultra.db']
    
    for db_path in databases:
        try:
            conn = sqlite3.connect(db_path, timeout=30.0)
            conn.row_factory = sqlite3.Row
            
            with closing(conn) as conn:
                cursor = conn.cursor()
                
                # Get all articles
                cursor.execute('''
                    SELECT id, url, title, summary, category, sentiment, 
                           topics, key_points, saved_at, word_count, reading_time
                    FROM articles 
                    ORDER BY saved_at DESC
                ''')
                
                articles = cursor.fetchall()
                
                if articles:
                    print(f"\n📂 Database: {db_path}")
                    print(f"📊 Total Articles: {len(articles)}\n")
                    print("-"*80)
                    
                    for i, article in enumerate(articles, 1):
                        title = (article['title'] or 'Untitled')[:60]
                        print(f"\n{i}. {title}...")
                        print(f"   🔗 {article['url']}")
                        print(f"   📅 Saved: {article['saved_at']}")
                        
                        if article['summary']:
                            print(f"\n   📝 Summary:")
                            print(f"   {article['summary'][:200]}...")
                        
                        if article['category']:
                            print(f"\n   📂 Category: {article['category']}")
                        
                        if article['sentiment']:
                            print(f"   😊 Sentiment: {article['sentiment']}")
                        
                        if article['topics']:
                            try:
                                topics = json.loads(article['topics'])
                                if topics:
                                    print(f"   🏷️ Topics: {', '.join(topics[:5])}")
                            except:
                                pass
                        
                        if article['key_points']:
                            try:
                                points = json.loads(article['key_points'])
                                if points:
                                    print(f"\n   🎯 Key Points:")
                                    for j, point in enumerate(points[:3], 1):
                                        print(f"      {j}. {point[:80]}...")
                            except:
                                pass
                        
                        if article['word_count']:
                            print(f"\n   📊 Stats: {article['word_count']} words | {article['reading_time']} min read")
                        
                        print("-"*80)
                        
        except sqlite3.OperationalError as e:
            if "no such table" not in str(e):
                print(f"⚠️ Database {db_path}: {e}")
        except Exception as e:
            print(f"⚠️ Error reading {db_path}: {e}")

def view_recent_logs():
    """Show recent server activity"""
    print("\n" + "="*80)
    print("📜 RECENT SERVER ACTIVITY")
    print("="*80)
    
    log_files = ['server.log', 'ultra_server.log']
    
    for log_file in log_files:
        try:
            with open(log_file, 'r') as f:
                lines = f.readlines()
                
            # Get last 20 meaningful lines
            meaningful_lines = []
            for line in reversed(lines):
                if any(keyword in line for keyword in ['Processing URL', 'AI analysis', 'saved', 'ERROR', 'Reply sent']):
                    meaningful_lines.append(line.strip())
                    if len(meaningful_lines) >= 10:
                        break
            
            if meaningful_lines:
                print(f"\n📄 {log_file} (Recent Activity):")
                print("-"*40)
                for line in reversed(meaningful_lines):
                    print(f"  {line[:150]}")
                    
        except FileNotFoundError:
            pass
        except Exception as e:
            print(f"⚠️ Error reading {log_file}: {e}")

def show_statistics():
    """Display collection statistics"""
    print("\n" + "="*80)
    print("📈 COLLECTION STATISTICS")
    print("="*80)
    
    try:
        conn = sqlite3.connect('articles_enhanced.db', timeout=30.0)
        conn.row_factory = sqlite3.Row
        
        with closing(conn) as conn:
            cursor = conn.cursor()
            
            # Total articles
            cursor.execute("SELECT COUNT(*) as total FROM articles")
            total = cursor.fetchone()['total']
            
            if total > 0:
                # Category distribution
                cursor.execute("""
                    SELECT category, COUNT(*) as count 
                    FROM articles 
                    WHERE category IS NOT NULL 
                    GROUP BY category 
                    ORDER BY count DESC
                """)
                categories = cursor.fetchall()
                
                # Sentiment distribution
                cursor.execute("""
                    SELECT sentiment, COUNT(*) as count 
                    FROM articles 
                    WHERE sentiment IS NOT NULL 
                    GROUP BY sentiment
                """)
                sentiments = cursor.fetchall()
                
                # Word count stats
                cursor.execute("""
                    SELECT 
                        SUM(word_count) as total_words,
                        AVG(word_count) as avg_words,
                        MAX(word_count) as max_words,
                        MIN(word_count) as min_words
                    FROM articles 
                    WHERE word_count > 0
                """)
                word_stats = cursor.fetchone()
                
                print(f"\n📚 Total Articles: {total}")
                
                if categories:
                    print("\n📂 Categories:")
                    for cat in categories:
                        print(f"   • {cat['category']}: {cat['count']} articles")
                
                if sentiments:
                    print("\n😊 Sentiments:")
                    for sent in sentiments:
                        print(f"   • {sent['sentiment']}: {sent['count']} articles")
                
                if word_stats['total_words']:
                    print("\n📊 Content Metrics:")
                    print(f"   • Total Words Analyzed: {word_stats['total_words']:,}")
                    print(f"   • Average Article Length: {word_stats['avg_words']:.0f} words")
                    print(f"   • Longest Article: {word_stats['max_words']} words")
                    print(f"   • Shortest Article: {word_stats['min_words']} words")
                    
    except Exception as e:
        print(f"⚠️ Error getting statistics: {e}")

if __name__ == "__main__":
    view_summaries()
    show_statistics()
    view_recent_logs()
    
    print("\n" + "="*80)
    print("💡 TIP: Visit https://6623ee01e26c.ngrok-free.app/ for visual dashboard")
    print("="*80)