# Persistence Issue - Data Loss on Redeploy

## The Problem
Data is being lost on each redeploy because:
1. The database in Cloud Storage is empty (0 articles)
2. Each deployment downloads this empty database
3. New articles are saved but may not sync properly before next deployment

## Root Cause
The sync mechanism has a 30-second interval, and if the container is terminated before a sync happens, data is lost.

## Solution
To fix this permanently:

### Immediate Actions
1. **Force sync on every write operation** - Done in enhanced version
2. **Backup before deploy** - Manual process needed
3. **Verify sync is working** - Check logs

### Manual Data Recovery Process
If you have data you want to preserve:

1. **Before deploying**, manually backup current data:
```bash
# Get current container's database
kubectl exec -it [POD_NAME] -- cat /tmp/articles.db > local_backup.db

# Or download from Cloud Run logs/console
```

2. **Upload backup to Cloud Storage**:
```bash
gcloud storage cp local_backup.db gs://secondbrain-app-20250612-article-data/articles.db
```

3. **Then deploy new version**

### Long-term Solution
Consider using:
- **Cloud SQL** instead of SQLite for true persistence
- **Firestore** for NoSQL document storage
- **Cloud Storage with JSON files** instead of SQLite

## Current Workaround
The enhanced version includes:
- Immediate sync after each save
- Better error handling
- Backup creation on sync

## Testing Persistence
1. Save an article
2. Wait 30 seconds for sync
3. Check Cloud Storage:
```bash
gcloud storage ls -l gs://secondbrain-app-20250612-article-data/
```
4. Download and verify:
```bash
gcloud storage cp gs://secondbrain-app-20250612-article-data/articles.db /tmp/test.db
sqlite3 /tmp/test.db "SELECT COUNT(*) FROM articles;"
```

## Important Notes
- Cloud Run containers can be terminated at any time
- There's no guarantee of graceful shutdown
- Sync must happen frequently and immediately after changes
- Consider using managed database services for production