import os
import logging
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage, 
    QuickReply, QuickReplyButton, MessageAction,
    FlexSendMessage
)
from dotenv import load_dotenv
from article_extractor import ArticleExtractor
from google_sheets import GoogleSheetsManager
from message_templates import create_article_saved_flex, create_error_message
import re

load_dotenv()

app = Flask(__name__)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

line_bot_api = LineBotApi(os.getenv('LINE_CHANNEL_ACCESS_TOKEN'))
handler = WebhookHandler(os.getenv('LINE_CHANNEL_SECRET'))

article_extractor = ArticleExtractor()
sheets_manager = GoogleSheetsManager()

@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    logger.info("Request body: " + body)
    
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        logger.error("Invalid signature")
        abort(400)
    
    return 'OK'

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    text = event.message.text.strip()
    user_id = event.source.user_id
    
    try:
        profile = line_bot_api.get_profile(user_id)
        user_name = profile.display_name
    except:
        user_name = "User"
    
    url_pattern = r'https?://(?:[-\w.])+(?:\:\d+)?(?:[/\w\s._~%!$&\'()*+,;=:@-]+)?'
    urls = re.findall(url_pattern, text)
    
    if not urls:
        quick_reply = QuickReply(items=[
            QuickReplyButton(
                action=MessageAction(label="📖 View saved articles", text="/list")
            ),
            QuickReplyButton(
                action=MessageAction(label="❓ Help", text="/help")
            ),
            QuickReplyButton(
                action=MessageAction(label="📊 Stats", text="/stats")
            )
        ])
        
        if text.lower() == '/help':
            help_text = (
                "📚 Article Saver Bot\n\n"
                "Send me any article URL and I'll save it to your Google Sheet!\n\n"
                "Commands:\n"
                "• Send URL - Save article\n"
                "• /list - View recent articles\n"
                "• /stats - View statistics\n"
                "• /help - Show this message\n\n"
                "Example:\n"
                "https://medium.com/article-link"
            )
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text=help_text, quick_reply=quick_reply)
            )
        elif text.lower() == '/list':
            recent_articles = sheets_manager.get_recent_articles(5)
            if recent_articles:
                articles_text = "📚 Recent Articles:\n\n"
                for article in recent_articles:
                    articles_text += f"• {article['title'][:50]}...\n  {article['category']} | {article['reading_time']}\n\n"
            else:
                articles_text = "No articles saved yet. Send me a URL to get started!"
            
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text=articles_text, quick_reply=quick_reply)
            )
        elif text.lower() == '/stats':
            stats = sheets_manager.get_statistics()
            stats_text = (
                f"📊 Your Reading Stats:\n\n"
                f"• Total articles: {stats['total']}\n"
                f"• Read: {stats['read']}\n"
                f"• Unread: {stats['unread']}\n"
                f"• Most saved category: {stats['top_category']}\n"
                f"• Total reading time: {stats['total_time']} min"
            )
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text=stats_text, quick_reply=quick_reply)
            )
        else:
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(
                    text="👋 Hi! Send me an article URL to save it to your reading list.",
                    quick_reply=quick_reply
                )
            )
        return
    
    url = urls[0]
    
    processing_message = TextSendMessage(text="📝 Extracting article information...")
    line_bot_api.reply_message(event.reply_token, processing_message)
    
    try:
        article_info = article_extractor.extract(url)
        
        article_info['saved_by'] = user_name
        article_info['notes'] = text.replace(url, '').strip() if text != url else ''
        
        row_number = sheets_manager.save_article(article_info)
        
        flex_message = create_article_saved_flex(article_info, row_number)
        
        line_bot_api.push_message(
            user_id,
            FlexSendMessage(
                alt_text=f"✅ Saved: {article_info['title'][:50]}...",
                contents=flex_message
            )
        )
        
        quick_reply = QuickReply(items=[
            QuickReplyButton(
                action=MessageAction(label="📝 Add note", text=f"/note {row_number}")
            ),
            QuickReplyButton(
                action=MessageAction(label="✅ Mark as read", text=f"/read {row_number}")
            ),
            QuickReplyButton(
                action=MessageAction(label="📖 View list", text="/list")
            )
        ])
        
        follow_up = TextSendMessage(
            text=f"Article saved to row {row_number} in your Google Sheet! 🎉",
            quick_reply=quick_reply
        )
        line_bot_api.push_message(user_id, follow_up)
        
    except Exception as e:
        logger.error(f"Error processing article: {str(e)}")
        error_message = create_error_message(str(e))
        line_bot_api.push_message(user_id, TextSendMessage(text=error_message))

@app.route('/health', methods=['GET'])
def health_check():
    return 'OK', 200

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)