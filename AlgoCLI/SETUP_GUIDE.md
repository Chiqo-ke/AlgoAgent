# AlgoCLI Quick Setup Guide

## 📋 Prerequisites

- Python 3.8 or higher
- AlgoAgent multi-agent API server running on port 8000

## 🚀 Installation

1. **Navigate to the AlgoCLI directory:**
   ```bash
   cd AlgoCLI
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure the API endpoint (optional):**
   
   The `.env` file is already created with default settings. Edit it if your API is on a different host/port:
   ```
   API_BASE_URL=http://localhost:8000
   API_TIMEOUT=30
   ```

## ▶️ Running the Application

### Option 1: Using PowerShell Script (Recommended for Windows)

```powershell
.\start.ps1
```

This script will:
- Check Python installation
- Verify dependencies
- Check API server connectivity
- Launch the application

### Option 2: Direct Python Run

```bash
python run.py
```

### Option 3: Direct App Launch

```bash
python app.py
```

## 🎮 Using the CLI

### Main Dashboard

The main screen shows:
- **Left Panel**: List of active workflows with status, progress, and task counts
- **Right Panel**: Tabbed view with workflow details, tasks, logs, and system metrics

### Keyboard Shortcuts

| Key | Action |
|-----|--------|
| `n` | Create new workflow |
| `r` | Refresh workflow list |
| `q` | Quit application |
| `Enter` | View workflow details |
| `p` | Pause selected workflow |
| `Ctrl+C` | Resume paused workflow |
| `d` | Delete/Cancel workflow |
| `↑/↓` | Navigate workflows |
| `Tab` | Switch between panels |

### Creating a Workflow

1. Press `n` or click the "➕ New" button
2. Enter your strategy request (e.g., "Create RSI strategy with 30/70 levels")
3. Press Enter or click "Create"
4. The workflow will appear in the list and start executing automatically

### Monitoring Workflows

- **Status Indicators**: Color-coded status (🟢 running, ⏸️ paused, ✅ completed, ❌ failed)
- **Progress Bars**: Real-time progress updates
- **Task List**: View individual task status and agent assignments
- **Logs**: Live log stream of system events

### Workflow Controls

- **Pause**: Select a workflow and press `p` to pause execution
- **Resume**: Press `Ctrl+C` to resume a paused workflow
- **Delete**: Press `d` to cancel and delete a workflow
- **Refresh**: Press `r` to manually refresh the workflow list

## 🎨 Theme Features

The **Luminous Theme** provides:
- Bright, glowing cyan and magenta accents
- High contrast for better readability
- Color-coded status indicators
- Smooth animations and transitions
- Dark background with vibrant highlights

## 🔧 Troubleshooting

### "Cannot connect to API" Error

1. Ensure the AlgoAgent API server is running:
   ```bash
   cd ../AlgoAgent
   python -m uvicorn multi_agent.api_server:app --host 0.0.0.0 --port 8000
   ```

2. Check the API URL in `.env` matches your server configuration

3. Verify the server is accessible:
   ```bash
   curl http://localhost:8000/health
   ```

### Dependencies Not Found

Install all requirements:
```bash
pip install -r requirements.txt
```

### Python Version Issues

Ensure Python 3.8+:
```bash
python --version
```

## 📊 API Endpoints Used

The CLI integrates with these API endpoints:

- `GET /health` - Health check
- `POST /api/workflows/` - Create workflow
- `GET /api/workflows/` - List workflows
- `GET /api/workflows/{id}/` - Get workflow status
- `PATCH /api/workflows/{id}/pause/` - Pause workflow
- `PATCH /api/workflows/{id}/resume/` - Resume workflow
- `DELETE /api/workflows/{id}/` - Cancel workflow
- `GET /api/workflows/{id}/tasks/` - Get workflow tasks
- `GET /api/system/info` - System information

## 🌟 Features

- ✨ **Real-time Updates**: Auto-refreshes every 5 seconds
- 🎯 **Interactive Dashboard**: Full keyboard and mouse control
- 📈 **Progress Tracking**: Visual progress bars for each workflow
- 🔍 **Detailed Views**: Task-level monitoring and logs
- 🎨 **Beautiful UI**: Luminous theme with glowing effects
- ⚡ **Fast Performance**: Async API calls for smooth operation

## 📝 Tips

1. **Auto-refresh**: The workflow list refreshes automatically every 5 seconds
2. **Tab Navigation**: Use Tab key to switch between tabs in the detail panel
3. **Keyboard First**: All operations can be performed with keyboard shortcuts
4. **Multiple Workflows**: Create and monitor multiple workflows simultaneously
5. **Live Logs**: The log tab shows real-time system events and API responses

## 🆘 Support

For issues or questions:
1. Check the logs in the "Logs" tab
2. Verify API server is running and accessible
3. Check system metrics in the "Metrics" tab
4. Review the API documentation in `../AlgoAgent/multi_agent/docs/api/`

---

**Enjoy your multi-agent workflow management! 🚀**
