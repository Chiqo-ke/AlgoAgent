# AlgoCLI Quick Reference

## 🚀 Quick Start

```bash
cd AlgoCLI
pip install -r requirements.txt
python run.py
```

## ⌨️ Keyboard Shortcuts

| Key | Action |
|-----|--------|
| `n` | New Workflow |
| `r` | Refresh |
| `q` | Quit |
| `Enter` | View Details |
| `p` | Pause |
| `Ctrl+C` | Resume |
| `d` | Delete |
| `↑/↓` | Navigate |
| `Tab` | Switch Tab |

## 🎨 Status Colors

| Color | Status |
|-------|--------|
| 🟢 Green | Running / Completed |
| 🔵 Blue | Created |
| 🟡 Yellow | Paused |
| ❌ Red | Failed |
| ⛔ Orange | Cancelled |

## 🤖 Agent Icons

| Icon | Agent |
|------|-------|
| 🧠 | Planner |
| 💻 | Coder |
| 🧪 | Tester |
| 🔧 | Debugger |

## 📊 Main Panels

1. **Workflows** (Left) - List of all workflows
2. **Details** (Right) - Selected workflow info
3. **Tasks** (Right) - Task breakdown
4. **Logs** (Right) - Event stream
5. **Metrics** (Right) - System stats

## 🔧 Common Tasks

### Create Workflow
1. Press `n`
2. Enter request
3. Press Enter

### Monitor Progress
1. Select workflow (↑/↓)
2. Press Enter
3. View Tasks tab

### Pause/Resume
1. Select workflow
2. Press `p` to pause
3. Press `Ctrl+C` to resume

### Cancel Workflow
1. Select workflow
2. Press `d`

## 🌐 API Endpoints

```
GET    /health
POST   /api/workflows/
GET    /api/workflows/
GET    /api/workflows/{id}/
PATCH  /api/workflows/{id}/pause/
PATCH  /api/workflows/{id}/resume/
DELETE /api/workflows/{id}/
```

## 🐛 Troubleshooting

### Can't Connect
```bash
# Start API server
cd ../AlgoAgent
python -m uvicorn multi_agent.api_server:app --host 0.0.0.0 --port 8000
```

### Missing Dependencies
```bash
pip install -r requirements.txt
```

### Check API Health
```bash
curl http://localhost:8000/health
```

## 📝 Configuration

Edit `.env` file:
```env
API_BASE_URL=http://localhost:8000
API_TIMEOUT=30
```

## 🎯 Tips

- Auto-refresh every 5 seconds
- Use keyboard for speed
- Check logs for errors
- View metrics for system health
- Multiple workflows supported

---
**Version**: 1.0.0 | **Theme**: Luminous
