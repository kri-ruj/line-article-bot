#!/usr/bin/env python3
"""Migrate articles from old database to AI-enhanced database with full AI analysis"""

import sqlite3
import json
import logging
from contextlib import closing
from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize OpenAI
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '')
openai_client = None
if OPENAI_API_KEY and len(OPENAI_API_KEY) > 20:
    openai_client = OpenAI(api_key=OPENAI_API_KEY)
    print("✅ OpenAI client initialized")

def analyze_with_ai(content, title, url):
    """Comprehensive AI analysis of article content"""
    if not openai_client or not content:
        return {}
    
    try:
        analysis_prompt = f"""Analyze this article and provide a detailed JSON response:

Title: {title}
URL: {url}
Content: {content[:3000]}

Return a JSON object with these fields:
{{
    "summary": "2-3 sentence summary",
    "category": "main category (Technology/Business/Science/Health/Politics/Entertainment/Sports/Education/Other)",
    "subcategory": "specific subcategory",
    "topics": ["list", "of", "main", "topics"],
    "tags": ["relevant", "hashtag", "style", "tags"],
    "people": ["mentioned", "people", "names"],
    "organizations": ["mentioned", "companies", "organizations"],
    "locations": ["mentioned", "places", "countries"],
    "technologies": ["mentioned", "technologies", "tools", "platforms"],
    "sentiment": "positive/negative/neutral",
    "sentiment_score": 0.0,
    "mood": "informative/urgent/casual/technical/analytical",
    "complexity_level": "beginner/intermediate/advanced",
    "key_points": ["main", "takeaway", "points"],
    "action_items": ["actionable", "items", "if", "any"],
    "questions_raised": ["questions", "the", "article", "raises"],
    "source_type": "news/blog/research/social/documentation/tutorial",
    "source_credibility": "high/medium/low"
}}"""

        response = openai_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are an expert content analyst."},
                {"role": "user", "content": analysis_prompt}
            ],
            max_tokens=800,
            temperature=0.3,
            response_format={"type": "json_object"}
        )
        
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        logger.error(f"AI analysis error: {str(e)}")
        return {}

def migrate_articles():
    """Migrate articles from old to new database with AI enhancement"""
    
    # Connect to both databases
    old_conn = sqlite3.connect('articles.db')
    old_conn.row_factory = sqlite3.Row
    new_conn = sqlite3.connect('articles_enhanced.db')
    
    try:
        # Get articles from old database
        old_cursor = old_conn.cursor()
        old_cursor.execute('SELECT * FROM articles')
        old_articles = old_cursor.fetchall()
        
        print(f"\n📚 Found {len(old_articles)} articles to migrate\n")
        
        new_cursor = new_conn.cursor()
        
        for article in old_articles:
            print(f"Processing: {article['title'][:50]}...")
            
            # Get AI analysis
            ai_analysis = {}
            if article['content']:
                print("  🧠 Running AI analysis...")
                ai_analysis = analyze_with_ai(
                    article['content'],
                    article['title'],
                    article['url']
                )
            
            # Insert into new database with AI enhancements
            new_cursor.execute('''
                INSERT OR IGNORE INTO articles (
                    user_id, url, url_hash, title, content, summary,
                    category, subcategory, topics, tags,
                    people, organizations, locations, technologies,
                    sentiment, sentiment_score, mood, complexity_level,
                    key_points, action_items, questions_raised,
                    reading_time, word_count, saved_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                article['user_id'],
                article['url'],
                article['url_hash'],
                article['title'],
                article['content'],
                ai_analysis.get('summary', article['summary']),
                ai_analysis.get('category', article['category']),
                ai_analysis.get('subcategory'),
                json.dumps(ai_analysis.get('topics', [])),
                json.dumps(ai_analysis.get('tags', [])),
                json.dumps(ai_analysis.get('people', [])),
                json.dumps(ai_analysis.get('organizations', [])),
                json.dumps(ai_analysis.get('locations', [])),
                json.dumps(ai_analysis.get('technologies', [])),
                ai_analysis.get('sentiment'),
                ai_analysis.get('sentiment_score', 0),
                ai_analysis.get('mood'),
                ai_analysis.get('complexity_level'),
                json.dumps(ai_analysis.get('key_points', [])),
                json.dumps(ai_analysis.get('action_items', [])),
                json.dumps(ai_analysis.get('questions_raised', [])),
                article['reading_time'],
                article['word_count'],
                article['saved_at']
            ))
            
            if ai_analysis:
                print(f"  ✅ Migrated with AI enhancements")
                print(f"     Category: {ai_analysis.get('category', 'N/A')}")
                print(f"     Sentiment: {ai_analysis.get('sentiment', 'N/A')}")
                print(f"     Topics: {', '.join(ai_analysis.get('topics', [])[:3])}")
            else:
                print(f"  ✅ Migrated (basic)")
        
        new_conn.commit()
        
        # Verify migration
        new_cursor.execute('SELECT COUNT(*) FROM articles')
        count = new_cursor.fetchone()[0]
        print(f"\n✅ Migration complete! {count} articles in enhanced database")
        
        # Show sample of migrated data
        new_cursor.execute('''
            SELECT title, category, sentiment, topics
            FROM articles
            LIMIT 5
        ''')
        
        print("\n📊 Sample of migrated articles:")
        for row in new_cursor.fetchall():
            print(f"  • {row[0][:40]}...")
            print(f"    Category: {row[1]}, Sentiment: {row[2]}")
            if row[3]:
                topics = json.loads(row[3])
                print(f"    Topics: {', '.join(topics[:3])}")
            print()
        
    finally:
        old_conn.close()
        new_conn.close()

if __name__ == "__main__":
    print("="*60)
    print("MIGRATING ARTICLES TO AI-ENHANCED DATABASE")
    print("="*60)
    migrate_articles()
    print("="*60)
    print("Migration complete! Your articles are now AI-enhanced.")
    print("Visit the dashboard to see the results!")
    print("="*60)