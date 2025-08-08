#!/usr/bin/env python3
"""
Update app_production_fixed.py to add URL extraction capability
"""

import re

# Read the current app
with open('app_production_fixed.py', 'r') as f:
    content = f.read()

# Find where to insert the URL extraction functions (after imports)
import_end = content.find('# Configuration from environment variables')

# URL extraction code to insert
url_extraction_code = '''
# URL Extraction Functions
def extract_urls(text):
    """Extract all URLs from text"""
    urls = []
    
    # Pattern 1: Standard URLs with protocol
    pattern1 = r'https?://(?:[-\\w.])+(?::\\d+)?(?:[/\\w\\-._~:?#\\[\\]@!$&\\'()*+,;=%.]*)?'
    urls.extend(re.findall(pattern1, text, re.IGNORECASE))
    
    # Pattern 2: URLs starting with www
    pattern2 = r'(?:^|[\\s])(?:www\\.)(?:[-\\w.])+(?:\\.[\\w]{2,})(?:[/\\w\\-._~:?#\\[\\]@!$&\\'()*+,;=%.]*)?'
    www_urls = re.findall(pattern2, text, re.IGNORECASE)
    for url in www_urls:
        url = url.strip()
        if url:
            urls.append(f'https://{url}')
    
    # Pattern 3: Common short URL services
    short_domains = ['bit.ly', 't.co', 'goo.gl', 'tinyurl.com', 'youtu.be', 'lnkd.in']
    for domain in short_domains:
        pattern = rf'(?:https?://)?(?:{re.escape(domain)})/[\\w\\-]+'
        short_urls = re.findall(pattern, text, re.IGNORECASE)
        for url in short_urls:
            if not url.startswith('http'):
                url = f'https://{url}'
            urls.append(url)
    
    # Pattern 4: Domain names with common TLDs
    tlds = ['com', 'org', 'net', 'edu', 'gov', 'io', 'co', 'ai', 'app', 'dev', 'me']
    tld_pattern = '|'.join(re.escape(tld) for tld in tlds)
    pattern4 = rf'(?:^|[\\s])([a-zA-Z0-9][-a-zA-Z0-9]*(?:\\.[a-zA-Z0-9][-a-zA-Z0-9]*)*\\.(?:{tld_pattern})(?:[/\\w\\-._~:?#\\[\\]@!$&\\'()*+,;=%.]*)?)'
    
    domain_urls = re.findall(pattern4, text, re.IGNORECASE)
    for url in domain_urls:
        url = url.strip()
        if url and not any(url in u for u in urls):
            full_url = f'https://{url}'
            if full_url not in urls:
                urls.append(full_url)
    
    # Clean and deduplicate
    cleaned = []
    for url in urls:
        url = re.sub(r'[.,;:!?\\)\\]\\}]+$', '', url)
        url = url.strip('\\'\"')
        try:
            result = urlparse(url)
            if result.scheme and result.netloc and url not in cleaned:
                cleaned.append(url)
        except:
            pass
    
    return cleaned

'''

# Insert the URL extraction code
content = content[:import_end] + url_extraction_code + content[import_end:]

# Now find and update the handle_line_webhook method to use URL extraction
webhook_pattern = r"(if event\['type'\] == 'message'.*?message_text = event\['message'\]\['text'\].*?reply_token = event\['replyToken'\].*?\n\s+# Process the message\n\s+)(if message_text\.startswith\('http'\):.*?else:.*?reply = self\.create_quick_reply_message\(\))"

def replacement(match):
    prefix = match.group(1)
    
    new_code = '''# Extract URLs from message
                    urls = extract_urls(message_text)
                    
                    if urls:
                        # Save all extracted URLs
                        saved_count = 0
                        for url in urls:
                            try:
                                self.save_article_from_line(user_id, url)
                                saved_count += 1
                            except Exception as e:
                                logging.error(f"Failed to save URL {url}: {e}")
                        
                        if saved_count == 1:
                            reply = self.create_flex_message(f'✅ Article saved!', urls[0])
                        elif saved_count > 1:
                            reply = {
                                'type': 'text',
                                'text': f'✅ Saved {saved_count} articles from your message!\\n\\n' + 
                                       '\\n'.join([f'• {url[:50]}{"..." if len(url) > 50 else ""}' for url in urls[:5]]) +
                                       (f'\\n... and {len(urls)-5} more' if len(urls) > 5 else ''),
                                'quickReply': {
                                    'items': [
                                        {
                                            'type': 'action',
                                            'action': {
                                                'type': 'uri',
                                                'label': '📊 View in LIFF',
                                                'uri': f'https://liff.line.me/{LIFF_ID}'
                                            }
                                        },
                                        {
                                            'type': 'action',
                                            'action': {
                                                'type': 'message',
                                                'label': '📚 List',
                                                'text': '/list'
                                            }
                                        }
                                    ]
                                }
                            }
                        else:
                            reply = {'type': 'text', 'text': '⚠️ No valid URLs found in your message'}
                    elif message_text.startswith('http'):
                        # Fallback for direct URL (shouldn't normally reach here)
                        self.save_article_from_line(user_id, message_text)
                        reply = self.create_flex_message('✅ Article saved!', message_text)
                    elif message_text == '/help':
                        reply = self.create_help_message()
                    elif message_text == '/stats':
                        reply = self.create_stats_message(user_id)
                    elif message_text == '/list':
                        reply = self.create_articles_list(user_id)
                    elif message_text == '/backup':
                        reply = self.create_backup_message()
                    else:
                        reply = self.create_quick_reply_message()'''
    
    return prefix + new_code

# Apply the replacement
content = re.sub(webhook_pattern, replacement, content, flags=re.DOTALL)

# Save the updated file
with open('app_production_enhanced.py', 'w') as f:
    f.write(content)

print("✅ Created app_production_enhanced.py with URL extraction!")
print("Features added:")
print("  - Extracts multiple URLs from text")
print("  - Handles various URL formats (with/without protocol)")
print("  - Supports short URLs (bit.ly, t.co, etc.)")
print("  - Saves all found URLs as separate articles")
print("  - Shows summary when multiple URLs are saved")