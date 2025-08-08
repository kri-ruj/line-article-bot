import requests
from bs4 import BeautifulSoup
from datetime import datetime
import re
import logging

logger = logging.getLogger(__name__)

class ArticleExtractor:
    def __init__(self):
        self.categories = {
            'AI/Tech': ['ai', 'artificial intelligence', 'machine learning', 'deep learning', 
                       'neural', 'algorithm', 'data science', 'tech', 'technology', 'software',
                       'hardware', 'computer', 'digital', 'cyber', 'automation', 'robot'],
            'Programming': ['python', 'javascript', 'java', 'code', 'coding', 'programming',
                          'developer', 'development', 'api', 'framework', 'backend', 'frontend',
                          'database', 'sql', 'react', 'node', 'git', 'debug', 'testing'],
            'Business': ['business', 'startup', 'entrepreneur', 'market', 'finance', 'investment',
                        'revenue', 'profit', 'strategy', 'management', 'leadership', 'growth',
                        'sales', 'marketing', 'customer', 'product', 'company'],
            'Design': ['design', 'ux', 'ui', 'user experience', 'interface', 'visual', 'graphic',
                      'prototype', 'wireframe', 'layout', 'typography', 'color', 'aesthetic'],
            'Science': ['science', 'research', 'study', 'experiment', 'hypothesis', 'theory',
                       'physics', 'chemistry', 'biology', 'mathematics', 'quantum', 'discovery'],
            'Health': ['health', 'medical', 'medicine', 'fitness', 'wellness', 'mental', 'physical',
                      'disease', 'treatment', 'therapy', 'doctor', 'patient', 'hospital'],
            'Education': ['education', 'learning', 'teaching', 'school', 'university', 'course',
                         'student', 'teacher', 'curriculum', 'knowledge', 'skill', 'training']
        }
    
    def extract(self, url):
        return self._extract_with_beautifulsoup(url)
    
    def _extract_with_beautifulsoup(self, url):
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            title = self._get_title(soup)
            author = self._get_author(soup)
            description = self._get_description(soup)
            text = self._get_article_text(soup)
            
            reading_time = self._calculate_reading_time(text)
            category = self._categorize_article(title, text, [])
            
            return {
                'url': url,
                'title': title,
                'author': author,
                'description': description[:500] if description else text[:500],
                'category': category,
                'reading_time': f"{reading_time} min",
                'keywords': '',
                'publish_date': '',
                'saved_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'status': 'Unread'
            }
            
        except Exception as e:
            logger.error(f"Error extracting article: {str(e)}")
            raise Exception(f"Could not extract article: {str(e)}")
    
    def _get_title(self, soup):
        title_tags = [
            soup.find('meta', property='og:title'),
            soup.find('meta', {'name': 'twitter:title'}),
            soup.find('title'),
            soup.find('h1')
        ]
        
        for tag in title_tags:
            if tag:
                if tag.name == 'meta':
                    return tag.get('content', '').strip()
                else:
                    return tag.get_text().strip()
        
        return 'Untitled Article'
    
    def _get_author(self, soup):
        author_tags = [
            soup.find('meta', {'name': 'author'}),
            soup.find('meta', property='article:author'),
            soup.find('span', {'class': re.compile('author', re.I)}),
            soup.find('div', {'class': re.compile('author', re.I)}),
            soup.find('a', {'rel': 'author'})
        ]
        
        for tag in author_tags:
            if tag:
                if tag.name == 'meta':
                    return tag.get('content', '').strip()
                else:
                    return tag.get_text().strip()
        
        return 'Unknown Author'
    
    def _get_description(self, soup):
        desc_tags = [
            soup.find('meta', property='og:description'),
            soup.find('meta', {'name': 'description'}),
            soup.find('meta', {'name': 'twitter:description'})
        ]
        
        for tag in desc_tags:
            if tag:
                return tag.get('content', '').strip()
        
        first_p = soup.find('p')
        if first_p:
            return first_p.get_text().strip()
        
        return ''
    
    def _get_article_text(self, soup):
        article_tags = soup.find_all(['article', 'main', 'div'], 
                                    {'class': re.compile('content|article|post', re.I)})
        
        if article_tags:
            paragraphs = article_tags[0].find_all('p')
        else:
            paragraphs = soup.find_all('p')
        
        text = ' '.join([p.get_text().strip() for p in paragraphs])
        return text
    
    def _calculate_reading_time(self, text):
        words = len(text.split())
        wpm = 200
        reading_time = max(1, round(words / wpm))
        return reading_time
    
    def _categorize_article(self, title, text, keywords):
        combined_text = f"{title} {text} {' '.join(keywords)}".lower()
        
        category_scores = {}
        for category, terms in self.categories.items():
            score = sum(1 for term in terms if term in combined_text)
            category_scores[category] = score
        
        if max(category_scores.values()) > 0:
            return max(category_scores, key=category_scores.get)
        
        return 'General'
    
    def _generate_summary(self, text):
        sentences = text.split('.')
        if len(sentences) > 3:
            return '. '.join(sentences[:3]) + '.'
        return text
    
    def _extract_title_fallback(self, url):
        domain = url.split('/')[2] if '/' in url else url
        return f"Article from {domain}"