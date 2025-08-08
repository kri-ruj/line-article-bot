# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

LINE Article Intelligence System - A Flask-based application for saving, analyzing, and managing articles via LINE bot with Kanban-style progress tracking and AI features.

## Architecture

### Main Applications

- **app_ultimate.py** - Consolidated app with ALL features (Port 5001) - NO DEPENDENCIES, uses only Python standard library
- **app_line_fixed.py** - LINE bot webhook handler (Port 5005) for receiving and processing LINE messages
- **app_production.py** - Production-ready app with authentication and persistent storage
- **app_firestore_final.py** - Google Firestore-integrated version for cloud deployment

### Database Schema (articles_kanban.db)

Primary table with columns:
- `id`, `url`, `url_hash`, `title`, `summary`
- `stage` (inbox/reading/reviewing/completed)
- `priority` (high/medium/low)
- `category`, `word_count`, `reading_time`
- `study_notes`, `key_learnings`, `total_study_time`
- `is_archived`, `created_at`, `updated_at`

## Development Commands

### Quick Start (NO DEPENDENCIES)
```bash
# Run the main app without any dependencies
python3 app_ultimate.py
# Open http://localhost:5001
```

### Full Setup (with LINE bot and dependencies)
```bash
# Create and activate virtual environment
python -m venv venv
# Windows: venv\Scripts\activate
# Linux/Mac: source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Running Services
```bash
# Run main consolidated app (no dependencies needed)
python app_ultimate.py          # Port 5001

# Run with LINE bot integration
python app_line_fixed.py        # Port 5005

# Run production version with auth
python app_production.py        # Port varies
```

### Testing
```bash
# Test LINE webhook locally
python test_line_webhook.py

# Test article saving
python test_article_save.py

# Test production webhook
python test_production_webhook.py
```

### Deployment
```bash
# Deploy to Google Cloud Run
chmod +x deploy.sh
./deploy.sh

# Build Docker image
docker build -t article-hub .

# Run Docker locally
docker run -p 8080:8080 -e PORT=8080 article-hub
```

## Key Files to Understand

- **app_ultimate.py**: Main consolidated app with all features (no dependencies)
- **ai_features.py**: AI analysis functions (sentiment, topic extraction, etc.)
- **app_line_fixed.py**: LINE bot webhook handler
- **url_extractor.py**: Article URL extraction and metadata fetching

## Environment Variables (.env)

```
LINE_CHANNEL_ACCESS_TOKEN=your_token
LINE_CHANNEL_SECRET=your_secret
LINE_LOGIN_CHANNEL_ID=your_login_id
LINE_LOGIN_CHANNEL_SECRET=your_login_secret
LIFF_ID=your_liff_id
```

## Production Deployment

- **Google Cloud Run**: Production deployment using Docker and deploy.sh script
- **URLs**: 
  - Webhook: `https://article-hub-959205905728.asia-northeast1.run.app/callback`
  - LIFF: `https://liff.line.me/2007870100-ao8GpgRQ`

## LINE Bot Commands

- Send any URL - Saves article with metadata extraction
- `/help` - Show available commands
- `/stats` - View statistics
- `/list` - Show recent articles