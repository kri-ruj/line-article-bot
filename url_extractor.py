#!/usr/bin/env python3
"""
URL Extraction Utilities
Extracts URLs from text messages with various formats
"""

import re
from typing import List, Tuple
from urllib.parse import urlparse

def extract_urls(text: str) -> List[str]:
    """
    Extract all URLs from text, handling various formats
    
    Supports:
    - Standard URLs (http://, https://)
    - URLs without protocol (www.example.com)
    - Short URLs (bit.ly/xyz)
    - URLs with various TLDs
    - URLs in parentheses, quotes, etc.
    """
    urls = []
    
    # Pattern 1: Standard URLs with protocol
    # Matches: http://example.com, https://www.example.com/path?query=1
    pattern1 = r'https?://(?:[-\w.])+(?::\d+)?(?:[/\w\-._~:?#\[\]@!$&\'()*+,;=%.]*)?'
    urls.extend(re.findall(pattern1, text, re.IGNORECASE))
    
    # Pattern 2: URLs starting with www (without protocol)
    # Matches: www.example.com, www.example.co.jp/path
    pattern2 = r'(?:^|[\s])(?:www\.)(?:[-\w.])+(?:\.[\w]{2,})(?:[/\w\-._~:?#\[\]@!$&\'()*+,;=%.]*)?'
    www_urls = re.findall(pattern2, text, re.IGNORECASE)
    # Add https:// to www URLs
    for url in www_urls:
        url = url.strip()
        if url:
            urls.append(f'https://{url}')
    
    # Pattern 3: Common short URL services
    # Matches: bit.ly/xyz, t.co/abc, goo.gl/123
    short_url_domains = [
        'bit.ly', 't.co', 'goo.gl', 'tinyurl.com', 'ow.ly', 
        'is.gd', 'buff.ly', 'adf.ly', 'go.gl', 'bitly.com',
        'youtu.be', 'qr.net', 'cur.lv', 'lnkd.in', 'db.tt',
        'qr.ae', 'adfoc.us', 'rb.gy', 'short.link', 'shortened.link'
    ]
    for domain in short_url_domains:
        pattern = rf'(?:https?://)?(?:{re.escape(domain)})/[\w\-]+'
        short_urls = re.findall(pattern, text, re.IGNORECASE)
        for url in short_urls:
            if not url.startswith('http'):
                url = f'https://{url}'
            urls.append(url)
    
    # Pattern 4: Domain names with common TLDs (without www or protocol)
    # Matches: example.com, github.io, medium.co
    # Common TLDs to look for
    tlds = [
        'com', 'org', 'net', 'edu', 'gov', 'io', 'co', 'ai', 'app',
        'dev', 'blog', 'shop', 'store', 'online', 'site', 'website',
        'tech', 'info', 'me', 'us', 'uk', 'ca', 'au', 'jp', 'kr',
        'cn', 'tw', 'sg', 'my', 'th', 'vn', 'id', 'ph'
    ]
    
    # Build pattern for TLDs
    tld_pattern = '|'.join(re.escape(tld) for tld in tlds)
    pattern4 = rf'(?:^|[\s])([a-zA-Z0-9][-a-zA-Z0-9]*(?:\.[a-zA-Z0-9][-a-zA-Z0-9]*)*\.(?:{tld_pattern})(?:[/\w\-._~:?#\[\]@!$&\'()*+,;=%.]*)?)'
    
    domain_urls = re.findall(pattern4, text, re.IGNORECASE)
    for url in domain_urls:
        url = url.strip()
        if url and not any(url in u for u in urls):
            # Check if it's not already captured
            full_url = f'https://{url}'
            if full_url not in urls:
                urls.append(full_url)
    
    # Clean up and deduplicate URLs
    cleaned_urls = []
    for url in urls:
        # Remove trailing punctuation that's likely not part of the URL
        url = re.sub(r'[.,;:!?\)\]\}]+$', '', url)
        # Remove quotes if URL is wrapped in them
        url = url.strip('\'"')
        # Validate URL structure
        try:
            result = urlparse(url)
            if result.scheme and result.netloc:
                if url not in cleaned_urls:
                    cleaned_urls.append(url)
        except:
            pass
    
    return cleaned_urls

def extract_urls_with_context(text: str) -> List[Tuple[str, str]]:
    """
    Extract URLs with surrounding context for better article identification
    Returns list of (url, context) tuples
    """
    urls = extract_urls(text)
    results = []
    
    for url in urls:
        # Find context around URL (up to 50 chars before and after)
        pattern = rf'(.{{0,50}}){re.escape(url)}(.{{0,50}})'
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            before = match.group(1).strip()
            after = match.group(2).strip()
            context = f"{before} {after}".strip()
            results.append((url, context))
        else:
            results.append((url, ""))
    
    return results

def is_valid_article_url(url: str) -> bool:
    """
    Check if URL is likely an article/content URL (not just a homepage)
    """
    try:
        parsed = urlparse(url)
        
        # Skip obvious non-article URLs
        skip_patterns = [
            r'^/?$',  # Root only
            r'^/?(index|home|main)(\.\w+)?$',  # Homepage variants
            r'^/?#',  # Anchor-only URLs
            r'^/?(login|signin|signup|register)',  # Auth pages
        ]
        
        path = parsed.path
        for pattern in skip_patterns:
            if re.match(pattern, path, re.IGNORECASE):
                return False
        
        # Check for article-like patterns
        article_patterns = [
            r'/\d{4}/\d{2}/',  # Date patterns (2024/03/)
            r'/posts?/',  # Blog posts
            r'/articles?/',  # Articles
            r'/blog/',  # Blog
            r'/news/',  # News
            r'/\w+/\w+',  # At least two path segments
            r'\?p=\d+',  # WordPress style
            r'/\d+$',  # Numeric IDs
            r'/[\w-]+-[\w-]+',  # Slugified titles
        ]
        
        full_url = parsed.path + (parsed.query or '')
        for pattern in article_patterns:
            if re.search(pattern, full_url, re.IGNORECASE):
                return True
        
        # If path has substantial content, likely an article
        if len(path.strip('/')) > 10:
            return True
            
        return False
    except:
        return False

# Test the extractor
if __name__ == "__main__":
    test_cases = [
        "Check out this article: https://medium.com/@user/awesome-post-123",
        "I found these resources: www.github.com/project and https://dev.to/tutorial",
        "Short link: bit.ly/abc123 and another one t.co/xyz789",
        "Visit example.com for more info",
        "Multiple URLs: First is https://www.google.com, second is github.io/page, and third medium.co/story",
        "Here's a YouTube video: youtu.be/dQw4w9WgXcQ and a blog post www.myblog.com/2024/03/my-post",
        "Check github.com/facebook/react and also npmjs.com/package/express",
        "Japanese site: www.example.co.jp/article/123",
        "Mixed text with https://example.com/path?query=1&test=2 in the middle",
        "Parentheses (https://www.example.org) and quotes 'www.test.com'",
    ]
    
    for text in test_cases:
        print(f"\nText: {text}")
        urls = extract_urls(text)
        print(f"Extracted URLs: {urls}")
        
        with_context = extract_urls_with_context(text)
        for url, context in with_context:
            print(f"  - {url}")
            if context:
                print(f"    Context: {context}")
            print(f"    Is article? {is_valid_article_url(url)}")