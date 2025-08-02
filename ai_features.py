#!/usr/bin/env python3
"""Advanced AI Features for Article Intelligence Bot"""

import os
import json
import sqlite3
import numpy as np
from typing import List, Dict, Any, Tuple
from datetime import datetime, timedelta
import hashlib
from collections import Counter
import re
from contextlib import closing

# Text processing imports
try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
except ImportError:
    print("Installing required packages...")
    import subprocess
    subprocess.check_call(['pip', 'install', 'scikit-learn'])
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity

def get_db(db_path='articles_kanban.db'):
    """Get database connection"""
    conn = sqlite3.connect(db_path, timeout=30.0, isolation_level=None)
    conn.execute('PRAGMA journal_mode=WAL')
    conn.row_factory = sqlite3.Row
    return conn

class AIFeatures:
    """Advanced AI features for article intelligence"""
    
    def __init__(self, db_path='articles_kanban.db'):
        self.db_path = db_path
        self.vectorizer = TfidfVectorizer(max_features=100, stop_words='english')
        
    def get_article_recommendations(self, article_id: int, limit: int = 5) -> List[Dict]:
        """Get smart recommendations based on article similarity"""
        try:
            with closing(get_db(self.db_path)) as conn:
                cursor = conn.cursor()
                
                # Get current article
                cursor.execute('''
                    SELECT id, title, summary, topics, category
                    FROM articles_kanban
                    WHERE id = ?
                ''', (article_id,))
                current_article = cursor.fetchone()
                
                if not current_article:
                    return []
                
                # Get all other articles
                cursor.execute('''
                    SELECT id, title, summary, topics, category
                    FROM articles_kanban
                    WHERE id != ? AND is_archived = 0
                ''')
                other_articles = cursor.fetchall()
                
                if not other_articles:
                    return []
                
                # Create text representations
                current_text = f"{current_article['title']} {current_article['summary'] or ''} {current_article['topics'] or ''}"
                
                article_texts = []
                article_data = []
                for article in other_articles:
                    text = f"{article['title']} {article['summary'] or ''} {article['topics'] or ''}"
                    article_texts.append(text)
                    article_data.append({
                        'id': article['id'],
                        'title': article['title'],
                        'category': article['category'],
                        'similarity_score': 0
                    })
                
                # Calculate similarity
                all_texts = [current_text] + article_texts
                tfidf_matrix = self.vectorizer.fit_transform(all_texts)
                similarities = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:])[0]
                
                # Add similarity scores
                for i, score in enumerate(similarities):
                    article_data[i]['similarity_score'] = float(score)
                
                # Sort by similarity and return top N
                recommendations = sorted(article_data, key=lambda x: x['similarity_score'], reverse=True)[:limit]
                
                # Add recommendation reasons
                for rec in recommendations:
                    if rec['similarity_score'] > 0.7:
                        rec['reason'] = "Highly similar content"
                    elif rec['similarity_score'] > 0.4:
                        rec['reason'] = "Related topic"
                    elif rec['category'] == current_article['category']:
                        rec['reason'] = "Same category"
                    else:
                        rec['reason'] = "You might also like"
                
                return recommendations
                
        except Exception as e:
            print(f"Error getting recommendations: {e}")
            return []
    
    def generate_auto_tags(self, text: str, title: str = "") -> List[str]:
        """Generate relevant hashtags for an article"""
        try:
            combined_text = f"{title} {text}".lower()
            
            # Remove special characters and URLs
            combined_text = re.sub(r'http\S+', '', combined_text)
            combined_text = re.sub(r'[^a-z0-9\s]', ' ', combined_text)
            
            # Extract words
            words = combined_text.split()
            
            # Filter short words and common words
            stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 
                         'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'were', 'been',
                         'be', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
                         'should', 'may', 'might', 'must', 'can', 'shall', 'it', 'this', 'that'}
            
            meaningful_words = [w for w in words if len(w) > 3 and w not in stop_words]
            
            # Count word frequency
            word_freq = Counter(meaningful_words)
            
            # Get top words as tags
            top_words = word_freq.most_common(10)
            
            # Generate hashtags
            hashtags = []
            for word, freq in top_words:
                if freq > 1:  # Word appears more than once
                    hashtags.append(f"#{word}")
            
            # Add special tags based on patterns
            if 'python' in combined_text or 'javascript' in combined_text or 'code' in combined_text:
                hashtags.append('#programming')
            if 'ai' in combined_text or 'machine learning' in combined_text:
                hashtags.append('#AI')
            if 'tutorial' in combined_text or 'how to' in combined_text:
                hashtags.append('#tutorial')
            if 'news' in combined_text or 'breaking' in combined_text:
                hashtags.append('#news')
            
            # Remove duplicates and limit to 7 tags
            hashtags = list(dict.fromkeys(hashtags))[:7]
            
            return hashtags
            
        except Exception as e:
            print(f"Error generating tags: {e}")
            return []
    
    def detect_similar_articles(self, threshold: float = 0.8) -> List[Tuple[Dict, Dict, float]]:
        """Detect duplicate or very similar articles in the database"""
        try:
            with closing(get_db(self.db_path)) as conn:
                cursor = conn.cursor()
                
                # Get all articles
                cursor.execute('''
                    SELECT id, url, title, summary, topics
                    FROM articles_kanban
                    WHERE is_archived = 0
                ''')
                articles = cursor.fetchall()
                
                if len(articles) < 2:
                    return []
                
                # Create text representations
                article_texts = []
                article_data = []
                for article in articles:
                    text = f"{article['title']} {article['summary'] or ''} {article['topics'] or ''}"
                    article_texts.append(text)
                    article_data.append({
                        'id': article['id'],
                        'title': article['title'],
                        'url': article['url']
                    })
                
                # Calculate similarity matrix
                tfidf_matrix = self.vectorizer.fit_transform(article_texts)
                similarity_matrix = cosine_similarity(tfidf_matrix)
                
                # Find similar pairs
                similar_pairs = []
                for i in range(len(articles)):
                    for j in range(i + 1, len(articles)):
                        similarity = similarity_matrix[i][j]
                        if similarity >= threshold:
                            similar_pairs.append((
                                article_data[i],
                                article_data[j],
                                float(similarity)
                            ))
                
                # Sort by similarity score
                similar_pairs.sort(key=lambda x: x[2], reverse=True)
                
                return similar_pairs
                
        except Exception as e:
            print(f"Error detecting similar articles: {e}")
            return []
    
    def calculate_priority_score(self, article: Dict) -> float:
        """Calculate smart priority score for an article"""
        try:
            score = 50.0  # Base score
            
            # Quality score weight (0-100)
            quality = article.get('quality_score', 0)
            score += quality * 0.3
            
            # Reading time factor (prefer shorter for quick wins)
            reading_time = article.get('reading_time', 10)
            if reading_time <= 5:
                score += 20  # Quick read bonus
            elif reading_time > 20:
                score -= 10  # Long read penalty
            
            # Category priorities (customize based on user preference)
            category = article.get('category', 'Other')
            category_weights = {
                'Technology': 15,
                'Business': 10,
                'Science': 12,
                'Programming': 20,
                'AI': 25,
                'Tutorial': 18
            }
            score += category_weights.get(category, 5)
            
            # Stage factor
            stage = article.get('stage', 'inbox')
            if stage == 'reading':
                score += 30  # Already started, should finish
            elif stage == 'reviewing':
                score += 20  # Almost done
            
            # Recency factor (newer articles get slight boost)
            added_date = article.get('added_date')
            if added_date:
                try:
                    date_added = datetime.fromisoformat(added_date)
                    days_old = (datetime.now() - date_added).days
                    if days_old < 1:
                        score += 15  # Very fresh
                    elif days_old < 7:
                        score += 10  # Recent
                    elif days_old > 30:
                        score -= 5  # Getting stale
                except:
                    pass
            
            # Normalize score to 0-100
            score = max(0, min(100, score))
            
            return score
            
        except Exception as e:
            print(f"Error calculating priority: {e}")
            return 50.0
    
    def generate_study_questions(self, article_text: str, title: str = "") -> List[Dict]:
        """Generate comprehension questions for an article"""
        try:
            # Use OpenAI if available
            api_key = os.getenv('OPENAI_API_KEY')
            if api_key:
                from openai import OpenAI
                client = OpenAI(api_key=api_key)
                
                prompt = f"""Generate 5 comprehension questions for this article:
                Title: {title}
                Content: {article_text[:1500]}
                
                Format as JSON array with 'question', 'type' (multiple_choice/short_answer/true_false), and 'difficulty' (easy/medium/hard).
                For multiple choice, include 'options' array and 'correct_answer'."""
                
                response = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "You are an educational assessment expert."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.7,
                    max_tokens=500
                )
                
                questions = json.loads(response.choices[0].message.content)
                return questions
            else:
                # Fallback to basic questions
                return [
                    {
                        "question": f"What is the main topic of '{title}'?",
                        "type": "short_answer",
                        "difficulty": "easy"
                    },
                    {
                        "question": "What are the key points discussed in this article?",
                        "type": "short_answer",
                        "difficulty": "medium"
                    },
                    {
                        "question": "How would you apply the concepts from this article?",
                        "type": "short_answer",
                        "difficulty": "hard"
                    }
                ]
                
        except Exception as e:
            print(f"Error generating questions: {e}")
            return []
    
    def generate_study_notes(self, article: Dict) -> str:
        """Generate formatted study notes from an article"""
        try:
            notes = f"""# 📚 Study Notes: {article.get('title', 'Article')}

## 📋 Quick Facts
- **Category**: {article.get('category', 'General')}
- **Difficulty**: {article.get('difficulty', 'Medium')}
- **Reading Time**: {article.get('reading_time', 'N/A')} minutes
- **Quality Score**: {article.get('quality_score', 0)}/100

## 🎯 Key Insights
{article.get('key_insights', '- No insights available')}

## 📝 Summary
{article.get('summary', 'No summary available')}

## 🏷️ Topics
{article.get('topics', 'No topics identified')}

## 💡 Action Items
{article.get('action_items', '- Review the article for action items')}

## 🔗 Related Concepts
{article.get('related_concepts', 'Explore related articles in your reading list')}

## 📌 Personal Notes
_Add your own notes here_

---
*Generated on {datetime.now().strftime('%Y-%m-%d %H:%M')}*
"""
            return notes
            
        except Exception as e:
            print(f"Error generating study notes: {e}")
            return "Error generating notes"
    
    def get_reading_analytics(self) -> Dict:
        """Get comprehensive reading analytics"""
        try:
            with closing(get_db(self.db_path)) as conn:
                cursor = conn.cursor()
                
                # Total articles by stage
                cursor.execute('''
                    SELECT stage, COUNT(*) as count
                    FROM articles_kanban
                    WHERE is_archived = 0
                    GROUP BY stage
                ''')
                stage_counts = {row['stage']: row['count'] for row in cursor.fetchall()}
                
                # Articles by category
                cursor.execute('''
                    SELECT category, COUNT(*) as count
                    FROM articles_kanban
                    WHERE is_archived = 0 AND category IS NOT NULL
                    GROUP BY category
                    ORDER BY count DESC
                ''')
                category_distribution = {row['category']: row['count'] for row in cursor.fetchall()}
                
                # Reading velocity (articles completed per week)
                cursor.execute('''
                    SELECT COUNT(*) as completed
                    FROM articles_kanban
                    WHERE stage = 'completed'
                    AND stage_updated >= datetime('now', '-7 days')
                ''')
                weekly_completed = cursor.fetchone()['completed']
                
                # Average reading time
                cursor.execute('''
                    SELECT AVG(reading_time) as avg_time
                    FROM articles_kanban
                    WHERE reading_time > 0
                ''')
                avg_reading_time = cursor.fetchone()['avg_time'] or 0
                
                # Quality score distribution
                cursor.execute('''
                    SELECT 
                        CASE 
                            WHEN quality_score >= 80 THEN 'High'
                            WHEN quality_score >= 60 THEN 'Medium'
                            ELSE 'Low'
                        END as quality_tier,
                        COUNT(*) as count
                    FROM articles_kanban
                    WHERE quality_score > 0
                    GROUP BY quality_tier
                ''')
                quality_distribution = {row['quality_tier']: row['count'] for row in cursor.fetchall()}
                
                analytics = {
                    'total_articles': sum(stage_counts.values()),
                    'stage_distribution': stage_counts,
                    'category_distribution': category_distribution,
                    'weekly_velocity': weekly_completed,
                    'avg_reading_time': round(avg_reading_time, 1),
                    'quality_distribution': quality_distribution,
                    'completion_rate': round(stage_counts.get('completed', 0) / max(sum(stage_counts.values()), 1) * 100, 1)
                }
                
                return analytics
                
        except Exception as e:
            print(f"Error getting analytics: {e}")
            return {}

# Initialize AI features
ai_features = AIFeatures()