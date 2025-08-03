#!/usr/bin/env python3
"""Demo script to showcase 10x AI features in action"""

import asyncio
import json
import sqlite3
from datetime import datetime
from contextlib import closing

# Import our 10x modules
from advanced_ai_pipeline import AdvancedAIPipeline, ArticleIntelligence
from vision_intelligence import VisionAnalyzer, VisualContentGenerator

def get_articles_from_db():
    """Get articles from database"""
    conn = sqlite3.connect('articles_kanban.db')
    conn.row_factory = sqlite3.Row
    
    cursor = conn.cursor()
    cursor.execute('''
        SELECT id, url, title, summary, extracted_content, category
        FROM articles_kanban
        WHERE is_archived = 0
        LIMIT 5
    ''')
    
    articles = []
    for row in cursor.fetchall():
        articles.append({
            'id': row['id'],
            'url': row['url'],
            'title': row['title'],
            'content': row['extracted_content'] or row['summary'] or row['title'],
            'category': row['category'] or 'general'
        })
    
    conn.close()
    return articles

async def demonstrate_quantum_scoring():
    """Demonstrate Quantum Reading Scores"""
    print("\n" + "="*60)
    print("🧠 QUANTUM READING SCORES DEMO")
    print("="*60)
    
    pipeline = AdvancedAIPipeline()
    articles = get_articles_from_db()
    
    if not articles:
        print("No articles found in database!")
        return
    
    enhanced_articles = []
    
    for article in articles:
        print(f"\nProcessing: {article['title'][:50]}...")
        enhanced = await pipeline.process_article(article)
        enhanced_articles.append(enhanced)
        
        print(f"  📊 Quantum Score: {enhanced.quantum_score:.0f}/1000")
        print(f"  🧬 Knowledge Density: {enhanced.knowledge_density:.2%}")
        print(f"  🧠 Cognitive Load: {enhanced.cognitive_load:.2%}")
        print(f"  💡 Impact Factor: {enhanced.impact_factor:.2%}")
        print(f"  ⏰ Optimal Read Time: {enhanced.optimal_read_time}")
        
        if enhanced.key_insights:
            print(f"  💎 Key Insights: {len(enhanced.key_insights)} found")
        if enhanced.action_items:
            print(f"  ✅ Action Items: {len(enhanced.action_items)} detected")
    
    # Rank by quantum score
    print("\n" + "-"*60)
    print("📈 ARTICLES RANKED BY QUANTUM SCORE:")
    print("-"*60)
    
    enhanced_articles.sort(key=lambda x: x.quantum_score, reverse=True)
    
    for i, article in enumerate(enhanced_articles, 1):
        score_bar = "█" * int(article.quantum_score / 100)
        print(f"{i}. [{article.quantum_score:4.0f}] {score_bar} {article.title[:40]}")
    
    return enhanced_articles

async def demonstrate_real_time_insights():
    """Demonstrate real-time reading insights"""
    print("\n" + "="*60)
    print("⚡ REAL-TIME READING INSIGHTS DEMO")
    print("="*60)
    
    pipeline = AdvancedAIPipeline()
    
    # Simulate reading session
    print("\nSimulating reading session...")
    print("📖 Article: 'Advanced AI Systems'")
    print("\nReal-time metrics:")
    
    for i in range(5):
        await asyncio.sleep(1)
        
        # Simulate changing metrics
        scroll = i * 20
        speed = 200 + (i * 10)
        focus = 0.9 - (i * 0.1)
        comprehension = 0.8 - (i * 0.05)
        
        print(f"\n⏱️ Time: {i+1}s")
        print(f"  📍 Scroll Position: {scroll}%")
        print(f"  🏃 Reading Speed: {speed} WPM")
        print(f"  🎯 Focus Level: {focus:.1%}")
        print(f"  🧠 Comprehension: {comprehension:.1%}")
        
        # Generate insight
        if focus < 0.6:
            print("  💡 Insight: Focus dropping - consider a break")
        if speed > 250:
            print("  💡 Insight: Great reading pace!")
        if comprehension < 0.7:
            print("  💡 Insight: Complex section - slow down")

def demonstrate_visual_intelligence():
    """Demonstrate visual intelligence features"""
    print("\n" + "="*60)
    print("👁️ VISUAL INTELLIGENCE DEMO")
    print("="*60)
    
    analyzer = VisionAnalyzer()
    generator = VisualContentGenerator()
    
    # Simulate image analysis
    print("\nAnalyzing article images...")
    
    # Create a simple test image (white background)
    from PIL import Image
    import io
    
    # Create test image
    img = Image.new('RGB', (800, 600), color='white')
    img_bytes = io.BytesIO()
    img.save(img_bytes, format='PNG')
    img_data = img_bytes.getvalue()
    
    # Analyze
    visual_intel = analyzer.analyze_image(img_data)
    
    print(f"\n📸 Image Analysis Results:")
    print(f"  🎨 Dominant Colors: {', '.join(visual_intel.dominant_colors)}")
    print(f"  📊 Complexity Score: {visual_intel.complexity_score:.2f}/1.0")
    print(f"  😊 Visual Sentiment: {visual_intel.sentiment}")
    print(f"  🏷️ Auto Tags: {', '.join(visual_intel.tags[:5])}")
    print(f"  ⭐ Quality Score: {visual_intel.quality_score:.2f}/1.0")
    
    # Generate infographic data
    print("\n📊 Generating Infographic Data...")
    article_data = {
        'title': 'AI Revolution 2024',
        'content': 'AI has grown 300% this year. Important: Machine learning is key. 85% of companies use AI.',
        'category': 'technology'
    }
    
    infographic = generator.generate_infographic_data(article_data)
    
    print(f"  📈 Statistics Found: {len(infographic['statistics'])}")
    print(f"  🎨 Color Scheme: {infographic['color_scheme']['primary']}")
    print(f"  📐 Suggested Layout: {infographic['layout']}")
    
    if infographic['statistics']:
        print("\n  📊 Key Statistics:")
        for stat in infographic['statistics'][:3]:
            print(f"    • {stat['icon']} {stat['value']}")

async def demonstrate_knowledge_graph():
    """Demonstrate knowledge graph connections"""
    print("\n" + "="*60)
    print("🕸️ KNOWLEDGE GRAPH DEMO")
    print("="*60)
    
    pipeline = AdvancedAIPipeline()
    articles = get_articles_from_db()
    
    if len(articles) < 2:
        print("Need at least 2 articles for graph demo!")
        return
    
    print("\nBuilding knowledge graph...")
    
    # Process articles and add to graph
    for article in articles[:3]:
        enhanced = await pipeline.process_article(article)
        pipeline.knowledge_graph.add_article(enhanced)
    
    # Show connections
    print("\n🔗 Article Connections:")
    for node_id, node_data in pipeline.knowledge_graph.graph.items():
        if node_data['type'] == 'article':
            connections = node_data.get('connections', {})
            if connections:
                print(f"\n📄 {node_data['title'][:40]}")
                for connected_id, strength in connections.items():
                    connected = pipeline.knowledge_graph.graph[connected_id]
                    print(f"  ↔️ {connected['title'][:35]} (strength: {strength:.2f})")
    
    # Find learning path
    print("\n🎯 Learning Path to 'AI':")
    path = pipeline.knowledge_graph.find_learning_path(
        start_article=articles[0]['id'],
        goal_concept='ai'
    )
    
    if path:
        print(f"  Recommended reading order: {' → '.join(map(str, path))}")
    else:
        print("  No direct path found")

async def demonstrate_predictive_analytics():
    """Demonstrate predictive analytics"""
    print("\n" + "="*60)
    print("🔮 PREDICTIVE ANALYTICS DEMO")
    print("="*60)
    
    pipeline = AdvancedAIPipeline()
    articles = get_articles_from_db()
    
    if not articles:
        print("No articles found!")
        return
    
    # Process articles
    enhanced_articles = []
    for article in articles:
        enhanced = await pipeline.process_article(article)
        enhanced_articles.append(enhanced)
    
    # Generate analytics report
    report = pipeline.analytics.generate_insights_report(enhanced_articles)
    
    print("\n📊 Analytics Report:")
    print(f"  📚 Total Articles: {report['total_articles']}")
    print(f"  🎯 Avg Quantum Score: {report['quantum_metrics']['average_score']:.0f}")
    print(f"  🧠 Knowledge Density: {report['knowledge_metrics']['knowledge_density_avg']:.2%}")
    
    print("\n🏆 Top Concepts:")
    for concept, count in list(report['knowledge_metrics']['top_concepts'].items())[:5]:
        print(f"  • {concept}: {count} occurrences")
    
    print("\n🔮 Predictions:")
    print(f"  📖 Next Week Reading: {report['predictions']['next_week_reading']} articles")
    
    if report['predictions']['knowledge_gaps']:
        print(f"\n❓ Knowledge Gaps Identified:")
        for gap in report['predictions']['knowledge_gaps'][:3]:
            print(f"  • {gap}")
    
    if report['recommendations']:
        print(f"\n💡 Recommendations:")
        for rec in report['recommendations']:
            print(f"  • {rec}")

async def main():
    """Run all demonstrations"""
    print("\n" + "🚀"*30)
    print(" "*20 + "10X AI FEATURES DEMO")
    print("🚀"*30)
    
    print("\nThis demo will showcase:")
    print("1. Quantum Reading Scores")
    print("2. Real-time Insights")
    print("3. Visual Intelligence")
    print("4. Knowledge Graph")
    print("5. Predictive Analytics")
    
    # Run demos
    enhanced_articles = await demonstrate_quantum_scoring()
    await demonstrate_real_time_insights()
    demonstrate_visual_intelligence()
    await demonstrate_knowledge_graph()
    await demonstrate_predictive_analytics()
    
    print("\n" + "="*60)
    print("✅ DEMO COMPLETE!")
    print("="*60)
    print("\nTo use these features in your app:")
    print("1. Start the WebSocket server: python realtime_server.py")
    print("2. Open the dashboard: http://localhost:5003")
    print("3. Click on AI features buttons")
    print("\nCheck HOW_TO_USE_10X.md for detailed instructions!")

if __name__ == "__main__":
    asyncio.run(main())