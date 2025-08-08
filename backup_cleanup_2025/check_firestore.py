#!/usr/bin/env python3
"""Check Firestore data"""

from google.cloud import firestore
import json

try:
    # Initialize Firestore
    db = firestore.Client(project='secondbrain-app-20250612')
    print("✓ Connected to Firestore")
    
    # Check articles collection
    articles_ref = db.collection('articles')
    docs = articles_ref.limit(10).stream()
    
    count = 0
    articles_by_stage = {}
    users = set()
    
    for doc in docs:
        count += 1
        data = doc.to_dict()
        stage = data.get('stage', 'unknown')
        user_id = data.get('user_id', 'no_user')
        
        if stage not in articles_by_stage:
            articles_by_stage[stage] = 0
        articles_by_stage[stage] += 1
        users.add(user_id)
        
        if count <= 3:  # Show first 3 articles
            print(f"\nArticle {count}:")
            print(f"  ID: {doc.id}")
            print(f"  User: {user_id}")
            print(f"  Stage: {stage}")
            print(f"  Title: {data.get('title', 'No title')[:50]}")
            print(f"  URL: {data.get('url', 'No URL')[:50]}")
    
    print(f"\n=== SUMMARY ===")
    print(f"Total articles: {count}")
    print(f"Unique users: {len(users)}")
    print(f"Articles by stage: {articles_by_stage}")
    
    if count == 0:
        print("\n❌ No articles found in Firestore!")
        print("This explains why the Kanban board is empty.")
    else:
        print(f"\n✓ Found {count} articles in Firestore")
        print("Users:", list(users)[:3], "..." if len(users) > 3 else "")
        
except Exception as e:
    print(f"❌ Error connecting to Firestore: {e}")
    import traceback
    traceback.print_exc()