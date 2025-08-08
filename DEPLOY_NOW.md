# 🚀 Deploy Updated Authentication Flow

## What's Changed
- Login page now at `/login` (not `/dashboard`)
- All paths redirect to `/login` first
- Dashboard requires authentication
- Clean authentication flow: Any URL → `/login` → LINE Auth → `/dashboard`

## Prerequisites Check
✅ Updated code in `app_firestore_final.py`
✅ Correct Dockerfile: `Dockerfile.firestore`
✅ Environment file: `.env.production`
✅ Deploy script updated with:
  - Correct LIFF ID: `2007870100-ao8GpgRQ`
  - Using `Dockerfile.firestore`

## Deploy Steps

1. **Ensure Docker is running**
   ```bash
   docker --version
   ```

2. **Make deploy script executable**
   ```bash
   chmod +x deploy.sh
   ```

3. **Run deployment**
   ```bash
   ./deploy.sh
   ```

   This will:
   - Build Docker image with updated code
   - Push to Google Container Registry
   - Deploy to Cloud Run
   - Update environment variables

4. **Verify deployment**
   - Check health: https://article-hub-959205905728.asia-northeast1.run.app/health
   - Test login page: https://article-hub-959205905728.asia-northeast1.run.app/login
   - Test redirects: https://article-hub-959205905728.asia-northeast1.run.app/

## Expected Results After Deployment

1. **Root path (/)** → Redirects to `/login`
2. **Login page (/login)** → Shows beautiful LINE login interface
3. **Dashboard (/dashboard)** → Requires authentication, redirects to `/login` if not logged in
4. **API endpoints** → Return 401 if not authenticated

## Post-Deployment Verification

Run the test script to verify:
```bash
./test_auth_curl.sh
```

Expected output:
- `/` → 302 redirect to `/login`
- `/home` → 302 redirect to `/login`
- `/kanban` → 302 redirect to `/login`
- `/login` → 200 (login page)
- `/api/stats` → 401 (requires auth)

## Troubleshooting

If deployment fails:

1. **Authentication issues**
   ```bash
   gcloud auth login
   gcloud config set project secondbrain-app-20250612
   ```

2. **Docker issues**
   - Ensure Docker Desktop is running
   - Check Docker permissions

3. **View logs**
   ```bash
   gcloud run logs read --service article-hub --region asia-northeast1
   ```

## Ready to Deploy?

Just run:
```bash
./deploy.sh
```

The deployment typically takes 3-5 minutes.