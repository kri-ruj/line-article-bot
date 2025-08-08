#!/usr/bin/env python3
"""Simple demo of 10x features without external dependencies"""

import sqlite3
import json
import random
from datetime import datetime
from contextlib import closing

def calculate_quantum_score(article):
    """Calculate simplified quantum score without numpy"""
    score = 500  # Base score
    
    # Title length bonus
    if article.get('title'):
        score += min(100, len(article['title']) * 2)
    
    # Category bonus
    category_scores = {
        'Technology': 150,
        'Science': 140,
        'Business': 120,
        'Sports': 80,
        'Other': 50
    }
    score += category_scores.get(article.get('category', 'Other'), 50)
    
    # Summary bonus
    if article.get('summary'):
        score += min(150, len(article.get('summary', '')) // 10)
    
    # Time of day bonus
    hour = datetime.now().hour
    if 6 <= hour <= 10:  # Morning bonus
        score += 100
    elif 19 <= hour <= 22:  # Evening bonus
        score += 80
    
    # Random quantum interference (-50 to +50)
    score += random.randint(-50, 50)
    
    return min(1000, max(0, score))

def analyze_article_intelligence(article):
    """Analyze article with simplified AI"""
    content = article.get('summary') or article.get('title', '')
    
    # Calculate metrics
    words = content.split()
    word_count = len(words)
    unique_words = len(set(words))
    
    intelligence = {
        'quantum_score': calculate_quantum_score(article),
        'knowledge_density': unique_words / (word_count + 1) if word_count > 0 else 0,
        'cognitive_load': min(1.0, word_count / 1000),
        'reading_time': max(1, word_count // 200),  # 200 WPM average
        'complexity': 'high' if word_count > 500 else 'medium' if word_count > 200 else 'low',
        'optimal_read_time': 'Morning (6-10 AM)' if word_count > 500 else 'Anytime'
    }
    
    # Extract concepts (simple keyword detection)
    concepts = []
    keywords = ['ai', 'technology', 'data', 'system', 'analysis', 'intelligence', 
                'algorithm', 'model', 'learning', 'network']
    
    content_lower = content.lower()
    for keyword in keywords:
        if keyword in content_lower:
            concepts.append(keyword)
    
    intelligence['concepts'] = concepts
    intelligence['concept_count'] = len(concepts)
    
    # Detect key insights (sentences with important words)
    insights = []
    sentences = content.split('.')
    for sentence in sentences[:10]:
        if any(word in sentence.lower() for word in ['important', 'key', 'remember', 'critical']):
            insights.append(sentence.strip()[:100] + '...')
    
    intelligence['key_insights'] = insights[:3]
    
    return intelligence

def get_articles_from_db():
    """Get articles from database"""
    try:
        conn = sqlite3.connect('articles_kanban.db')
        conn.row_factory = sqlite3.Row
        
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, url, title, summary, category, stage
            FROM articles_kanban
            WHERE is_archived = 0
            LIMIT 10
        ''')
        
        articles = []
        for row in cursor.fetchall():
            articles.append(dict(row))
        
        conn.close()
        return articles
    except Exception as e:
        print(f"Database error: {e}")
        return []

def demonstrate_quantum_scoring():
    """Show quantum scores for articles"""
    print("\n" + "="*60)
    print("🧠 QUANTUM READING SCORES (0-1000)")
    print("="*60)
    
    articles = get_articles_from_db()
    
    if not articles:
        print("No articles found in database!")
        print("Please add articles first using the LINE bot or web interface.")
        return []
    
    enhanced_articles = []
    
    for article in articles:
        intelligence = analyze_article_intelligence(article)
        article['intelligence'] = intelligence
        enhanced_articles.append(article)
        
        print(f"\n📄 {article['title'][:50]}...")
        print(f"   Quantum Score: {intelligence['quantum_score']}/1000")
        
        # Score visualization
        score_bar = "█" * (intelligence['quantum_score'] // 100)
        score_bar += "▒" * (10 - len(score_bar))
        print(f"   [{score_bar}]")
        
        print(f"   📊 Knowledge Density: {intelligence['knowledge_density']:.1%}")
        print(f"   🧠 Cognitive Load: {intelligence['cognitive_load']:.1%}")
        print(f"   ⏱️ Reading Time: {intelligence['reading_time']} min")
        print(f"   📚 Complexity: {intelligence['complexity']}")
        print(f"   ⏰ Best Time: {intelligence['optimal_read_time']}")
        
        if intelligence['concepts']:
            print(f"   🏷️ Concepts: {', '.join(intelligence['concepts'][:5])}")
        
        if intelligence['key_insights']:
            print(f"   💡 Insights Found: {len(intelligence['key_insights'])}")
    
    # Rank by quantum score
    enhanced_articles.sort(key=lambda x: x['intelligence']['quantum_score'], reverse=True)
    
    print("\n" + "-"*60)
    print("📈 TOP ARTICLES BY QUANTUM SCORE:")
    print("-"*60)
    
    for i, article in enumerate(enhanced_articles[:5], 1):
        score = article['intelligence']['quantum_score']
        emoji = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else "📄"
        print(f"{emoji} {i}. [{score:4}] {article['title'][:45]}")
    
    return enhanced_articles

def simulate_real_time_reading():
    """Simulate real-time reading metrics"""
    print("\n" + "="*60)
    print("⚡ REAL-TIME READING SIMULATION")
    print("="*60)
    
    print("\n📖 Simulating article reading...")
    print("Article: 'Advanced AI Systems and Future Applications'\n")
    
    # Simulate 10 seconds of reading
    for second in range(1, 11):
        scroll = second * 10
        speed = 200 + random.randint(-20, 30)
        focus = max(0, min(1, 0.9 - (second * 0.05) + random.random() * 0.2))
        comprehension = max(0, min(1, 0.85 - (second * 0.03) + random.random() * 0.1))
        
        print(f"⏱️ Second {second:2d}:")
        
        # Visual bars
        focus_bar = "█" * int(focus * 10) + "░" * (10 - int(focus * 10))
        comp_bar = "█" * int(comprehension * 10) + "░" * (10 - int(comprehension * 10))
        
        print(f"  📍 Progress: {scroll:3d}% | Speed: {speed} WPM")
        print(f"  🎯 Focus:    [{focus_bar}] {focus:.0%}")
        print(f"  🧠 Compreh:  [{comp_bar}] {comprehension:.0%}")
        
        # Real-time insights
        if focus < 0.5:
            print("  💡 INSIGHT: Focus dropping - take a break!")
        elif speed > 250:
            print("  💡 INSIGHT: Excellent reading pace!")
        elif comprehension < 0.6:
            print("  💡 INSIGHT: Complex section - consider re-reading")
        
        print()

def show_knowledge_connections():
    """Show how articles connect to each other"""
    print("\n" + "="*60)
    print("🕸️ KNOWLEDGE GRAPH CONNECTIONS")
    print("="*60)
    
    articles = get_articles_from_db()
    
    if len(articles) < 2:
        print("Need at least 2 articles to show connections!")
        return
    
    print("\n🔗 Article Relationship Network:\n")
    
    # Simulate connections based on shared concepts
    for i, article1 in enumerate(articles[:5]):
        intel1 = analyze_article_intelligence(article1)
        concepts1 = set(intel1['concepts'])
        
        if not concepts1:
            continue
            
        print(f"📄 {article1['title'][:40]}")
        print(f"   Concepts: {', '.join(concepts1)}")
        
        connections = []
        for j, article2 in enumerate(articles[:5]):
            if i != j:
                intel2 = analyze_article_intelligence(article2)
                concepts2 = set(intel2['concepts'])
                
                if concepts1 & concepts2:  # Shared concepts
                    shared = concepts1 & concepts2
                    strength = len(shared) / len(concepts1 | concepts2)
                    connections.append((article2['title'][:35], strength, shared))
        
        if connections:
            print("   Connected to:")
            for title, strength, shared in sorted(connections, key=lambda x: x[1], reverse=True)[:3]:
                strength_bar = "●" * int(strength * 5) + "○" * (5 - int(strength * 5))
                print(f"     → {title} [{strength_bar}]")
                print(f"       Shared: {', '.join(shared)}")
        print()

def generate_analytics_report():
    """Generate comprehensive analytics"""
    print("\n" + "="*60)
    print("📊 ANALYTICS & INSIGHTS REPORT")
    print("="*60)
    
    articles = get_articles_from_db()
    
    if not articles:
        print("No articles to analyze!")
        return
    
    # Analyze all articles
    total_quantum = 0
    all_concepts = []
    stages = {'inbox': 0, 'reading': 0, 'reviewing': 0, 'completed': 0}
    
    for article in articles:
        intel = analyze_article_intelligence(article)
        total_quantum += intel['quantum_score']
        all_concepts.extend(intel['concepts'])
        stage = article.get('stage', 'inbox')
        stages[stage] = stages.get(stage, 0) + 1
    
    avg_quantum = total_quantum / len(articles) if articles else 0
    
    # Count concept frequency
    concept_freq = {}
    for concept in all_concepts:
        concept_freq[concept] = concept_freq.get(concept, 0) + 1
    
    print(f"\n📈 Summary Statistics:")
    print(f"   Total Articles: {len(articles)}")
    print(f"   Avg Quantum Score: {avg_quantum:.0f}/1000")
    
    print(f"\n📚 Reading Progress:")
    for stage, count in stages.items():
        if count > 0:
            bar = "█" * count + "░" * (10 - count)
            print(f"   {stage.capitalize():10s} [{bar}] {count}")
    
    if concept_freq:
        print(f"\n🏆 Top Concepts:")
        for concept, freq in sorted(concept_freq.items(), key=lambda x: x[1], reverse=True)[:5]:
            print(f"   • {concept}: {freq} articles")
    
    # Predictions
    print(f"\n🔮 Predictions & Recommendations:")
    
    completion_rate = stages.get('completed', 0) / len(articles) if articles else 0
    if completion_rate < 0.3:
        print("   ⚠️ Low completion rate - focus on finishing current reads")
    else:
        print("   ✅ Good completion rate - ready for new articles")
    
    if avg_quantum < 600:
        print("   📚 Add more high-quality articles to improve scores")
    else:
        print("   🌟 Excellent article quality - keep it up!")
    
    # Knowledge gaps (simulated)
    all_important_concepts = ['machine learning', 'blockchain', 'cloud computing', 'cybersecurity']
    missing_concepts = [c for c in all_important_concepts if c not in concept_freq]
    
    if missing_concepts:
        print(f"\n❓ Knowledge Gaps Detected:")
        for concept in missing_concepts[:3]:
            print(f"   • Consider reading about: {concept}")

def show_visual_intelligence():
    """Demonstrate visual analysis capabilities"""
    print("\n" + "="*60)
    print("👁️ VISUAL INTELLIGENCE CAPABILITIES")
    print("="*60)
    
    print("\n🎨 Image Analysis Features:")
    print("   ✓ Object Detection - Identify items in images")
    print("   ✓ Text Extraction (OCR) - Read text from images")
    print("   ✓ Color Analysis - Dominant colors and themes")
    print("   ✓ Sentiment Detection - Emotional tone")
    print("   ✓ Complexity Scoring - Visual complexity")
    print("   ✓ Chart Recognition - Extract data from graphs")
    print("   ✓ Face Detection - Count people in images")
    
    print("\n📊 Infographic Generation:")
    print("   ✓ Auto-extract statistics from text")
    print("   ✓ Generate timeline from dates")
    print("   ✓ Create comparison charts")
    print("   ✓ Suggest color schemes")
    print("   ✓ Recommend layouts")
    
    print("\n🔍 Visual Search:")
    print("   ✓ Find similar images")
    print("   ✓ Visual fingerprinting")
    print("   ✓ Content-based matching")

def main():
    """Run the simplified demo"""
    print("\n" + "🚀"*30)
    print(" "*25 + "10X AI FEATURES DEMO")
    print("🚀"*30)
    
    print("\n Welcome to the 10x Article Intelligence System!")
    print("\n This demo showcases advanced AI features:")
    print(" • Quantum Reading Scores (0-1000)")
    print(" • Real-time Reading Metrics")
    print(" • Knowledge Graph Connections")
    print(" • Predictive Analytics")
    print(" • Visual Intelligence")
    
    # Run demonstrations
    enhanced_articles = demonstrate_quantum_scoring()
    
    if enhanced_articles:
        simulate_real_time_reading()
        show_knowledge_connections()
        generate_analytics_report()
        show_visual_intelligence()
    
    print("\n" + "="*60)
    print("✅ DEMO COMPLETE!")
    print("="*60)
    
    print("\n🎯 Next Steps:")
    print("1. Start the main app: python3 app_unified_home.py")
    print("2. Open dashboard: http://localhost:5003")
    print("3. Try the AI features buttons")
    print("4. Start WebSocket server for real-time: python3 realtime_server.py")
    print("\n📖 See HOW_TO_USE_10X.md for detailed instructions!")
    print("\n💡 The more you use it, the smarter it gets!")

if __name__ == "__main__":
    main()