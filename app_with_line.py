import os
import logging
from flask import Flask, request, abort, jsonify
from datetime import datetime
import re
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import LINE Bot SDK
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage,
    FlexSendMessage, QuickReply, QuickReplyButton, MessageAction
)

app = Flask(__name__)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize LINE Bot
line_bot_api = LineBotApi(os.getenv('LINE_CHANNEL_ACCESS_TOKEN'))
handler = WebhookHandler(os.getenv('LINE_CHANNEL_SECRET'))

# In-memory storage for demo
saved_articles = []

@app.route("/", methods=['GET'])
def home():
    return """
    <h1>LINE Article Bot - With LINE Integration</h1>
    <p>Bot is running with LINE integration!</p>
    <h2>Status:</h2>
    <ul>
        <li>✅ LINE Webhook: Active</li>
        <li>✅ Message Handling: Enabled</li>
        <li>⚠️ Google Sheets: Not configured (using memory storage)</li>
    </ul>
    <h2>Articles Saved: """ + str(len(saved_articles)) + """</h2>
    """

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({
        "status": "healthy",
        "mode": "line-enabled",
        "articles_saved": len(saved_articles)
    })

@app.route('/callback', methods=['POST'])
def callback():
    # Get signature - handle missing header gracefully
    signature = request.headers.get('X-Line-Signature', '')
    body = request.get_data(as_text=True)
    logger.info("Request body: " + body[:200] + "..." if len(body) > 200 else body)
    
    # Skip signature verification if header is missing (for testing)
    if not signature:
        logger.warning("No signature provided - skipping verification")
        # Still try to process the webhook
        try:
            handler.handle(body, "dummy_signature")
        except:
            pass
        return 'OK', 200
    
    try:
        handler.handle(body, signature)
    except InvalidSignatureError as e:
        logger.error(f"Invalid signature: {str(e)}")
        logger.error(f"Signature received: {signature[:20]}...")
        abort(400)
    except Exception as e:
        logger.error(f"Error handling webhook: {str(e)}")
        # Return 200 to prevent LINE from retrying
        return 'OK', 200
    
    return 'OK', 200

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_id = event.source.user_id
    text = event.message.text
    
    logger.info(f"Received message from {user_id}: {text}")
    
    # Check for URLs in the message
    url_pattern = r'https?://(?:[-\w.])+(?:\:\d+)?(?:[/\w\s._~%!$&\'()*+,;=:@-]+)?'
    urls = re.findall(url_pattern, text)
    
    if urls:
        # Simulate article extraction
        article_info = {
            'url': urls[0],
            'title': f'Article from {urls[0].split("/")[2]}',
            'description': 'Article saved successfully! This is running in demo mode with LINE integration.',
            'category': 'Web Article',
            'saved_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        saved_articles.append(article_info)
        
        # Create flex message
        flex_message = create_article_flex_message(article_info, len(saved_articles))
        
        line_bot_api.reply_message(
            event.reply_token,
            FlexSendMessage(
                alt_text=f"✅ Saved: {article_info['title']}",
                contents=flex_message
            )
        )
    elif text.lower() == '/list':
        if saved_articles:
            articles_text = "📚 Your Saved Articles:\n\n"
            for i, article in enumerate(saved_articles[-5:], 1):
                articles_text += f"{i}. {article['title']}\n   📅 {article['saved_at']}\n   🔗 {article['url'][:40]}...\n\n"
            articles_text += f"\n📊 Total saved: {len(saved_articles)} articles"
        else:
            articles_text = "📭 No articles saved yet.\n\nSend me a URL to get started!"
        
        quick_reply = QuickReply(items=[
            QuickReplyButton(
                action=MessageAction(label="❓ Help", text="/help")
            ),
            QuickReplyButton(
                action=MessageAction(label="📊 Stats", text="/stats")
            )
        ])
        
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=articles_text, quick_reply=quick_reply)
        )
    elif text.lower() == '/stats':
        stats_text = f"""📊 Your Statistics:

📚 Total Articles: {len(saved_articles)}
📅 First Save: {saved_articles[0]['saved_at'] if saved_articles else 'N/A'}
⏰ Last Save: {saved_articles[-1]['saved_at'] if saved_articles else 'N/A'}

💡 Tip: Send any URL to save it instantly!"""
        
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=stats_text)
        )
    elif text.lower() in ['/help', 'help', '?']:
        help_text = """🤖 Article Saver Bot

I help you save and organize articles!

📝 Commands:
• Send any URL - I'll save it
• /list - View recent articles
• /stats - See your statistics
• /help - Show this message

🔥 Quick Tips:
• Just paste a link to save
• I extract title & content
• Articles saved in memory

⚠️ Note: Running without Google Sheets
Articles are temporary (memory only)"""
        
        quick_reply = QuickReply(items=[
            QuickReplyButton(
                action=MessageAction(label="📖 View articles", text="/list")
            ),
            QuickReplyButton(
                action=MessageAction(label="📊 Stats", text="/stats")
            ),
            QuickReplyButton(
                action=MessageAction(label="🔗 Test", text="https://example.com")
            )
        ])
        
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=help_text, quick_reply=quick_reply)
        )
    else:
        # Default response with quick actions
        quick_reply = QuickReply(items=[
            QuickReplyButton(
                action=MessageAction(label="❓ Help", text="/help")
            ),
            QuickReplyButton(
                action=MessageAction(label="📖 List", text="/list")
            ),
            QuickReplyButton(
                action=MessageAction(label="📊 Stats", text="/stats")
            )
        ])
        
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(
                text="👋 Send me a URL to save it, or use the quick actions below!",
                quick_reply=quick_reply
            )
        )

def create_article_flex_message(article_info, row_number):
    return {
        "type": "bubble",
        "size": "kilo",
        "header": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {
                    "type": "box",
                    "layout": "horizontal",
                    "contents": [
                        {
                            "type": "text",
                            "text": "✅ Article Saved!",
                            "color": "#ffffff",
                            "size": "lg",
                            "weight": "bold",
                            "flex": 1
                        },
                        {
                            "type": "text",
                            "text": f"#{row_number}",
                            "color": "#ffffff",
                            "size": "md",
                            "align": "end"
                        }
                    ]
                }
            ],
            "backgroundColor": "#27ACB2",
            "paddingAll": "20px"
        },
        "body": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {
                    "type": "text",
                    "text": article_info['title'],
                    "weight": "bold",
                    "size": "lg",
                    "wrap": True,
                    "maxLines": 2
                },
                {
                    "type": "text",
                    "text": article_info['description'],
                    "size": "sm",
                    "color": "#666666",
                    "margin": "md",
                    "wrap": True,
                    "maxLines": 3
                },
                {
                    "type": "separator",
                    "margin": "xl"
                },
                {
                    "type": "box",
                    "layout": "vertical",
                    "margin": "xl",
                    "spacing": "sm",
                    "contents": [
                        {
                            "type": "box",
                            "layout": "horizontal",
                            "contents": [
                                {
                                    "type": "text",
                                    "text": "📁 Category:",
                                    "size": "sm",
                                    "color": "#555555",
                                    "flex": 0
                                },
                                {
                                    "type": "text",
                                    "text": article_info['category'],
                                    "size": "sm",
                                    "color": "#111111",
                                    "align": "end"
                                }
                            ]
                        },
                        {
                            "type": "box",
                            "layout": "horizontal",
                            "contents": [
                                {
                                    "type": "text",
                                    "text": "🕐 Saved:",
                                    "size": "sm",
                                    "color": "#555555",
                                    "flex": 0
                                },
                                {
                                    "type": "text",
                                    "text": article_info['saved_at'],
                                    "size": "sm",
                                    "color": "#111111",
                                    "align": "end"
                                }
                            ]
                        }
                    ]
                }
            ],
            "paddingAll": "20px"
        },
        "footer": {
            "type": "box",
            "layout": "vertical",
            "spacing": "sm",
            "contents": [
                {
                    "type": "button",
                    "action": {
                        "type": "uri",
                        "label": "📖 Read Article",
                        "uri": article_info['url']
                    },
                    "style": "primary",
                    "color": "#27ACB2",
                    "height": "sm"
                },
                {
                    "type": "button",
                    "action": {
                        "type": "message",
                        "label": "📚 View All Articles",
                        "text": "/list"
                    },
                    "style": "secondary",
                    "height": "sm"
                }
            ],
            "paddingAll": "10px"
        }
    }

if __name__ == "__main__":
    port = int(os.environ.get('PORT', '5001'))
    print("\n" + "="*60)
    print("LINE ARTICLE BOT - WITH LINE INTEGRATION")
    print("="*60)
    print(f"\nServer starting on http://localhost:{port}")
    print("\n✅ LINE Bot is active and responding to messages!")
    print("📱 Send a message to your bot in LINE to test")
    print("\n" + "="*60)
    app.run(host='0.0.0.0', port=port, debug=True)