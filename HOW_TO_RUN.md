# How to Run - LINE Article Bot (After Refactoring)

## Quick Start (Easiest)

### Option 1: Use the Batch File (Windows)
```bash
run.bat
```
Then choose:
- Press 1 for Ultimate App (NO DEPENDENCIES NEEDED)
- Press 2 for LINE Bot (needs setup)
- Press 3 for Production App (needs setup)
- Press 4 for AI Demo

### Option 2: Direct Python Command
```bash
# NO SETUP NEEDED - Just run:
python app_ultimate.py

# Open browser at: http://localhost:5001
```

## The 3 Main Apps

### 1. app_ultimate.py - RECOMMENDED FOR TESTING
- **No dependencies needed** (uses only Python standard library)
- **No setup required**
- Full Kanban board with drag & drop
- All AI features working (simulated)
- Port: 5001

```bash
python app_ultimate.py
# Open: http://localhost:5001
```

### 2. app_line_fixed.py - For LINE Integration
- Requires dependencies installed
- Needs .env file configured
- Handles LINE webhook messages
- Port: 5005

```bash
# First time setup:
pip install -r requirements.txt

# Configure .env file:
LINE_CHANNEL_ACCESS_TOKEN=your_token
LINE_CHANNEL_SECRET=your_secret

# Run:
python app_line_fixed.py
```

### 3. app_production.py - For Production Deployment
- Full authentication system
- Persistent storage
- Multi-user support
- Requires full setup

```bash
# Setup:
pip install -r requirements.txt
# Configure .env

# Run:
python app_production.py
```

## Test Everything Works

Run the test script:
```bash
python test_run.py
```

Output should show:
```
Testing imports...
  app_ultimate.py           Ultimate App (No Dependencies) [PASS]
  app_line_fixed.py         LINE Bot                       [PASS]
  app_production.py         Production App                 [PASS]
  simple_10x_demo.py        AI Demo                        [PASS]
```

## Project Structure (Cleaned)

```
line-article-bot/
├── run.bat                 # Easy launcher
├── test_run.py            # Test all apps
│
├── app_ultimate.py        # Main app (NO DEPS)
├── app_line_fixed.py      # LINE bot
├── app_production.py      # Production version
│
├── ai_features.py         # AI functions
├── url_extractor.py       # URL extraction
├── article_extractor.py   # Article parsing
├── message_templates.py   # LINE templates
│
├── simple_10x_demo.py     # Demo script
│
├── requirements.txt       # Dependencies (optional)
├── .env                   # Config (for LINE/production)
│
└── backup_cleanup_2025/   # Backup of old files
```

## Common Issues & Solutions

### Issue: Unicode/Emoji errors on Windows
**Solution**: Fixed in current version (emojis removed from console output)

### Issue: Port already in use
**Solution**: Change PORT in the app file:
```python
PORT = 5002  # Change to any free port
```

### Issue: Missing dependencies
**Solution**: Use app_ultimate.py which needs NO dependencies

### Issue: LINE bot not receiving messages
**Solution**: Check .env configuration and ngrok tunnel

## Features Available

### In app_ultimate.py (No Dependencies):
- ✅ Kanban board (4 columns)
- ✅ Drag & drop
- ✅ Add/Edit articles
- ✅ Quantum scoring (0-1000)
- ✅ Priority ranking
- ✅ Study notes
- ✅ Recommendations
- ✅ Similar detection
- ✅ Real-time updates
- ✅ Export features

### Additional in Production:
- User authentication
- Team collaboration
- Persistent storage
- LINE integration

## Deployment

For production deployment:
```bash
# Build Docker image
docker build -t article-hub .

# Run locally
docker run -p 8080:8080 article-hub

# Deploy to Google Cloud
./deploy.sh
```

## Support

All old files backed up in: `backup_cleanup_2025/`

To restore any deleted file:
```bash
cp backup_cleanup_2025/filename.py .
```