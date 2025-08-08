#!/bin/bash

# Enhanced Deployment Script for LINE Article Intelligence System
# Includes all features: Kanban, AI analysis, LINE bot, authentication

echo "🚀 Deploying Enhanced Article Intelligence System..."

# Configuration
PROJECT_ID="secondbrain-app-20250612"
SERVICE_NAME="article-hub"
REGION="asia-northeast1"
IMAGE_NAME="gcr.io/${PROJECT_ID}/${SERVICE_NAME}"

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo "❌ gcloud CLI not found. Please install Google Cloud SDK."
    exit 1
fi

# Set project
gcloud config set project ${PROJECT_ID}

# Enable required APIs
echo "📦 Enabling required APIs..."
gcloud services enable cloudbuild.googleapis.com run.googleapis.com firestore.googleapis.com

# Create optimized Dockerfile for production
cat > Dockerfile.production << 'EOF'
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY app_production.py .
COPY ai_features.py .
COPY url_extractor.py .
COPY article_extractor.py .
COPY message_templates.py .
COPY *.html ./
COPY *.js ./

# Create temp directory for database
RUN mkdir -p /tmp

# Environment setup
ENV PORT=8080
ENV PYTHONUNBUFFERED=1

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8080/health')"

# Run the application
CMD ["python", "app_production.py"]
EOF

# Build Docker image
echo "🔨 Building Docker image..."
docker build -f Dockerfile.production -t ${IMAGE_NAME} .

# Push to Container Registry
echo "📤 Pushing image to Container Registry..."
docker push ${IMAGE_NAME}

# Deploy to Cloud Run
echo "☁️ Deploying to Cloud Run..."
gcloud run deploy ${SERVICE_NAME} \
    --image ${IMAGE_NAME} \
    --platform managed \
    --region ${REGION} \
    --allow-unauthenticated \
    --memory 512Mi \
    --cpu 1 \
    --min-instances 0 \
    --max-instances 10 \
    --port 8080 \
    --set-env-vars "LINE_CHANNEL_ACCESS_TOKEN=${LINE_CHANNEL_ACCESS_TOKEN}" \
    --set-env-vars "LINE_CHANNEL_SECRET=${LINE_CHANNEL_SECRET}" \
    --set-env-vars "LINE_LOGIN_CHANNEL_ID=${LINE_LOGIN_CHANNEL_ID}" \
    --set-env-vars "LINE_LOGIN_CHANNEL_SECRET=${LINE_LOGIN_CHANNEL_SECRET}" \
    --set-env-vars "LIFF_ID=${LIFF_ID}" \
    --set-env-vars "BASE_URL=https://${SERVICE_NAME}-959205905728.asia-northeast1.run.app"

# Get service URL
SERVICE_URL=$(gcloud run services describe ${SERVICE_NAME} --region ${REGION} --format 'value(status.url)')

echo "✅ Deployment complete!"
echo "📱 Service URL: ${SERVICE_URL}"
echo "🔗 LINE Webhook URL: ${SERVICE_URL}/callback"
echo "🖥️ Dashboard: ${SERVICE_URL}/kanban"
echo ""
echo "📝 Next steps:"
echo "1. Update LINE webhook URL to: ${SERVICE_URL}/callback"
echo "2. Update LIFF app URL to: ${SERVICE_URL}/kanban"
echo "3. Test the bot by sending a message"