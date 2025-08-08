#\!/bin/bash
echo "Starting deployment of fixed application..."

# Set project
gcloud config set project secondbrain-app-20250612

# Deploy with explicit settings
gcloud run deploy article-hub \
  --source . \
  --region asia-northeast1 \
  --platform managed \
  --allow-unauthenticated \
  --memory 512Mi \
  --max-instances 10 \
  --timeout 60 \
  --no-traffic \
  --tag fixed

echo "Deployment submitted"
