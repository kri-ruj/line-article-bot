import os
import logging
from flask import Flask, request, abort, jsonify
from datetime import datetime
import re

# Simple demo mode without LINE and Google dependencies
app = Flask(__name__)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# In-memory storage for demo
saved_articles = []

@app.route("/", methods=['GET'])
def home():
    return """
    <h1>LINE Article Bot - Demo Mode</h1>
    <p>Bot is running in demo mode without LINE/Google integration.</p>
    <h2>Test Endpoints:</h2>
    <ul>
        <li>POST /demo/save - Save an article (send JSON with 'url' field)</li>
        <li>GET /demo/articles - View saved articles</li>
        <li>GET /health - Health check</li>
    </ul>
    <h2>To complete setup:</h2>
    <ol>
        <li>Get LINE credentials from LINE Developers Console</li>
        <li>Get Google Sheets credentials from Google Cloud Console</li>
        <li>Update .env file with your credentials</li>
        <li>Run the main app.py</li>
    </ol>
    """

@app.route("/demo/save", methods=['POST'])
def demo_save():
    """Demo endpoint to test article saving"""
    data = request.get_json()
    if not data or 'url' not in data:
        return jsonify({"error": "Please provide a URL"}), 400
    
    # Simulate article extraction
    from article_extractor import ArticleExtractor
    extractor = ArticleExtractor()
    
    try:
        article_info = extractor.extract(data['url'])
        article_info['id'] = len(saved_articles) + 1
        saved_articles.append(article_info)
        
        return jsonify({
            "success": True,
            "message": f"Article saved! (Demo mode - not saved to Google Sheets)",
            "article": {
                "title": article_info['title'],
                "category": article_info['category'],
                "reading_time": article_info['reading_time'],
                "url": article_info['url']
            }
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/demo/articles", methods=['GET'])
def demo_articles():
    """View saved articles in demo mode"""
    return jsonify({
        "total": len(saved_articles),
        "articles": saved_articles
    })

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({
        "status": "healthy",
        "mode": "demo",
        "message": "Bot is running in demo mode. Configure credentials to enable full functionality."
    })

@app.route('/callback', methods=['POST'])
def callback():
    # Get the signature from LINE (if present)
    signature = request.headers.get('X-Line-Signature', '')
    body = request.get_data(as_text=True)
    
    # Log the webhook call
    logger.info(f"Received webhook call in demo mode")
    logger.info(f"Body: {body[:100]}...")  # Log first 100 chars
    
    # In demo mode, we just return OK without signature verification
    # This allows LINE to verify the webhook endpoint
    return 'OK', 200

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5001))
    print("\n" + "="*60)
    print("LINE ARTICLE BOT - DEMO MODE")
    print("="*60)
    print(f"\nServer starting on http://localhost:{port}")
    print("\nDemo mode is active because credentials are not configured.")
    print("To enable full functionality:")
    print("1. Get LINE credentials from https://developers.line.biz/console/")
    print("2. Get Google Sheets credentials from Google Cloud Console")
    print("3. Update .env file with your credentials")
    print("4. Run app.py instead of app_demo.py")
    print("\n" + "="*60)
    app.run(host='0.0.0.0', port=port, debug=True)