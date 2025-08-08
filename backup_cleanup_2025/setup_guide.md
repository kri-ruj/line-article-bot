# 🚀 LINE Article Bot Setup Guide

## Step-by-Step Setup Instructions

### ✅ Current Status
- ✓ Bot code is ready
- ✓ All Python files created
- ⏳ Need to configure LINE and Google credentials

---

## 📱 Step 1: LINE Bot Setup (10 minutes)

### 1.1 Create LINE Channel
1. Go to: https://developers.line.biz/console/
2. Log in with your LINE account
3. Click "Create a new provider" (or use existing)
4. Enter provider name (e.g., "My Bots")
5. Click "Create a Messaging API channel"
6. Fill in:
   - Channel name: "Article Saver Bot"
   - Channel description: "Saves articles to Google Sheets"
   - Category: Select appropriate
   - Subcategory: Select appropriate
7. Click "Create"

### 1.2 Get Credentials
1. In your channel settings, go to "Basic settings" tab
2. Copy **Channel secret** 
3. Go to "Messaging API" tab
4. Under "Channel access token", click "Issue"
5. Copy the **Channel access token**

### 1.3 Add Bot as Friend
1. In "Messaging API" tab
2. Scan the QR code with LINE app
3. Add bot as friend

---

## 📊 Step 2: Google Sheets Setup (15 minutes)

### 2.1 Create Google Sheet
1. Go to: https://sheets.google.com
2. Create new spreadsheet
3. Name it "Article Library"
4. Copy the Sheet ID from URL:
   ```
   https://docs.google.com/spreadsheets/d/[THIS_IS_YOUR_SHEET_ID]/edit
   ```

### 2.2 Enable Google Sheets API
1. Go to: https://console.cloud.google.com/
2. Create new project or select existing
3. Click hamburger menu → "APIs & Services" → "Library"
4. Search for "Google Sheets API"
5. Click on it and press "Enable"

### 2.3 Create Service Account
1. Go to "APIs & Services" → "Credentials"
2. Click "+ CREATE CREDENTIALS" → "Service account"
3. Service account details:
   - Name: "line-bot-sheets"
   - ID: (auto-generated)
   - Description: "LINE bot access to Google Sheets"
4. Click "Create and Continue"
5. Skip "Grant this service account access" (click Continue)
6. Skip "Grant users access" (click Done)

### 2.4 Download Credentials
1. Click on your created service account
2. Go to "Keys" tab
3. Click "Add Key" → "Create new key"
4. Choose "JSON"
5. Download will start automatically
6. **Save this file as `credentials.json` in the bot folder**

### 2.5 Share Sheet with Service Account
1. Open `credentials.json` file
2. Find the email: `"client_email": "xxx@xxx.iam.gserviceaccount.com"`
3. Go to your Google Sheet
4. Click "Share" button (top right)
5. Paste the service account email
6. Give "Editor" permission
7. Uncheck "Notify people"
8. Click "Share"

---

## ⚙️ Step 3: Configure Bot

### 3.1 Update .env file
Edit the `.env` file with your credentials:

```env
# LINE Bot Configuration
LINE_CHANNEL_ACCESS_TOKEN=paste_your_channel_access_token_here
LINE_CHANNEL_SECRET=paste_your_channel_secret_here

# Google Sheets Configuration
GOOGLE_SHEETS_ID=paste_your_sheet_id_here
SHEET_NAME=Articles

# Google Service Account Credentials
GOOGLE_CREDENTIALS_PATH=credentials.json

# Server Configuration
PORT=5000
```

### 3.2 Place credentials.json
Make sure `credentials.json` is in the same folder as `app.py`

---

## 🧪 Step 4: Test Locally

### 4.1 Install Dependencies
```bash
pip install Flask line-bot-sdk beautifulsoup4 requests google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client python-dotenv gunicorn
```

### 4.2 Production Deployment
The bot is deployed on Google Cloud Run:
- **Production URL**: https://article-hub-959205905728.asia-northeast1.run.app
- **Webhook URL**: https://article-hub-959205905728.asia-northeast1.run.app/callback
- **Database**: Google Firestore (permanent storage)

### 4.3 Set Webhook URL (Already Configured)
1. Go to LINE Developers Console
2. In "Messaging API" tab
3. Webhook URL should be: `https://article-hub-959205905728.asia-northeast1.run.app/callback`
4. Toggle "Use webhook" to ON
5. Click "Verify" to test connection

---

## 🎯 Step 5: Test Your Bot

1. Open LINE app
2. Find your bot in friends list
3. Send a test URL like:
   - https://medium.com/any-article
   - https://dev.to/any-article
4. Bot should:
   - Extract article info
   - Save to Google Sheet
   - Send confirmation message

### Test Commands:
- Send any URL - Saves article
- `/help` - Shows help
- `/list` - Shows recent articles
- `/stats` - Shows statistics

---

## 🚢 Step 6: Deploy (Optional)

### Deploy to Railway (Easiest)
1. Push code to GitHub
2. Go to https://railway.app
3. Sign in with GitHub
4. New Project → Deploy from GitHub repo
5. Select your repo
6. Add environment variables from .env
7. Deploy!

### Deploy to Heroku
1. Install Heroku CLI
2. Run:
```bash
heroku create your-app-name
heroku config:set LINE_CHANNEL_ACCESS_TOKEN=xxx
heroku config:set LINE_CHANNEL_SECRET=xxx
heroku config:set GOOGLE_SHEETS_ID=xxx
heroku config:set GOOGLE_CREDENTIALS_JSON='paste_entire_json_content'
git push heroku main
```

---

## 🔧 Troubleshooting

### Bot doesn't respond
- Check webhook URL is correct: https://article-hub-959205905728.asia-northeast1.run.app/callback
- Verify "Use webhook" is ON in LINE Developers Console
- Check Cloud Run logs: `gcloud logging read "resource.type=cloud_run_revision" --limit 20`
- Look at Flask console for errors

### Google Sheets error
- Verify sheet is shared with service account email
- Check credentials.json is in correct location
- Ensure Sheet ID is correct

### Article extraction fails
- Some sites block bots
- Try different article URLs
- Check internet connection

---

## 📝 Next Steps

After setup:
1. Customize categories in `article_extractor.py`
2. Modify message templates in `message_templates.py`
3. Add more features as needed

Need help? Check the console logs for detailed error messages!