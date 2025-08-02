#!/usr/bin/env python3
"""Generate a comprehensive report of the data structure and collected information"""

import sqlite3
import json
from contextlib import closing
import pandas as pd
from datetime import datetime
from tabulate import tabulate

def get_db():
    """Get database connection"""
    conn = sqlite3.connect('articles_enhanced.db', timeout=30.0)
    conn.row_factory = sqlite3.Row
    return conn

def analyze_current_data():
    """Analyze current data structure and content"""
    
    print("="*80)
    print("📊 ARTICLE INTELLIGENCE SYSTEM - DATA STRUCTURE REPORT")
    print("="*80)
    print(f"\nGenerated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    with closing(get_db()) as conn:
        cursor = conn.cursor()
        
        # 1. DATABASE SCHEMA
        print("\n" + "="*60)
        print("1️⃣ CURRENT DATA STRUCTURE")
        print("="*60)
        
        cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='articles'")
        schema = cursor.fetchone()
        if schema:
            print("\n📋 Articles Table Structure:")
            print("-"*40)
            
            # Parse schema to show fields
            schema_lines = schema['sql'].split('\n')
            fields = []
            for line in schema_lines:
                line = line.strip()
                if line and not line.startswith('CREATE') and not line.startswith(')'):
                    if '--' in line:
                        parts = line.split('--')
                        field = parts[0].strip().rstrip(',')
                        comment = parts[1].strip() if len(parts) > 1 else ''
                        if field and not field.startswith('INDEX'):
                            fields.append([field.split()[0], comment])
            
            print(tabulate(fields, headers=['Field Name', 'Description'], tablefmt='grid'))
        
        # 2. DATA STATISTICS
        print("\n" + "="*60)
        print("2️⃣ DATA COLLECTION STATISTICS")
        print("="*60)
        
        # Total articles
        cursor.execute("SELECT COUNT(*) as total FROM articles")
        total = cursor.fetchone()['total']
        print(f"\n📚 Total Articles: {total}")
        
        if total > 0:
            # Articles with AI analysis
            cursor.execute("SELECT COUNT(*) as count FROM articles WHERE category IS NOT NULL")
            ai_analyzed = cursor.fetchone()['count']
            print(f"🧠 AI Analyzed: {ai_analyzed} ({ai_analyzed/total*100:.1f}%)")
            
            # Category distribution
            print("\n📂 Category Distribution:")
            cursor.execute("""
                SELECT category, COUNT(*) as count 
                FROM articles 
                WHERE category IS NOT NULL 
                GROUP BY category 
                ORDER BY count DESC
            """)
            categories = cursor.fetchall()
            if categories:
                cat_data = [[cat['category'], cat['count']] for cat in categories]
                print(tabulate(cat_data, headers=['Category', 'Count'], tablefmt='simple'))
            
            # 3. AI CLASSIFICATION DATA
            print("\n" + "="*60)
            print("3️⃣ AI CLASSIFICATION DETAILS")
            print("="*60)
            
            # Sample article with full data
            cursor.execute("""
                SELECT * FROM articles 
                WHERE category IS NOT NULL 
                ORDER BY saved_at DESC 
                LIMIT 1
            """)
            sample = cursor.fetchone()
            
            if sample:
                print("\n📄 Sample Article Data Structure:")
                print("-"*40)
                
                data_collected = {
                    "🔗 URL Information": {
                        "URL": sample['url'],
                        "URL Hash": sample['url_hash'][:10] + "...",
                        "Title": sample['title'][:50] + "..." if sample['title'] else "N/A"
                    },
                    "📊 AI Classification": {
                        "Category": sample['category'],
                        "Subcategory": sample['subcategory'],
                        "Topics": json.loads(sample['topics']) if sample['topics'] else [],
                        "Tags": json.loads(sample['tags']) if sample['tags'] else []
                    },
                    "👥 Entity Extraction": {
                        "People": json.loads(sample['people']) if sample['people'] else [],
                        "Organizations": json.loads(sample['organizations']) if sample['organizations'] else [],
                        "Locations": json.loads(sample['locations']) if sample['locations'] else [],
                        "Technologies": json.loads(sample['technologies']) if sample['technologies'] else []
                    },
                    "😊 Sentiment Analysis": {
                        "Sentiment": sample['sentiment'],
                        "Score": sample['sentiment_score'],
                        "Mood": sample['mood'],
                        "Complexity": sample['complexity_level']
                    },
                    "📝 Content Analysis": {
                        "Summary": sample['summary'][:100] + "..." if sample['summary'] else "N/A",
                        "Key Points": json.loads(sample['key_points']) if sample['key_points'] else [],
                        "Action Items": json.loads(sample['action_items']) if sample['action_items'] else [],
                        "Questions": json.loads(sample['questions_raised']) if sample['questions_raised'] else []
                    },
                    "📈 Metrics": {
                        "Word Count": sample['word_count'],
                        "Reading Time": f"{sample['reading_time']} minutes",
                        "Saved At": sample['saved_at']
                    }
                }
                
                for section, data in data_collected.items():
                    print(f"\n{section}:")
                    for key, value in data.items():
                        if isinstance(value, list):
                            if value:
                                print(f"  • {key}: {', '.join(str(v) for v in value[:3])}")
                                if len(value) > 3:
                                    print(f"    ... and {len(value)-3} more")
                            else:
                                print(f"  • {key}: None")
                        else:
                            print(f"  • {key}: {value}")
            
            # 4. DATA COMPLETENESS
            print("\n" + "="*60)
            print("4️⃣ DATA COMPLETENESS ANALYSIS")
            print("="*60)
            
            fields_to_check = [
                ('summary', 'Summary'),
                ('category', 'Category'),
                ('sentiment', 'Sentiment'),
                ('topics', 'Topics'),
                ('people', 'People Entities'),
                ('organizations', 'Org Entities'),
                ('technologies', 'Tech Entities'),
                ('key_points', 'Key Points')
            ]
            
            completeness_data = []
            for field, name in fields_to_check:
                cursor.execute(f"SELECT COUNT(*) as count FROM articles WHERE {field} IS NOT NULL AND {field} != ''")
                filled = cursor.fetchone()['count']
                percentage = (filled/total*100) if total > 0 else 0
                completeness_data.append([name, filled, f"{percentage:.1f}%"])
            
            print("\n" + tabulate(completeness_data, headers=['Field', 'Filled', 'Coverage'], tablefmt='grid'))
            
            # 5. INSIGHTS AND PATTERNS
            print("\n" + "="*60)
            print("5️⃣ DISCOVERED INSIGHTS")
            print("="*60)
            
            # Check insights table
            cursor.execute("SELECT COUNT(*) as count FROM insights WHERE is_dismissed = 0")
            insights_count = cursor.fetchone()['count']
            print(f"\n💡 Active Insights: {insights_count}")
            
            if insights_count > 0:
                cursor.execute("""
                    SELECT insight_type, title, description, importance_score 
                    FROM insights 
                    WHERE is_dismissed = 0 
                    ORDER BY importance_score DESC 
                    LIMIT 5
                """)
                insights = cursor.fetchall()
                print("\nTop Insights:")
                for i, insight in enumerate(insights, 1):
                    print(f"\n{i}. {insight['title']} (Importance: {insight['importance_score']*100:.0f}%)")
                    print(f"   Type: {insight['insight_type']}")
                    print(f"   {insight['description']}")
            
            # 6. RECOMMENDATIONS
            print("\n" + "="*60)
            print("6️⃣ RECOMMENDATIONS FOR BETTER DATA")
            print("="*60)
            
            recommendations = []
            
            if ai_analyzed < total:
                recommendations.append("🔄 Run AI analysis on remaining articles")
            
            if not categories or len(categories) < 3:
                recommendations.append("📚 Collect more diverse content for better classification")
            
            cursor.execute("SELECT COUNT(DISTINCT json_extract(value, '$')) as tech_count FROM articles, json_each(technologies) WHERE technologies IS NOT NULL")
            tech_diversity = cursor.fetchone()
            if not tech_diversity or tech_diversity['tech_count'] < 10:
                recommendations.append("💻 Collect more technology-focused articles")
            
            cursor.execute("SELECT AVG(word_count) as avg_words FROM articles WHERE word_count > 0")
            avg_words = cursor.fetchone()['avg_words']
            if avg_words and avg_words < 500:
                recommendations.append("📝 Consider collecting longer, more detailed articles")
            
            if recommendations:
                print("\n🎯 To improve data quality:")
                for rec in recommendations:
                    print(f"  • {rec}")
            else:
                print("\n✅ Data collection is comprehensive!")

def show_enhanced_structure():
    """Show the enhanced structure we can implement"""
    
    print("\n" + "="*80)
    print("🚀 PROPOSED ENHANCED DATA STRUCTURE")
    print("="*80)
    
    enhanced_fields = {
        "🌐 Website Information": [
            "domain - Website domain (e.g., github.com)",
            "subdomain - Specific subdomain",
            "website_type - news/blog/docs/forum/ecommerce",
            "cms_detected - WordPress/Medium/Ghost/custom",
            "ssl_enabled - HTTPS availability",
            "response_time_ms - Page load time",
            "page_size_kb - Total page size"
        ],
        "📰 Content Metadata": [
            "meta_description - SEO description",
            "meta_keywords - SEO keywords",
            "og_title - Open Graph title",
            "og_image - Preview image",
            "canonical_url - Canonical URL",
            "author_bio - Author information",
            "published_date - Original publication date"
        ],
        "🔍 Enhanced AI Analysis": [
            "industry - Industry sector classification",
            "products - Products mentioned",
            "events - Events referenced",
            "dates_mentioned - Important dates",
            "predictions - Future predictions made",
            "claims - Claims to fact-check",
            "readability_score - Flesch reading ease"
        ],
        "📊 Engagement Metrics": [
            "social_shares - Share counts by platform",
            "comments_count - Number of comments",
            "likes_count - Likes/upvotes",
            "user_engagement_score - Calculated score"
        ],
        "🔗 Advanced Relationships": [
            "referenced_by - Articles citing this",
            "knowledge_graph - Semantic connections",
            "content_patterns - Detected patterns",
            "website_profile - Domain-level insights"
        ]
    }
    
    print("\nAdditional data fields to capture:")
    for category, fields in enhanced_fields.items():
        print(f"\n{category}:")
        for field in fields:
            print(f"  • {field}")
    
    print("\n" + "="*60)
    print("💾 DATA EXPORT OPTIONS")
    print("="*60)
    
    print("\nAvailable export formats:")
    print("  • CSV - Spreadsheet compatible")
    print("  • JSON - Structured data with nested fields")
    print("  • Parquet - Efficient columnar storage")
    print("  • SQL - Database backup")
    print("  • Markdown - Human-readable reports")

if __name__ == "__main__":
    try:
        analyze_current_data()
        show_enhanced_structure()
        
        print("\n" + "="*80)
        print("✅ Report generated successfully!")
        print("="*80)
        
    except Exception as e:
        print(f"\n❌ Error generating report: {str(e)}")
        import traceback
        traceback.print_exc()