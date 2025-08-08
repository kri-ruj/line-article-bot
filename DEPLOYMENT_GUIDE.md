# 🚀 Deployment Guide - Article Intelligence Hub

## Prerequisites
1. Google Cloud account with billing enabled
2. gcloud CLI installed and configured
3. Docker installed locally
4. LINE Developer account with channels created

## Step 1: Prepare Credentials

Create `.env.production` file with your LINE credentials:
```bash
cp .env.production.example .env.production
# Edit .env.production with your values:
# - LINE_CHANNEL_ACCESS_TOKEN
# - LINE_CHANNEL_SECRET  
# - LINE_LOGIN_CHANNEL_ID
# - LINE_LOGIN_CHANNEL_SECRET
```

## Step 2: Build Docker Image Locally

Test the Docker build:
```bash
# Build the image
docker build -t article-hub:test .

# Run locally to test
docker run -p 8080:8080 \
  -e PORT=8080 \
  -e DB_PATH=/tmp/articles.db \
  -e BASE_URL=http://localhost:8080 \
  -e LIFF_ID=2007552096-GxP76rNd \
  article-hub:test

# Test health endpoint
curl http://localhost:8080/health
```

## Step 3: Deploy to Google Cloud Run

### Option A: Using deploy.sh script (Recommended)
```bash
# Make script executable
chmod +x deploy.sh

# Run deployment
./deploy.sh
```

### Option B: Manual deployment
```bash
# Set variables
PROJECT_ID="secondbrain-app-20250612"  # Project with billing enabled
REGION="asia-northeast1"
SERVICE_NAME="article-hub"

# Authenticate
gcloud auth login --account krittameth.rujirachainon@gmail.com
gcloud config set project $PROJECT_ID

# Enable APIs
gcloud services enable run.googleapis.com containerregistry.googleapis.com

# Build and push image
gcloud builds submit --tag gcr.io/$PROJECT_ID/$SERVICE_NAME

# Deploy to Cloud Run
gcloud run deploy $SERVICE_NAME \
  --image gcr.io/$PROJECT_ID/$SERVICE_NAME \
  --region $REGION \
  --platform managed \
  --allow-unauthenticated \
  --memory 512Mi \
  --set-env-vars "BASE_URL=https://$SERVICE_NAME-$PROJECT_ID.a.run.app" \
  --set-env-vars "LIFF_ID=2007552096-GxP76rNd" \
  --set-secrets "LINE_CHANNEL_ACCESS_TOKEN=line-channel-access-token:latest" \
  --set-secrets "LINE_CHANNEL_SECRET=line-channel-secret:latest" \
  --set-secrets "LINE_LOGIN_CHANNEL_ID=line-login-channel-id:latest" \
  --set-secrets "LINE_LOGIN_CHANNEL_SECRET=line-login-channel-secret:latest"
```

## Step 4: Configure Secrets (Recommended)

Store sensitive data in Secret Manager:
```bash
# Create secrets
echo -n "YOUR_TOKEN" | gcloud secrets create line-channel-access-token --data-file=-
echo -n "YOUR_SECRET" | gcloud secrets create line-channel-secret --data-file=-
echo -n "YOUR_ID" | gcloud secrets create line-login-channel-id --data-file=-
echo -n "YOUR_SECRET" | gcloud secrets create line-login-channel-secret --data-file=-

# Grant Cloud Run access to secrets
gcloud secrets add-iam-policy-binding line-channel-access-token \
  --member="serviceAccount:$PROJECT_ID-compute@developer.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"
```

## Step 5: Update LINE Settings

### Update Webhook URL
1. Go to [LINE Developers Console](https://developers.line.biz/)
2. Select your Messaging API channel
3. Go to "Messaging API" tab
4. Update Webhook URL to: `https://article-hub-secondbrain-app-20250612.a.run.app/webhook`
5. Enable "Use webhook"
6. Click "Verify" button

### Update LIFF URL
1. Go to LIFF tab
2. Select your LIFF app (ID: 2007552096-GxP76rNd)
3. Update Endpoint URL to: `https://article-hub-secondbrain-app-20250612.a.run.app`

### Update LINE Login
1. Select your LINE Login channel
2. Go to "LINE Login" tab
3. Add callback URL: `https://article-hub-secondbrain-app-20250612.a.run.app/callback`

## Step 6: Verify Deployment

```bash
# Get service URL
SERVICE_URL=$(gcloud run services describe article-hub \
  --region asia-northeast1 --format 'value(status.url)')

# Test health endpoint
curl $SERVICE_URL/health

# Check logs
gcloud run logs read --service article-hub --region asia-northeast1

# Monitor metrics
echo "View metrics at: https://console.cloud.google.com/run"
```

## Step 7: Test Features

1. **Test LINE Bot**:
   - Send a message to your LINE bot
   - Should receive article management options

2. **Test LIFF App**:
   - Open https://liff.line.me/2007552096-GxP76rNd
   - Should see the article management interface

3. **Test LINE Login**:
   - Visit the service URL directly
   - Click "Login with LINE"
   - Should authenticate and redirect back

## Troubleshooting

### Common Issues

1. **Database errors**: Cloud Run uses ephemeral storage. For persistence, connect to Cloud SQL or Firestore
2. **Authentication errors**: Verify all LINE credentials are correctly set
3. **Webhook not responding**: Check webhook URL and verify it's enabled in LINE console
4. **LIFF not loading**: Ensure LIFF ID is correct and endpoint URL is updated

### View Logs
```bash
# Real-time logs
gcloud run logs tail --service article-hub --region asia-northeast1

# Recent logs
gcloud run logs read --service article-hub --region asia-northeast1 --limit 50
```

### Update Environment Variables
```bash
gcloud run services update article-hub \
  --region asia-northeast1 \
  --update-env-vars KEY=VALUE
```

### Rollback
```bash
# List revisions
gcloud run revisions list --service article-hub --region asia-northeast1

# Rollback to previous revision
gcloud run services update-traffic article-hub \
  --region asia-northeast1 \
  --to-revisions REVISION_NAME=100
```

## Production Considerations

1. **Database**: Switch from SQLite to Cloud SQL or Firestore for persistence
2. **Monitoring**: Set up Cloud Monitoring alerts
3. **Logging**: Configure structured logging
4. **Security**: Use Secret Manager for all sensitive data
5. **Scaling**: Configure auto-scaling based on traffic
6. **Backup**: Implement data backup strategy

## Cost Optimization

- Cloud Run charges only for actual usage
- First 2 million requests/month are free
- Optimize cold starts by keeping instances warm
- Use Cloud CDN for static assets
- Monitor and optimize container size

## Support

- Cloud Run Documentation: https://cloud.google.com/run/docs
- LINE Developers: https://developers.line.biz/
- Project Console: https://console.cloud.google.com/run?project=secondbrain-app-20250612