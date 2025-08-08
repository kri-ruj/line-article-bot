# LINE Login Configuration

## Required Settings in LINE Developers Console

### 1. LINE Login Channel Information
- **Channel ID**: 2007870100
- **Channel Name**: Your LINE Login Channel

### 2. Callback URLs (Must Add ALL of These)
Add these URLs in the "Callback URL" section:

```
https://article-hub-959205905728.asia-northeast1.run.app/callback
https://article-hub-fwsh7yaraa-an.a.run.app/callback
http://localhost:5000/callback
http://localhost:8080/callback
```

### 3. Required Permissions
Make sure these are enabled:
- ✅ profile
- ✅ openid

### 4. Channel Status
- Make sure the channel is **Published** (not in Development mode)

### 5. LIFF Settings (if using LIFF)
- **LIFF ID**: 2007552096-GxP76rNd
- **Endpoint URL**: https://article-hub-959205905728.asia-northeast1.run.app
- **Scope**: profile, openid

## Production URLs

### Main Service URL
```
https://article-hub-959205905728.asia-northeast1.run.app
```

### Webhook URL (for LINE Messaging API)
```
https://article-hub-959205905728.asia-northeast1.run.app/webhook
```

### Login URL
```
https://article-hub-959205905728.asia-northeast1.run.app/login
```

### Kanban Board
```
https://article-hub-959205905728.asia-northeast1.run.app/kanban
```

## Testing LINE Login

After adding the callback URLs, test login at:
```
https://article-hub-959205905728.asia-northeast1.run.app/login
```

## Troubleshooting

If you still get redirect_uri errors:

1. **Check for typos** - The URL must match EXACTLY
2. **Wait a few minutes** - Changes may take time to propagate
3. **Clear browser cache** and try again
4. **Check channel status** - Must be Published, not Development
5. **Verify BASE_URL** in Cloud Run environment variables matches the service URL