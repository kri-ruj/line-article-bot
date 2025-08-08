#!/bin/bash

echo "=== Deployment Verification Script ==="
echo ""

# Check current service URL
echo "1. Current Service URL:"
gcloud run services describe article-hub --region asia-northeast1 --format="value(status.url)"
echo ""

# Check last deployment time
echo "2. Last Deployment Time:"
gcloud run services describe article-hub --region asia-northeast1 --format="value(status.latestReadyRevisionName)" | cut -d'-' -f3-
echo ""

# Check if build is still in progress
echo "3. Latest Build Status:"
gcloud builds list --limit=1 --format="table(ID,STATUS,CREATE_TIME)"
echo ""

# Check if the fixes are in the deployed version
echo "4. Testing if fixes are live (checking JavaScript content):"
SERVICE_URL=$(gcloud run services describe article-hub --region asia-northeast1 --format="value(status.url)")

# Test if localStorage persistence is mentioned in the response
echo "   Checking for localStorage persistence..."
curl -s "$SERVICE_URL" | grep -q "localStorage.setItem('lineUserId'" && echo "   ✓ localStorage persistence found" || echo "   ✗ localStorage persistence NOT found"

echo ""
echo "5. Manual Testing URLs:"
echo "   - Main App: $SERVICE_URL"
echo "   - LIFF URL: https://liff.line.me/2007870100-ao8GpgRQ"
echo ""

echo "=== How to Manually Verify Fixes ==="
echo "1. Open the LIFF URL in your browser"
echo "2. Login with LINE"
echo "3. Add some articles"
echo "4. Refresh the page"
echo "5. Check if your articles and userId persist"
echo "6. Try creating/joining a team"
echo ""

# Show build logs URL if build is in progress
BUILD_ID=$(gcloud builds list --limit=1 --format="value(ID)" 2>/dev/null)
if [ ! -z "$BUILD_ID" ]; then
    echo "Build logs available at:"
    echo "https://console.cloud.google.com/cloud-build/builds/$BUILD_ID?project=secondbrain-app-20250612"
fi