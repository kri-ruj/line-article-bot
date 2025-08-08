# 🚀 Production Deployment - Article Intelligence Hub

## ✅ Current Production Status

Your Article Intelligence Hub is **FULLY DEPLOYED** on Google Cloud Run with Firestore database.

**NO NGROK NEEDED** - Everything runs on Google Cloud!

## 📱 Production URLs

### Service Endpoints
- **Main Service**: https://article-hub-959205905728.asia-northeast1.run.app
- **LINE Webhook**: https://article-hub-959205905728.asia-northeast1.run.app/callback
- **Dashboard**: https://article-hub-959205905728.asia-northeast1.run.app/dashboard
- **Kanban Board**: https://article-hub-959205905728.asia-northeast1.run.app/kanban
- **Health Check**: https://article-hub-959205905728.asia-northeast1.run.app/health
- **LIFF Dashboard**: https://liff.line.me/2007552096-GxP76rNd

## 🔥 Technology Stack

- **Runtime**: Google Cloud Run (Serverless)
- **Database**: Google Firestore (NoSQL, Permanent Storage)
- **Container**: Docker (linux/amd64)
- **Language**: Python 3.11
- **Messaging**: LINE Messaging API
- **Authentication**: LINE Login OAuth 2.0

## 📊 Features

### Core Functionality
- ✅ Save articles from LINE chat
- ✅ Extract URLs from text messages
- ✅ Support multiple URLs in single message
- ✅ Permanent data storage (Firestore)
- ✅ Real-time synchronization
- ✅ Kanban board for article management
- ✅ Dashboard with statistics

### Data Persistence
- ✅ No data loss on redeploy
- ✅ Automatic Firestore backups
- ✅ 99.99% availability
- ✅ Scalable to millions of documents

## 🧪 Testing Production

### Quick Test
```bash
python3 test_production_webhook.py
```

### Manual Test
1. Send any URL to your LINE bot
2. Check Firestore Console: https://console.firebase.google.com/project/secondbrain-app-20250612/firestore
3. View in Dashboard: https://article-hub-959205905728.asia-northeast1.run.app/dashboard

## 🛠️ Deployment Commands

### View Logs
```bash
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=article-hub" \
  --limit 20 --project secondbrain-app-20250612
```

### Update Deployment
```bash
# Build and push new image
docker build --platform linux/amd64 -f Dockerfile.firestore -t article-hub-firestore .
docker tag article-hub-firestore gcr.io/secondbrain-app-20250612/article-hub:latest
docker push gcr.io/secondbrain-app-20250612/article-hub:latest

# Deploy to Cloud Run
gcloud run deploy article-hub \
  --image gcr.io/secondbrain-app-20250612/article-hub:latest \
  --region asia-northeast1 \
  --project secondbrain-app-20250612
```

### Check Service Status
```bash
gcloud run services describe article-hub \
  --region asia-northeast1 \
  --project secondbrain-app-20250612
```

## 📝 Configuration

### Environment Variables (Already Set in Cloud Run)
- `LINE_CHANNEL_ACCESS_TOKEN`: Your LINE bot token
- `LINE_CHANNEL_SECRET`: Your LINE bot secret
- `LINE_LOGIN_CHANNEL_ID`: LINE Login channel ID
- `PORT`: 8080 (Cloud Run default)

### Firestore Collections
- `users`: User profiles and statistics
- `articles`: Saved articles with metadata
- `sessions`: Login sessions

## 🔒 Security

- ✅ HTTPS only (enforced by Cloud Run)
- ✅ LINE signature verification
- ✅ Firestore security rules
- ✅ Service account with minimal permissions
- ✅ No secrets in code (using environment variables)

## 📈 Monitoring

### Cloud Console
- [Cloud Run Dashboard](https://console.cloud.google.com/run/detail/asia-northeast1/article-hub/metrics?project=secondbrain-app-20250612)
- [Firestore Console](https://console.firebase.google.com/project/secondbrain-app-20250612/firestore)
- [Cloud Logging](https://console.cloud.google.com/logs?project=secondbrain-app-20250612)

### Health Check
```bash
curl https://article-hub-959205905728.asia-northeast1.run.app/health
```

## 🚫 What NOT to Do

- ❌ **DO NOT use ngrok** - Production runs on Cloud Run
- ❌ **DO NOT run locally** for production - Use Cloud Run
- ❌ **DO NOT use SQLite** - Firestore is the database
- ❌ **DO NOT commit secrets** - Use environment variables

## 💡 Tips

1. **Always use production URLs** - No localhost, no ngrok
2. **Check Firestore for data** - That's where articles are stored
3. **Monitor Cloud Run logs** - For debugging issues
4. **Use LIFF for mobile access** - Better LINE integration

## 🆘 Troubleshooting

### Bot not responding?
1. Check webhook URL in LINE Console: Should be `https://article-hub-959205905728.asia-northeast1.run.app/callback`
2. Verify webhook is enabled in LINE Console
3. Check Cloud Run logs for errors

### Data not saving?
1. Check Firestore Console for documents
2. Verify Cloud Run has Firestore permissions
3. Check logs for write errors

### Need to restart service?
```bash
gcloud run services update article-hub --region asia-northeast1
```

---

**Remember: Everything is in production on Google Cloud. No local development or ngrok needed!**