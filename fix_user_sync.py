#!/usr/bin/env python3
"""
Fix user synchronization by adding user_id column to database
"""

import sqlite3
import os
from datetime import datetime

def add_user_id_column():
    """Add user_id column to articles_kanban table"""
    print("Fixing User Synchronization Issue")
    print("=" * 50)
    
    db_path = 'articles_kanban.db'
    
    # Backup database first
    backup_path = f'articles_kanban_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.db'
    print(f"1. Creating backup: {backup_path}")
    
    try:
        import shutil
        shutil.copy2(db_path, backup_path)
        print("   Backup created successfully")
    except Exception as e:
        print(f"   Warning: Could not create backup: {e}")
    
    # Connect to database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check if user_id column already exists
        cursor.execute("PRAGMA table_info(articles_kanban)")
        columns = [row[1] for row in cursor.fetchall()]
        
        if 'user_id' in columns:
            print("2. user_id column already exists")
        else:
            print("2. Adding user_id column to database...")
            cursor.execute("""
                ALTER TABLE articles_kanban 
                ADD COLUMN user_id TEXT
            """)
            conn.commit()
            print("   user_id column added successfully")
        
        # Add index for better performance
        print("3. Creating index on user_id...")
        try:
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_user_id 
                ON articles_kanban(user_id)
            """)
            conn.commit()
            print("   Index created successfully")
        except Exception as e:
            print(f"   Note: {e}")
        
        # Verify the change
        cursor.execute("PRAGMA table_info(articles_kanban)")
        columns = [row[1] for row in cursor.fetchall()]
        if 'user_id' in columns:
            print("4. Verification: user_id column confirmed")
        
    except Exception as e:
        print(f"Error: {e}")
        conn.rollback()
    finally:
        conn.close()

def create_user_table():
    """Create a separate users table for better data management"""
    print("\nCreating Users Table")
    print("=" * 50)
    
    conn = sqlite3.connect('articles_kanban.db')
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id TEXT PRIMARY KEY,
                line_user_id TEXT UNIQUE,
                display_name TEXT,
                picture_url TEXT,
                status_message TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_seen TIMESTAMP,
                article_count INTEGER DEFAULT 0,
                total_reading_time INTEGER DEFAULT 0,
                preferences TEXT
            )
        """)
        conn.commit()
        print("Users table created/verified")
        
    except Exception as e:
        print(f"Error creating users table: {e}")
    finally:
        conn.close()

def update_webhook_handler():
    """Create updated webhook handler that properly saves user_id"""
    
    code = '''
# Updated webhook handler with user_id support
def handle_line_message(event):
    """Process LINE message with user tracking"""
    
    user_id = event.source.user_id  # Get LINE user ID
    message_text = event.message.text
    
    # Extract URLs from message
    urls = extract_urls(message_text)
    
    if urls:
        for url in urls:
            # Save article with user_id
            save_article(url, user_id)
            
    # Send reply to user
    reply_message = create_reply(urls, user_id)
    line_bot_api.reply_message(event.reply_token, reply_message)

def save_article(url, user_id):
    """Save article with user association"""
    
    conn = sqlite3.connect('articles_kanban.db')
    cursor = conn.cursor()
    
    # Extract article metadata
    title = extract_title(url)
    summary = extract_summary(url)
    
    # Insert with user_id
    cursor.execute("""
        INSERT INTO articles_kanban (url, title, summary, user_id, stage)
        VALUES (?, ?, ?, ?, 'inbox')
    """, (url, title, summary, user_id))
    
    conn.commit()
    conn.close()
'''
    
    print("\nWebhook Handler Code Update")
    print("=" * 50)
    print("Add this code to your webhook handler to track users:")
    print(code)

def test_user_sync():
    """Test if user sync will work now"""
    print("\nTesting User Sync")
    print("=" * 50)
    
    conn = sqlite3.connect('articles_kanban.db')
    cursor = conn.cursor()
    
    try:
        # Test insert with user_id
        test_user = "Utest_" + datetime.now().strftime("%Y%m%d%H%M%S")
        cursor.execute("""
            INSERT INTO articles_kanban (url, title, user_id, stage)
            VALUES (?, ?, ?, ?)
        """, ("https://test.com", "Test Article", test_user, "inbox"))
        
        # Verify
        cursor.execute("SELECT * FROM articles_kanban WHERE user_id = ?", (test_user,))
        result = cursor.fetchone()
        
        if result:
            print(f"Test successful! Article saved with user_id: {test_user}")
            # Clean up test data
            cursor.execute("DELETE FROM articles_kanban WHERE user_id = ?", (test_user,))
        else:
            print("Test failed - could not save with user_id")
            
        conn.commit()
        
    except Exception as e:
        print(f"Test error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    add_user_id_column()
    create_user_table()
    test_user_sync()
    update_webhook_handler()
    
    print("\n" + "=" * 50)
    print("User Sync Fix Complete!")
    print("=" * 50)
    print("\nNext Steps:")
    print("1. Deploy the updated webhook handler")
    print("2. Test by sending a URL to your LINE bot")
    print("3. Check if articles are saved with user_id")
    print("\nThe production app should now properly track users!")