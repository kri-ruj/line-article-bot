#!/usr/bin/env python3
"""
Migrate articles to your LINE user account
"""

from google.cloud import firestore
import sys

# Initialize Firestore
db = firestore.Client(project='secondbrain-app-20250612')

def show_article_owners():
    """Show who owns the articles"""
    print("\n=== CHECKING ARTICLE OWNERSHIP ===\n")
    
    articles_ref = db.collection('articles')
    docs = articles_ref.stream()
    
    user_articles = {}
    total = 0
    
    for doc in docs:
        data = doc.to_dict()
        user_id = data.get('user_id', 'unknown')
        
        if user_id not in user_articles:
            user_articles[user_id] = {
                'count': 0,
                'stages': {},
                'sample_titles': []
            }
        
        user_articles[user_id]['count'] += 1
        
        stage = data.get('stage', 'unknown')
        if stage not in user_articles[user_id]['stages']:
            user_articles[user_id]['stages'][stage] = 0
        user_articles[user_id]['stages'][stage] += 1
        
        if len(user_articles[user_id]['sample_titles']) < 3:
            title = data.get('title', 'Untitled')[:50]
            user_articles[user_id]['sample_titles'].append(title)
        
        total += 1
    
    print(f"Total articles in database: {total}\n")
    print("Articles by User ID:")
    print("-" * 60)
    
    for user_id, info in user_articles.items():
        print(f"\nUser: {user_id}")
        print(f"  Articles: {info['count']}")
        print(f"  Stages: {info['stages']}")
        print(f"  Sample articles:")
        for title in info['sample_titles']:
            print(f"    - {title}")
    
    return user_articles

def migrate_articles(from_user_id, to_user_id):
    """Migrate all articles from one user to another"""
    print(f"\n=== MIGRATING ARTICLES ===")
    print(f"FROM: {from_user_id}")
    print(f"TO: {to_user_id}\n")
    
    if not to_user_id or to_user_id == 'YOUR_USER_ID_HERE':
        print("ERROR: Please provide your actual User ID")
        print("1. Go to https://article-hub-959205905728.asia-northeast1.run.app/dashboard")
        print("2. Click 'Debug' link")
        print("3. Copy your User ID from the popup")
        return
    
    articles_ref = db.collection('articles')
    
    # Find articles belonging to from_user_id
    query = articles_ref.where('user_id', '==', from_user_id)
    docs = query.stream()
    
    migrated = 0
    for doc in docs:
        data = doc.to_dict()
        # Update the user_id
        doc.reference.update({'user_id': to_user_id})
        migrated += 1
        print(f"  Migrated: {data.get('title', 'Untitled')[:50]}")
    
    print(f"\n✅ Successfully migrated {migrated} articles!")
    print(f"\nNow refresh your dashboard to see the articles:")
    print("https://article-hub-959205905728.asia-northeast1.run.app/dashboard")
    
    return migrated

if __name__ == "__main__":
    # Show current article ownership
    user_articles = show_article_owners()
    
    print("\n" + "=" * 60)
    print("YOUR OPTIONS:")
    print("=" * 60)
    
    print("\n1. If you're Udcd08cd8a445c68f462a739e8898abb9:")
    print("   - You already have 36 articles! They should appear.")
    print("   - Try clearing cache and refreshing.")
    
    print("\n2. If you're U2de324e2a7198cf6ef152ab22afc80ea:")
    print("   - You have 26 articles! They should appear.")
    
    print("\n3. If you're a different user:")
    print("   - Your articles might be under a different ID")
    print("   - Or you need to migrate articles to your account")
    
    print("\n4. To migrate ALL 62 articles to YOUR account:")
    print("   a) Get your User ID from Debug popup")
    print("   b) Run this command:")
    print("      python3 migrate_all_to_user.py YOUR_USER_ID_HERE")
    
    print("\n5. To test with sample data immediately:")
    print("   https://article-hub-959205905728.asia-northeast1.run.app/dashboard?test=true")