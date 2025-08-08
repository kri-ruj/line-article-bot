#!/usr/bin/env python3
"""Export current data structure and create comprehensive CSV/JSON exports"""

import sqlite3
import json
import csv
from contextlib import closing
from datetime import datetime
import pandas as pd

def get_db():
    """Get database connection"""
    conn = sqlite3.connect('articles_enhanced.db', timeout=30.0)
    conn.row_factory = sqlite3.Row
    return conn

def export_data_structure():
    """Export all data in structured format"""
    
    print("="*80)
    print("📊 COMPREHENSIVE DATA EXPORT")
    print("="*80)
    print(f"\nTimestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    with closing(get_db()) as conn:
        
        # 1. Export to DataFrame for analysis
        query = """
        SELECT 
            id,
            user_id,
            url,
            title,
            summary,
            category,
            subcategory,
            sentiment,
            sentiment_score,
            mood,
            complexity_level,
            reading_time,
            word_count,
            saved_at,
            source_credibility,
            source_type,
            topics,
            tags,
            people,
            organizations,
            locations,
            technologies,
            key_points,
            action_items,
            questions_raised
        FROM articles
        """
        
        df = pd.read_sql_query(query, conn)
        
        # 2. Process JSON fields for better structure
        json_fields = ['topics', 'tags', 'people', 'organizations', 'locations', 
                      'technologies', 'key_points', 'action_items', 'questions_raised']
        
        for field in json_fields:
            df[field] = df[field].apply(lambda x: json.loads(x) if x else [])
        
        # 3. Create structured export
        structured_data = []
        for _, row in df.iterrows():
            article = {
                "📋 Basic Information": {
                    "ID": row['id'],
                    "URL": row['url'],
                    "Title": row['title'] if row['title'] else "Untitled",
                    "Saved At": str(row['saved_at'])
                },
                "📊 AI Classification": {
                    "Category": row['category'],
                    "Subcategory": row['subcategory'],
                    "Topics": row['topics'],
                    "Tags": row['tags']
                },
                "😊 Sentiment Analysis": {
                    "Sentiment": row['sentiment'],
                    "Score": row['sentiment_score'],
                    "Mood": row['mood'],
                    "Complexity": row['complexity_level']
                },
                "👥 Entities": {
                    "People": row['people'],
                    "Organizations": row['organizations'],
                    "Locations": row['locations'],
                    "Technologies": row['technologies']
                },
                "📝 Content Analysis": {
                    "Summary": row['summary'],
                    "Key Points": row['key_points'],
                    "Action Items": row['action_items'],
                    "Questions": row['questions_raised']
                },
                "📈 Metrics": {
                    "Word Count": row['word_count'],
                    "Reading Time (min)": row['reading_time'],
                    "Source Type": row['source_type'],
                    "Source Credibility": row['source_credibility']
                }
            }
            structured_data.append(article)
        
        # 4. Save as JSON
        with open('data_export.json', 'w', encoding='utf-8') as f:
            json.dump(structured_data, f, indent=2, ensure_ascii=False)
        print("✅ Exported to data_export.json")
        
        # 5. Save as CSV (flattened)
        csv_data = []
        for _, row in df.iterrows():
            csv_row = {
                'id': row['id'],
                'url': row['url'],
                'title': row['title'],
                'category': row['category'],
                'subcategory': row['subcategory'],
                'sentiment': row['sentiment'],
                'sentiment_score': row['sentiment_score'],
                'mood': row['mood'],
                'complexity': row['complexity_level'],
                'topics_count': len(row['topics']),
                'topics': ', '.join(row['topics'][:3]) if row['topics'] else '',
                'people': ', '.join(row['people'][:3]) if row['people'] else '',
                'organizations': ', '.join(row['organizations'][:3]) if row['organizations'] else '',
                'technologies': ', '.join(row['technologies'][:3]) if row['technologies'] else '',
                'key_points_count': len(row['key_points']),
                'word_count': row['word_count'],
                'reading_time': row['reading_time'],
                'saved_at': row['saved_at']
            }
            csv_data.append(csv_row)
        
        df_csv = pd.DataFrame(csv_data)
        df_csv.to_csv('data_export.csv', index=False, encoding='utf-8')
        print("✅ Exported to data_export.csv")
        
        # 6. Create summary statistics
        print("\n" + "="*60)
        print("📊 DATA SUMMARY")
        print("="*60)
        
        print(f"\nTotal Articles: {len(df)}")
        print(f"Date Range: {df['saved_at'].min()} to {df['saved_at'].max()}")
        
        print("\n📂 Categories:")
        category_counts = df['category'].value_counts()
        for cat, count in category_counts.items():
            print(f"  • {cat}: {count} articles")
        
        print("\n😊 Sentiment Distribution:")
        sentiment_counts = df['sentiment'].value_counts()
        for sent, count in sentiment_counts.items():
            if sent:
                print(f"  • {sent}: {count} articles")
        
        print("\n📈 Content Metrics:")
        print(f"  • Average Word Count: {df['word_count'].mean():.0f}")
        print(f"  • Average Reading Time: {df['reading_time'].mean():.0f} minutes")
        print(f"  • Total Words Analyzed: {df['word_count'].sum():,}")
        
        # 7. Create enhanced structure documentation
        print("\n" + "="*60)
        print("🎯 RECOMMENDED DATA STRUCTURE")
        print("="*60)
        
        structure = {
            "Core Fields": [
                "id: Unique identifier",
                "url: Article URL",
                "domain: Extract from URL (e.g., github.com)",
                "title: Article title",
                "saved_at: Timestamp when saved",
                "published_date: Original publication date"
            ],
            "AI Classification": [
                "category: Main category",
                "subcategory: Detailed subcategory",
                "industry: Industry sector",
                "topics: Array of main topics",
                "tags: Auto-generated tags",
                "keywords: Extracted keywords"
            ],
            "Entity Extraction": [
                "people: Names with roles",
                "organizations: Companies/orgs with types",
                "locations: Places with geo data",
                "technologies: Tech with versions",
                "products: Products mentioned",
                "events: Events with dates"
            ],
            "Content Analysis": [
                "summary: AI-generated summary",
                "sentiment: positive/negative/neutral",
                "sentiment_score: -1 to 1",
                "mood: informative/urgent/casual/technical",
                "complexity_level: beginner/intermediate/advanced",
                "readability_score: Flesch score"
            ],
            "Insights": [
                "key_points: Main takeaways",
                "action_items: Actionable items",
                "questions_raised: Questions to explore",
                "predictions: Future predictions",
                "claims: Claims to verify"
            ],
            "Metrics": [
                "word_count: Total words",
                "sentence_count: Total sentences",
                "reading_time: Minutes to read",
                "unique_words: Vocabulary diversity",
                "engagement_score: Calculated engagement"
            ],
            "Website Info": [
                "website_type: news/blog/docs/forum",
                "cms_detected: WordPress/Medium/etc",
                "ssl_enabled: HTTPS availability",
                "response_time_ms: Load time",
                "page_size_kb: Page size"
            ],
            "Source Credibility": [
                "source_credibility: high/medium/low",
                "source_type: news/blog/research/social",
                "author: Article author",
                "author_bio: Author description",
                "domain_trust_score: 0-100"
            ]
        }
        
        for category, fields in structure.items():
            print(f"\n{category}:")
            for field in fields:
                print(f"  • {field}")
        
        # 8. Export structure as markdown
        with open('data_structure.md', 'w') as f:
            f.write("# Article Intelligence System - Data Structure\n\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            f.write("## Current Data Statistics\n\n")
            f.write(f"- Total Articles: {len(df)}\n")
            f.write(f"- Categories: {len(category_counts)}\n")
            f.write(f"- Total Words Analyzed: {df['word_count'].sum():,}\n\n")
            
            f.write("## Data Fields\n\n")
            for category, fields in structure.items():
                f.write(f"### {category}\n\n")
                for field in fields:
                    f.write(f"- {field}\n")
                f.write("\n")
        
        print("\n✅ Exported to data_structure.md")
        
        print("\n" + "="*60)
        print("📁 EXPORTED FILES:")
        print("="*60)
        print("  1. data_export.json - Complete structured data")
        print("  2. data_export.csv - Spreadsheet-friendly format")
        print("  3. data_structure.md - Documentation")

if __name__ == "__main__":
    try:
        export_data_structure()
        print("\n✅ All exports completed successfully!")
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()