# 🚀 How to Use 10X AI Features

## Quick Start Guide

### 1. Start the Servers

```bash
# Terminal 1: Main App (Port 5003)
python app_unified_home.py

# Terminal 2: WebSocket Server (Port 8765)
python realtime_server.py

# Terminal 3: LINE Bot (Port 5005) - if needed
python app_line_fixed.py
```

### 2. Access the Enhanced Dashboard
Open: http://localhost:5003

## 🧠 Using Quantum Reading Scores

The Quantum Score (0-1000) tells you which articles to read first:
- **900-1000**: MUST READ - Perfect timing & high impact
- **700-899**: HIGH PRIORITY - Very relevant
- **500-699**: GOOD - Worth reading
- **Below 500**: LOW - Save for later

### How It Works:
1. Click "📊 View Priority Ranking" on dashboard
2. Articles are ranked by Quantum Score
3. The score considers:
   - Your reading patterns
   - Current time of day
   - Article complexity vs your level
   - Knowledge connections
   - Potential impact

## ⚡ Real-time Reading Intelligence

### Connect to WebSocket:
```javascript
// Add this to any article page
const ws = new WebSocket('ws://localhost:8765');

ws.onopen = () => {
    // Start reading session
    ws.send(JSON.stringify({
        type: 'start_reading',
        session_id: 'session_123',
        article_id: 1,
        user_id: 'user_1'
    }));
};

// Send reading metrics
setInterval(() => {
    ws.send(JSON.stringify({
        type: 'reading_metrics',
        scroll_position: window.scrollY,
        reading_speed: 250, // words per minute
        focus_level: 0.8,
        comprehension_score: 0.7,
        engagement_level: 0.9
    }));
}, 1000);

// Receive insights
ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    console.log('Real-time insight:', data);
};
```

## 👁️ Visual Intelligence Analysis

### Analyze Images in Articles:
```python
from vision_intelligence import VisionAnalyzer

analyzer = VisionAnalyzer()

# Analyze an image
with open('article_image.jpg', 'rb') as f:
    image_data = f.read()
    
visual_intel = analyzer.analyze_image(image_data)

print(f"Objects: {visual_intel.objects_detected}")
print(f"Text in image: {visual_intel.text_extracted}")
print(f"Complexity: {visual_intel.complexity_score}")
print(f"Chart detected: {visual_intel.chart_data}")
```

## 📊 Knowledge Graph Navigation

### Find Learning Paths:
```python
from advanced_ai_pipeline import KnowledgeGraphEngine

graph = KnowledgeGraphEngine()

# Add articles to graph
graph.add_article(article1)
graph.add_article(article2)

# Find path to learn a concept
path = graph.find_learning_path(
    start_article=1,
    goal_concept="machine learning"
)
print(f"Read these articles in order: {path}")
```

## 🎯 Using the Advanced Pipeline

### Process Articles with Full Intelligence:
```python
import asyncio
from advanced_ai_pipeline import AdvancedAIPipeline

async def enhance_article():
    pipeline = AdvancedAIPipeline()
    
    article_data = {
        'id': 1,
        'url': 'https://example.com',
        'title': 'AI Revolution',
        'content': 'Full article text...'
    }
    
    # Process through 10x pipeline
    enhanced = await pipeline.process_article(article_data)
    
    print(f"Quantum Score: {enhanced.quantum_score}")
    print(f"Knowledge Density: {enhanced.knowledge_density}")
    print(f"Optimal Read Time: {enhanced.optimal_read_time}")
    print(f"Key Insights: {enhanced.key_insights}")
    print(f"Action Items: {enhanced.action_items}")

asyncio.run(enhance_article())
```

## 🔄 Real-time Features

### 1. Collaborative Reading
Multiple users can read the same article and see each other's:
- Highlights
- Comments
- Reading position
- Insights

### 2. Voice Commands
Say commands like:
- "Summarize this article"
- "Explain this concept"
- "Bookmark this position"
- "Next article"
- "Translate to Spanish"

### 3. Live Metrics Dashboard
Watch in real-time:
- Your reading speed
- Focus level
- Comprehension score
- Time to completion

## 📈 Analytics & Insights

### Generate Intelligence Report:
```python
from advanced_ai_pipeline import AdvancedAnalytics

analytics = AdvancedAnalytics()
report = analytics.generate_insights_report(articles)

print(f"Average Quantum Score: {report['quantum_metrics']['average_score']}")
print(f"Top Concepts: {report['knowledge_metrics']['top_concepts']}")
print(f"Knowledge Gaps: {report['predictions']['knowledge_gaps']}")
print(f"Recommendations: {report['recommendations']}")
```

## 🎮 Interactive Features

### 1. Reading Modes
- **Speed Mode**: Optimized for fast reading
- **Deep Mode**: Enhanced comprehension features
- **Collaborative Mode**: Read with others
- **Voice Mode**: Hands-free operation

### 2. AI Assistants
- **Question Generator**: Auto-creates study questions
- **Note Taker**: Generates personalized notes
- **Concept Explainer**: Breaks down complex ideas
- **Progress Tracker**: Monitors your learning

## 💡 Pro Tips

### Optimize Your Quantum Scores:
1. **Read in the morning** (6-10 AM) for complex articles
2. **Build knowledge chains** - read connected articles
3. **Match complexity** to your current level
4. **Focus on high-impact** articles with action items

### Improve Reading Efficiency:
1. **Use real-time metrics** to maintain focus
2. **Take breaks** when focus drops below 50%
3. **Review insights** after each session
4. **Follow suggested** learning paths

### Visual Intelligence:
1. **Analyze charts** for quick data extraction
2. **Search visually** similar articles
3. **Generate infographics** from text
4. **Track visual** complexity

## 🚨 Troubleshooting

### WebSocket Not Connecting:
```bash
# Check if server is running
lsof -i :8765

# Restart server
python realtime_server.py
```

### Low Quantum Scores:
- Check your reading history is being tracked
- Ensure articles have content (not just titles)
- Verify time settings are correct

### No Visual Analysis:
- Install Pillow: `pip install Pillow`
- Check image file formats (JPG, PNG)
- Verify image file sizes (<10MB)

## 📱 Mobile Access

Access from your phone:
1. Find your computer's IP: `ipconfig` or `ifconfig`
2. Access: `http://YOUR_IP:5003`
3. WebSocket: `ws://YOUR_IP:8765`

## 🔗 LINE Bot Integration

Send to LINE Bot:
- "analyze [URL]" - Get quantum score
- "visual [URL]" - Analyze images
- "recommend" - Get recommendations
- "insights" - Get current insights

## 🎯 Next Steps

1. **Start Simple**: Try the priority ranking first
2. **Add WebSocket**: Enable real-time features
3. **Analyze Images**: Process article visuals
4. **Build Graph**: Connect your knowledge
5. **Go Collaborative**: Read with friends

---

Need help? The system learns and improves as you use it. The more you read, the smarter it gets! 🚀