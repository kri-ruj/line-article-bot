# 📚 LINE Article Saver Bot

A LINE bot that automatically saves articles to Google Sheets. Just send a URL and it extracts article information, categorizes it, and saves it to your spreadsheet for easy reading management.

## ✨ Features

- **Automatic Article Extraction**: Extracts title, author, reading time, and description
- **Smart Categorization**: Auto-categorizes articles (AI/Tech, Business, Programming, etc.)
- **Google Sheets Integration**: Saves all articles to your Google Sheet
- **Reading Management**: Track read/unread status, add notes, view statistics
- **Beautiful Messages**: Rich flex messages with article previews

## 📋 Prerequisites

- Python 3.8+
- LINE Messaging API Account
- Google Cloud Account with Sheets API enabled
- Google Sheets document

## 🚀 Quick Setup Guide

### Step 1: LINE Bot Setup (10 minutes)

1. Go to [LINE Developers Console](https://developers.line.biz/console/)
2. Create a new provider (or select existing)
3. Create a new Messaging API channel
4. Note down:
   - Channel Secret (Basic settings tab)
   - Channel Access Token (Messaging API tab - issue a token)

### Step 2: Google Sheets Setup (15 minutes)

#### Create the Spreadsheet:
1. Create a new Google Sheet
2. Name it "Article Library" (or your preference)
3. Note the Sheet ID from the URL: `https://docs.google.com/spreadsheets/d/[SHEET_ID]/edit`

#### Enable Google Sheets API:
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing
3. Enable Google Sheets API:
   - Go to "APIs & Services" → "Library"
   - Search for "Google Sheets API"
   - Click and Enable

#### Create Service Account:
1. Go to "APIs & Services" → "Credentials"
2. Click "Create Credentials" → "Service Account"
3. Fill in service account details
4. Click "Create and Continue"
5. Skip optional permissions
6. Click "Done"
7. Click on the created service account
8. Go to "Keys" tab
9. Click "Add Key" → "Create new key"
10. Choose JSON format
11. Save the downloaded file as `credentials.json`

#### Share Sheet with Service Account:
1. Open your Google Sheet
2. Click "Share" button
3. Add the service account email (found in credentials.json as "client_email")
4. Give "Editor" permission
5. Click "Send"

### Step 3: Local Setup

1. Clone or download this repository:
```bash
git clone <repository-url>
cd line-article-bot
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Create `.env` file from template:
```bash
cp .env.example .env
```

4. Edit `.env` with your credentials:
```env
LINE_CHANNEL_ACCESS_TOKEN=your_line_channel_access_token
LINE_CHANNEL_SECRET=your_line_channel_secret
GOOGLE_SHEETS_ID=your_google_sheets_id
SHEET_NAME=Articles
GOOGLE_CREDENTIALS_PATH=credentials.json
```

5. Place your `credentials.json` file in the project root

### Step 4: Testing Locally with ngrok

1. Install ngrok: https://ngrok.com/download

2. Run the Flask app:
```bash
python app.py
```

3. In another terminal, expose your local server:
```bash
ngrok http 5000
```

4. Copy the HTTPS URL from ngrok (e.g., `https://abc123.ngrok.io`)

5. Set webhook URL in LINE Console:
   - Go to LINE Developers Console
   - Open your channel
   - Messaging API tab
   - Set Webhook URL: `https://abc123.ngrok.io/callback`
   - Enable "Use webhook"

6. Test by adding your bot as friend and sending a URL!

## 🚢 Deployment Options

### Deploy to Heroku

1. Install Heroku CLI
2. Create Heroku app:
```bash
heroku create your-app-name
```

3. Set environment variables:
```bash
heroku config:set LINE_CHANNEL_ACCESS_TOKEN=your_token
heroku config:set LINE_CHANNEL_SECRET=your_secret
heroku config:set GOOGLE_SHEETS_ID=your_sheet_id
heroku config:set SHEET_NAME=Articles
heroku config:set GOOGLE_CREDENTIALS_JSON='paste_entire_credentials_json_content'
```

4. Deploy:
```bash
git add .
git commit -m "Initial deployment"
git push heroku main
```

5. Update LINE webhook URL to: `https://your-app-name.herokuapp.com/callback`

### Deploy to Railway

1. Fork this repository to your GitHub
2. Go to [Railway](https://railway.app/)
3. Click "New Project" → "Deploy from GitHub repo"
4. Select your forked repository
5. Add environment variables in Railway dashboard
6. Railway will auto-deploy
7. Get deployment URL from Railway
8. Update LINE webhook URL

### Deploy to Google Cloud Run

1. Install gcloud CLI
2. Build and deploy:
```bash
gcloud run deploy line-article-bot \
  --source . \
  --platform managed \
  --region asia-northeast1 \
  --allow-unauthenticated
```
3. Set environment variables in Cloud Run console
4. Update LINE webhook URL

## 📱 How to Use

### Basic Commands:
- **Send any URL** - Saves the article to your sheet
- **/help** - Show help message
- **/list** - View recent 5 articles
- **/stats** - View reading statistics

### After Saving an Article:
- **Read Article** - Opens the article in browser
- **Mark as Read** - Updates status in sheet
- **Add Note** - Add personal notes

### Google Sheet Structure:
Your sheet will have these columns:
- Saved Date
- Title
- Author  
- URL
- Category
- Reading Time
- Description
- Keywords
- Publish Date
- Status (Read/Unread)
- Notes
- Saved By
- Read Date
- Rating

## 🔧 Configuration

### Categories
Edit `article_extractor.py` to customize categories:
```python
self.categories = {
    'Your Category': ['keyword1', 'keyword2'],
    # Add more...
}
```

### Reading Time Calculation
Default: 200 words per minute. Edit in `article_extractor.py`:
```python
wpm = 200  # Change this value
```

## 🐛 Troubleshooting

### Bot doesn't respond:
- Check webhook URL is correct
- Verify all environment variables are set
- Check logs for errors

### Google Sheets errors:
- Ensure service account has editor access
- Verify Sheet ID is correct
- Check credentials.json is valid

### Article extraction fails:
- Some websites block automated access
- Try different article URLs
- Check internet connectivity

## 📝 License

MIT License - feel free to use and modify!

## 🤝 Contributing

Contributions welcome! Please feel free to submit a Pull Request.

## 💡 Future Enhancements

- [ ] AI-powered article summarization
- [ ] Reading reminders
- [ ] Export to Notion/Evernote
- [ ] Multiple sheet support
- [ ] Reading progress tracking
- [ ] Article recommendations

## 📧 Support

For issues or questions, please open an issue on GitHub.

---

Made with ❤️ for productive reading!