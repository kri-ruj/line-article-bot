import os
import logging
from flask import Flask, request, jsonify
from datetime import datetime
import json
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)

# LINE API configuration
LINE_ACCESS_TOKEN = os.getenv('LINE_CHANNEL_ACCESS_TOKEN')
LINE_REPLY_URL = 'https://api.line.me/v2/bot/message/reply'

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# In-memory storage
saved_articles = []
webhook_logs = []

@app.route("/", methods=['GET'])
def home():
    return f"""
    <h1>LINE Bot - Simple Webhook Test</h1>
    <p>✅ Server is running on ngrok</p>
    <p>📊 Webhooks received: {len(webhook_logs)}</p>
    <p>📚 Articles saved: {len(saved_articles)}</p>
    <h2>Recent Webhooks:</h2>
    <pre>{json.dumps(webhook_logs[-5:], indent=2) if webhook_logs else 'No webhooks yet'}</pre>
    """

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({
        "status": "healthy",
        "mode": "simple",
        "webhooks_received": len(webhook_logs)
    })

@app.route('/callback', methods=['POST'])
def callback():
    # Log all headers for debugging
    headers = dict(request.headers)
    body = request.get_data(as_text=True)
    
    # Parse body if it's JSON
    try:
        body_json = json.loads(body) if body else {}
    except:
        body_json = {"raw": body}
    
    # Log webhook
    webhook_log = {
        "timestamp": datetime.now().isoformat(),
        "signature": headers.get('X-Line-Signature', 'none')[:20] + '...' if headers.get('X-Line-Signature') else 'none',
        "body": body_json,
        "events_count": len(body_json.get('events', []))
    }
    webhook_logs.append(webhook_log)
    
    logger.info(f"Webhook received:")
    logger.info(f"  Signature present: {bool(headers.get('X-Line-Signature'))}")
    logger.info(f"  Events: {len(body_json.get('events', []))}")
    logger.info(f"  Destination: {body_json.get('destination', 'none')}")
    
    # Process events if present
    if body_json.get('events'):
        for event in body_json['events']:
            if event.get('type') == 'message':
                message = event.get('message', {})
                reply_token = event.get('replyToken')
                
                if message.get('type') == 'text':
                    text = message.get('text', '')
                    logger.info(f"  Message text: {text}")
                    
                    # Prepare reply message
                    reply_text = ""
                    
                    # Check for URLs
                    if 'http' in text.lower():
                        article = {
                            "url": text,
                            "title": f"Article {len(saved_articles) + 1}",
                            "saved_at": datetime.now().isoformat()
                        }
                        saved_articles.append(article)
                        logger.info(f"  Saved article: {article['title']}")
                        reply_text = f"✅ Article saved!\n\n📚 Title: {article['title']}\n🔗 URL: {text[:50]}...\n📅 Saved at: {article['saved_at'][:19]}\n\nTotal articles: {len(saved_articles)}"
                    
                    elif text.lower() == '/list':
                        if saved_articles:
                            reply_text = "📚 Your Saved Articles:\n\n"
                            for i, article in enumerate(saved_articles[-5:], 1):
                                reply_text += f"{i}. {article['title']}\n   {article['url'][:30]}...\n\n"
                        else:
                            reply_text = "📭 No articles saved yet.\nSend me a URL to get started!"
                    
                    elif text.lower() in ['/help', 'help']:
                        reply_text = "🤖 Article Bot Help\n\n📝 Commands:\n• Send any URL - Save article\n• /list - View saved articles\n• /help - Show this message\n\n💡 Just paste a link to save it!"
                    
                    else:
                        reply_text = f"👋 Hi! Send me a URL to save it.\n\nYou said: {text}\n\nType /help for commands."
                    
                    # Send reply to LINE
                    if reply_token and reply_text:
                        send_reply(reply_token, reply_text)
    
    # Always return 200 OK to LINE
    return 'OK', 200

def send_reply(reply_token, text):
    """Send a reply message to LINE"""
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {LINE_ACCESS_TOKEN}'
    }
    
    data = {
        'replyToken': reply_token,
        'messages': [
            {
                'type': 'text',
                'text': text
            }
        ]
    }
    
    try:
        response = requests.post(LINE_REPLY_URL, headers=headers, json=data)
        if response.status_code == 200:
            logger.info(f"Reply sent successfully")
        else:
            logger.error(f"Failed to send reply: {response.status_code} - {response.text}")
    except Exception as e:
        logger.error(f"Error sending reply: {str(e)}")

@app.route('/logs', methods=['GET'])
def view_logs():
    return jsonify({
        "total_webhooks": len(webhook_logs),
        "recent_webhooks": webhook_logs[-10:],
        "saved_articles": saved_articles
    })

if __name__ == "__main__":
    port = int(os.environ.get('PORT', '5001'))
    print("\n" + "="*60)
    print("LINE BOT - SIMPLE WEBHOOK TEST")
    print("="*60)
    print(f"\nServer starting on http://localhost:{port}")
    print("\n✅ This server accepts ALL webhooks (no signature verification)")
    print("📊 View logs at /logs endpoint")
    print("\n" + "="*60)
    app.run(host='0.0.0.0', port=port, debug=True)