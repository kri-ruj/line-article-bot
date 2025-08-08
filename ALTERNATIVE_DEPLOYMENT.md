# 🚀 Alternative Deployment Options (No Billing Required)

Since Google Cloud requires billing, here are FREE alternatives for deploying your LINE Article Hub:

## Option 1: Railway (Recommended) 🚂
**Free tier: $5 credit/month, no credit card required**

### Steps:
1. **Sign up at [Railway.app](https://railway.app/)**

2. **Install Railway CLI:**
```bash
npm install -g @railway/cli
# or
brew install railway
```

3. **Deploy from GitHub:**
```bash
# Login to Railway
railway login

# Initialize project
railway init

# Link to GitHub repo (recommended)
railway link

# Deploy
railway up

# Get your app URL
railway open
```

4. **Set environment variables in Railway dashboard:**
   - Go to your project settings
   - Add these variables:
     - `LINE_CHANNEL_ACCESS_TOKEN`
     - `LINE_CHANNEL_SECRET`
     - `LINE_LOGIN_CHANNEL_ID`
     - `LINE_LOGIN_CHANNEL_SECRET`

## Option 2: Render.com 🎨
**Free tier: 750 hours/month**

### Steps:
1. **Sign up at [Render.com](https://render.com/)**

2. **Deploy from GitHub:**
   - Connect your GitHub account
   - Select your repository
   - Choose "Docker" as environment
   - Use the provided `render.yaml` config

3. **Set environment variables in Render dashboard:**
   - Go to Environment tab
   - Add your LINE credentials

## Option 3: Fly.io ✈️
**Free tier: 3 shared VMs**

### Steps:
1. **Install Fly CLI:**
```bash
curl -L https://fly.io/install.sh | sh
```

2. **Create fly.toml:**
```toml
app = "article-hub"
primary_region = "nrt"  # Tokyo

[build]
  dockerfile = "Dockerfile"

[env]
  PORT = "8080"
  DB_PATH = "/tmp/articles.db"
  LIFF_ID = "2007552096-GxP76rNd"

[http_service]
  internal_port = 8080
  force_https = true
  auto_stop_machines = true
  auto_start_machines = true
  min_machines_running = 0
```

3. **Deploy:**
```bash
fly auth login
fly launch
fly secrets set LINE_CHANNEL_ACCESS_TOKEN=your_token
fly secrets set LINE_CHANNEL_SECRET=your_secret
fly secrets set LINE_LOGIN_CHANNEL_ID=your_id
fly secrets set LINE_LOGIN_CHANNEL_SECRET=your_secret
fly deploy
```

## Option 4: Replit 💻
**Free tier with always-on available**

### Steps:
1. **Fork on Replit:**
   - Go to [Replit.com](https://replit.com/)
   - Import from GitHub
   - Select Python template

2. **Create .replit file:**
```
run = "python app_production.py"
language = "python3"

[env]
PORT = "8080"
DB_PATH = "/tmp/articles.db"
LIFF_ID = "2007552096-GxP76rNd"
```

3. **Add secrets in Replit:**
   - Use Secrets tab for LINE credentials

## Option 5: Local with ngrok (Development) 🏠

### Steps:
1. **Run locally:**
```bash
PORT=8080 python3 app_production.py
```

2. **Expose with ngrok:**
```bash
ngrok http 8080
```

3. **Use ngrok URL for LINE webhooks**

## Comparison Table

| Platform | Free Tier | Always On | Custom Domain | Best For |
|----------|-----------|-----------|---------------|----------|
| Railway | $5/month credit | Yes | Yes (paid) | Production |
| Render | 750 hrs/month | No (spins down) | Yes | Hobby projects |
| Fly.io | 3 VMs | Yes | Yes | Global apps |
| Replit | Limited | With Hacker plan | Yes | Quick prototypes |
| ngrok | Limited requests | Yes | No | Development |

## After Deployment

### Update LINE Settings:
1. **Webhook URL:** `https://your-app-url.com/webhook`
2. **LIFF Endpoint:** `https://your-app-url.com`
3. **LINE Login Callback:** `https://your-app-url.com/callback`

### Database Persistence:
For production, consider adding:
- **PostgreSQL** (free on Railway/Render)
- **SQLite with volume** (Fly.io)
- **Turso** (Serverless SQLite)

## Quick Start with Railway (Easiest)

```bash
# 1. Install Railway CLI
npm install -g @railway/cli

# 2. Login
railway login

# 3. Create new project
railway init

# 4. Deploy
railway up

# 5. Add environment variables in dashboard
railway open

# Done! Your app is live 🎉
```

## Environment Variables Template

Create `.env` for local development:
```env
PORT=8080
DB_PATH=/tmp/articles.db
LIFF_ID=2007552096-GxP76rNd
BASE_URL=http://localhost:8080
LINE_CHANNEL_ACCESS_TOKEN=your_token_here
LINE_CHANNEL_SECRET=your_secret_here
LINE_LOGIN_CHANNEL_ID=your_id_here
LINE_LOGIN_CHANNEL_SECRET=your_secret_here
```

## Support Links

- [Railway Docs](https://docs.railway.app/)
- [Render Docs](https://render.com/docs)
- [Fly.io Docs](https://fly.io/docs/)
- [Replit Docs](https://docs.replit.com/)
- [ngrok Docs](https://ngrok.com/docs)