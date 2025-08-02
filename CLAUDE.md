# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

LINE Article Intelligence System - A multi-service architecture for saving, analyzing, and managing articles sent via LINE bot with AI-powered analysis and Kanban-style progress tracking.

## Architecture

### Service Architecture (Multiple Flask Apps on Different Ports)

- **Port 5001**: `app_ultra_enhanced.py` - Ultra-enhanced article processing with OpenAI GPT-3.5 integration (75+ data fields)
- **Port 5002**: `app_kanban.py` - Kanban board for article study progress (4 stages: inbox/reading/reviewing/completed)
- **Port 5003**: `app_unified_home.py` - Unified homepage with navigation, real-time logs, and dashboard
- **Port 5004**: `app_main.py` - Main routing application that forwards requests
- **Port 5005**: `app_line_fixed.py` - LINE bot with proper webhook handling and message responses

### Database Architecture

- **articles_enhanced.db**: Main database with AI-enhanced fields (migrated from Google Sheets)
- **articles_kanban.db**: Kanban-specific database for study progress tracking
- **articles_ultra.db**: Ultra-enhanced database with 75+ fields (has column mismatch issue)

### Key Integration Points

1. LINE webhook → ngrok → Port 5003 (unified home) → forwards to Port 5005 (LINE bot)
2. Article saving → LINE bot → Kanban database → AI analysis (if enabled)
3. Dashboard views → Read from Kanban DB → Display on unified home

## Development Commands

### Environment Setup
```bash
# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
pip install openai  # For AI features
```

### Running Services
```bash
# Start individual services
source venv/bin/activate
python3 app_line_fixed.py      # LINE bot (port 5005)
python3 app_unified_home.py    # Homepage (port 5003)
python3 app_kanban.py          # Kanban board (port 5002)
python3 app_ultra_enhanced.py  # AI analysis (port 5001)

# Start all services (background)
source venv/bin/activate
nohup python3 app_line_fixed.py > line_bot.log 2>&1 &
nohup python3 app_unified_home.py > unified.log 2>&1 &
nohup python3 app_kanban.py > kanban.log 2>&1 &
```

### Ngrok Tunneling
```bash
# For homepage + LINE webhook
ngrok http 5003

# Update LINE webhook URL to: https://[ngrok-url]/callback
```

### Database Commands
```bash
# Check database contents
sqlite3 articles_kanban.db "SELECT * FROM articles_kanban;"

# Check article stages
sqlite3 articles_kanban.db "SELECT stage, COUNT(*) FROM articles_kanban GROUP BY stage;"
```

### Monitoring Logs
```bash
# Watch LINE bot logs
tail -f line_bot.log

# Watch all logs
tail -f *.log

# Check for errors
grep ERROR *.log
```

## Known Issues & Solutions

### Database Column Mismatch (app_ultra_enhanced.py)
- **Issue**: "77 values for 78 columns" error
- **Location**: app_ultra_enhanced.py:542
- **Fix**: Check INSERT statement column count vs values provided

### Invalid LINE Reply Token
- **Issue**: Test tokens don't work with LINE API
- **Solution**: Only real LINE webhook events have valid reply tokens

### Port Conflicts
- **Issue**: Port 5000 used by macOS AirPlay Receiver
- **Solution**: Use ports 5001-5005 instead

### ngrok Session Limits
- **Issue**: Free account limited to 1 session
- **Solution**: Kill existing ngrok before starting new one: `pkill ngrok`

## Environment Variables (.env)

```
LINE_CHANNEL_ACCESS_TOKEN=your_token
LINE_CHANNEL_SECRET=your_secret
OPENAI_API_KEY=your_openai_key  # For AI analysis
GOOGLE_SHEETS_ID=your_sheet_id  # Legacy, not used
```

## LINE Bot Commands

- Send any URL - Saves article to Kanban
- `/help` - Show available commands
- `/stats` - View statistics
- `/list` - Show recent articles

## Database Schema (articles_kanban)

Main columns:
- `id`: Primary key
- `url`, `url_hash`: Article URL and hash
- `title`, `summary`: Article metadata
- `stage`: Kanban stage (inbox/reading/reviewing/completed)
- `priority`: high/medium/low
- `study_notes`, `key_learnings`: User notes
- `total_study_time`: Time spent in minutes
- `is_archived`: Boolean for hiding articles

## Testing

### Test LINE Webhook Locally
```python
# Create test_webhook.py
import requests
url = "http://localhost:5005/callback"
# ... (webhook test code)
```

### Test Database Connection
```bash
sqlite3 articles_kanban.db ".tables"
```

## Deployment Notes

- Ensure all environment variables are set
- Use process manager (PM2, systemd) for production
- Set up proper logging rotation
- Configure ngrok authtoken for stable URLs
- Consider using LINE webhook verification

## AI Analysis Features (when enabled)

- Sentiment analysis with confidence scores
- Topic extraction and categorization
- Named entity recognition
- Key insights and takeaways
- Quality and credibility scoring
- Virality prediction
- Reading level assessment
- Actionable insights generation