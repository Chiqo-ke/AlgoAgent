# AlgoCLI - Multi-Agent Workflow CLI

A stunning Textual-based CLI interface for managing AI-driven trading strategy workflows.

## Features

- 🌟 **Luminous Theme** - Beautiful glowing interface with vibrant colors
- 🚀 **Real-time Updates** - Live workflow status and event streaming
- 📊 **Interactive Dashboard** - Monitor multiple workflows simultaneously
- 🔄 **Workflow Control** - Create, pause, resume, and cancel workflows
- 📝 **Task Monitoring** - Track individual task progress and results
- 🎨 **Rich UI** - Modern terminal interface with smooth animations

## Installation

```bash
cd AlgoCLI
pip install -r requirements.txt
```

## Configuration

Copy `.env.example` to `.env` and configure your API endpoint:

```bash
cp .env.example .env
```

## Usage

```bash
python app.py
```

### Keyboard Shortcuts

- `n` - Create new workflow
- `r` - Refresh workflow list
- `q` - Quit application
- `↑/↓` - Navigate workflows
- `Enter` - View workflow details
- `p` - Pause selected workflow
- `Ctrl+C` - Resume paused workflow
- `d` - Delete/Cancel workflow

## API Requirements

The CLI requires the AlgoAgent multi-agent API server running on port 8000:

```bash
cd ../AlgoAgent
python -m uvicorn multi_agent.api_server:app --host 0.0.0.0 --port 8000
```

## Screenshots

The CLI features:
- Dashboard with workflow list
- Real-time task progress bars
- Color-coded status indicators
- Live event log stream
- Interactive workflow creation dialog

## License

MIT
