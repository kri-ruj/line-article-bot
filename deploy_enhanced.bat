@echo off
echo ========================================
echo Enhanced Article Intelligence Deployment
echo ========================================
echo.

REM Configuration
set PROJECT_ID=secondbrain-app-20250612
set SERVICE_NAME=article-hub
set REGION=asia-northeast1
set IMAGE_NAME=gcr.io/%PROJECT_ID%/%SERVICE_NAME%

REM Check if gcloud is installed
where gcloud >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: gcloud CLI not found. Please install Google Cloud SDK.
    echo Download from: https://cloud.google.com/sdk/docs/install
    pause
    exit /b 1
)

REM Set project
echo Setting up Google Cloud project...
gcloud config set project %PROJECT_ID%

REM Enable required APIs
echo Enabling required APIs...
call gcloud services enable cloudbuild.googleapis.com run.googleapis.com firestore.googleapis.com

REM Build the Docker image locally
echo Building Docker image...
docker build -t %IMAGE_NAME% .

REM Push to Container Registry
echo Pushing image to Container Registry...
docker push %IMAGE_NAME%

REM Deploy to Cloud Run
echo Deploying to Cloud Run...
gcloud run deploy %SERVICE_NAME% ^
    --image %IMAGE_NAME% ^
    --platform managed ^
    --region %REGION% ^
    --allow-unauthenticated ^
    --memory 512Mi ^
    --cpu 1 ^
    --min-instances 0 ^
    --max-instances 10 ^
    --port 8080

REM Get service URL
for /f "tokens=*" %%i in ('gcloud run services describe %SERVICE_NAME% --region %REGION% --format "value(status.url)"') do set SERVICE_URL=%%i

echo.
echo ========================================
echo Deployment Complete!
echo ========================================
echo Service URL: %SERVICE_URL%
echo LINE Webhook: %SERVICE_URL%/callback
echo Dashboard: %SERVICE_URL%/kanban
echo.
echo To test locally first:
echo   python app_ultimate.py
echo   Open: http://localhost:5001
echo.
pause