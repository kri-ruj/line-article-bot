#!/usr/bin/env python3
"""
Comprehensive data migration script
Merges all articles from various databases into articles_kanban.db
"""

import sqlite3
import hashlib
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

def get_url_hash(url):
    """Generate hash for URL to avoid duplicates"""
    return hashlib.md5(url.encode()).hexdigest() if url else None

def migrate_all_data():
    """Migrate all article data from various databases"""
    
    # Connect to target database
    target_conn = sqlite3.connect('articles_kanban.db')
    target_conn.execute('PRAGMA journal_mode=WAL')
    target_cursor = target_conn.cursor()
    
    # Ensure table exists with all columns
    logger.info("Creating/updating target table schema...")
    target_cursor.execute('''
        CREATE TABLE IF NOT EXISTS articles_kanban (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            url TEXT,
            url_hash TEXT UNIQUE,
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
            export_count INTEGER DEFAULT 0,
            source_db TEXT
        )
    ''')
    
    # Get existing URLs to avoid duplicates
    target_cursor.execute("SELECT url_hash FROM articles_kanban WHERE url_hash IS NOT NULL")
    existing_hashes = {row[0] for row in target_cursor.fetchall()}
    logger.info(f"Found {len(existing_hashes)} existing articles in target database")
    
    total_migrated = 0
    
    # 1. Migrate from articles.db
    try:
        logger.info("\n=== Migrating from articles.db ===")
        source_conn = sqlite3.connect('articles.db')
        source_conn.row_factory = sqlite3.Row
        source_cursor = source_conn.cursor()
        
        source_cursor.execute("SELECT * FROM articles")
        articles = source_cursor.fetchall()
        logger.info(f"Found {len(articles)} articles in articles.db")
        
        for article in articles:
            url = article['url']
            url_hash = get_url_hash(url)
            
            if url_hash and url_hash not in existing_hashes:
                target_cursor.execute('''
                    INSERT INTO articles_kanban 
                    (url, url_hash, title, summary, category, stage, created_at, source_db)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    url,
                    url_hash,
                    article['title'] if 'title' in article.keys() else 'Untitled',
                    article['summary'] if 'summary' in article.keys() else '',
                    article['category'] if 'category' in article.keys() else 'Other',
                    'inbox',
                    article['created_at'] if 'created_at' in article.keys() else datetime.now(),
                    'articles.db'
                ))
                existing_hashes.add(url_hash)
                total_migrated += 1
                logger.info(f"  Migrated: {article['title'] if 'title' in article.keys() else url[:50]}")
        
        source_conn.close()
    except Exception as e:
        logger.warning(f"Could not migrate from articles.db: {e}")
    
    # 2. Migrate from articles_enhanced.db
    try:
        logger.info("\n=== Migrating from articles_enhanced.db ===")
        source_conn = sqlite3.connect('articles_enhanced.db')
        source_conn.row_factory = sqlite3.Row
        source_cursor = source_conn.cursor()
        
        source_cursor.execute("SELECT * FROM articles")
        articles = source_cursor.fetchall()
        logger.info(f"Found {len(articles)} articles in articles_enhanced.db")
        
        for article in articles:
            url = article['url']
            url_hash = get_url_hash(url)
            
            if url_hash and url_hash not in existing_hashes:
                # Map enhanced fields
                category = article['category'] if 'category' in article.keys() else 'Other'
                if category == 'General':
                    category = 'Other'
                
                target_cursor.execute('''
                    INSERT INTO articles_kanban 
                    (url, url_hash, title, summary, category, stage, priority, 
                     word_count, reading_time, created_at, source_db)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    url,
                    url_hash,
                    article['title'] if 'title' in article.keys() else 'Untitled',
                    article['summary'] if 'summary' in article.keys() else '',
                    category,
                    'inbox',
                    article['priority'] if 'priority' in article.keys() else 'medium',
                    article['word_count'] if 'word_count' in article.keys() else 0,
                    article['estimated_reading_time'] if 'estimated_reading_time' in article.keys() else 5,
                    article['created_at'] if 'created_at' in article.keys() else datetime.now(),
                    'articles_enhanced.db'
                ))
                existing_hashes.add(url_hash)
                total_migrated += 1
                logger.info(f"  Migrated: {article['title'] if 'title' in article.keys() else url[:50]}")
        
        source_conn.close()
    except Exception as e:
        logger.warning(f"Could not migrate from articles_enhanced.db: {e}")
    
    # 3. Migrate from articles_ultra.db
    try:
        logger.info("\n=== Migrating from articles_ultra.db ===")
        source_conn = sqlite3.connect('articles_ultra.db')
        source_conn.row_factory = sqlite3.Row
        source_cursor = source_conn.cursor()
        
        # Try to get articles from articles_ultra table
        try:
            source_cursor.execute("SELECT * FROM articles_ultra")
        except:
            # Fallback to articles table if articles_ultra doesn't exist
            source_cursor.execute("SELECT * FROM articles")
        
        articles = source_cursor.fetchall()
        logger.info(f"Found {len(articles)} articles in articles_ultra.db")
        
        for article in articles:
            url = article['url'] if 'url' in article.keys() else None
            if not url:
                continue
                
            url_hash = get_url_hash(url)
            
            if url_hash and url_hash not in existing_hashes:
                target_cursor.execute('''
                    INSERT INTO articles_kanban 
                    (url, url_hash, title, summary, category, stage, priority,
                     word_count, reading_time, created_at, source_db)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    url,
                    url_hash,
                    article['title'] if 'title' in article.keys() else 'Untitled',
                    article['summary'] if 'summary' in article.keys() else '',
                    article['category'] if 'category' in article.keys() else 'Other',
                    article['stage'] if 'stage' in article.keys() else 'inbox',
                    article['priority'] if 'priority' in article.keys() else 'medium',
                    article['word_count'] if 'word_count' in article.keys() else 0,
                    article['reading_time_minutes'] if 'reading_time_minutes' in article.keys() else 5,
                    article['created_at'] if 'created_at' in article.keys() else datetime.now(),
                    'articles_ultra.db'
                ))
                existing_hashes.add(url_hash)
                total_migrated += 1
                logger.info(f"  Migrated: {article['title'] if 'title' in article.keys() else url[:50]}")
        
        source_conn.close()
    except Exception as e:
        logger.warning(f"Could not migrate from articles_ultra.db: {e}")
    
    # Commit all changes
    target_conn.commit()
    
    # Get final statistics
    target_cursor.execute("SELECT COUNT(*) FROM articles_kanban")
    total_articles = target_cursor.fetchone()[0]
    
    target_cursor.execute("SELECT stage, COUNT(*) FROM articles_kanban GROUP BY stage")
    stage_stats = target_cursor.fetchall()
    
    target_cursor.execute("SELECT source_db, COUNT(*) FROM articles_kanban WHERE source_db IS NOT NULL GROUP BY source_db")
    source_stats = target_cursor.fetchall()
    
    target_conn.close()
    
    # Print summary
    logger.info("\n" + "="*60)
    logger.info("MIGRATION COMPLETE!")
    logger.info("="*60)
    logger.info(f"Total articles migrated: {total_migrated}")
    logger.info(f"Total articles in database: {total_articles}")
    
    logger.info("\nArticles by stage:")
    for stage, count in stage_stats:
        logger.info(f"  {stage}: {count}")
    
    logger.info("\nArticles by source database:")
    for source, count in source_stats:
        logger.info(f"  {source}: {count}")
    
    logger.info("\n✅ All data has been successfully migrated to articles_kanban.db")
    
    return total_articles

if __name__ == "__main__":
    total = migrate_all_data()
    print(f"\n🎉 Migration complete! {total} total articles in database.")
    print("You can now restart the app to see all your articles.")