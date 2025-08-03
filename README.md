# 🧠 Article Intelligence Hub

AI-powered article management system with drag-and-drop Kanban board and quantum scoring.

## ✨ Features

- **Drag & Drop Kanban Board** - Move articles between Inbox → Reading → Reviewing → Completed
- **Quantum Scoring (0-1000)** - AI ranks articles by importance
- **Smart Recommendations** - AI suggests related articles
- **Study Notes Generation** - Auto-generate study notes for any article
- **Priority Ranking** - See articles ranked by AI score
- **Similar Article Detection** - Find duplicate content
- **Real-time Analytics** - Track reading progress and completion rate

## 🚀 Quick Start

### Run the App (NO DEPENDENCIES REQUIRED\!)

```bash
python3 app_ultimate.py
```

Then open: **http://localhost:5001**

### Run LINE Bot (Optional)

```bash
python3 app_line_fixed.py
```

LINE bot runs on port 5005 for article saving via LINE messenger.

## 📱 How to Use

### Kanban Board
- **Drag articles** between columns to change their status
- **Inbox** → New articles to read
- **Reading** → Currently reading
- **Reviewing** → Need to review/study
- **Completed** → Finished articles

### AI Features
- Click **"Priority Ranking"** to see articles ranked by AI
- Click **"Study Notes"** to generate notes
- Click **"Smart Recommendations"** to get suggestions

### Quantum Score
Articles are scored 0-1000 based on:
- Content quality
- Category relevance
- Time of day optimization
- Reading stage
- AI analysis

## 📊 Database

Articles are stored in `articles_kanban.db` SQLite database.

## 🔧 Configuration

Edit `app_ultimate.py` to change:
- `PORT = 5001` - Change server port
- `KANBAN_DB_PATH` - Database file location

## 🎯 No Dependencies\!

This app uses **only Python standard library**. No pip install needed\!

---

Made with ❤️ and AI
