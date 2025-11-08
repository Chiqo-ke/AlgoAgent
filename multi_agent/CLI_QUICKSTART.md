# Multi-Agent System CLI - Quick Start Guide

## Overview

The CLI provides an interactive command-line interface for submitting strategy requests and monitoring workflows in the multi-agent system.

## Installation

No additional installation needed. The CLI uses existing dependencies.

## Usage

### 1. Interactive Mode (Recommended)

Start the CLI in interactive mode:

```cmd
cd C:\Users\nyaga\Documents\AlgoAgent\multi_agent
C:\Users\nyaga\Documents\AlgoAgent\.venv\Scripts\python.exe cli.py
```

**Available Commands:**
- `submit <request>` - Submit a new strategy request
- `status <workflow_id>` - Check workflow status
- `list` - List all workflows
- `help` - Show help
- `exit` - Exit CLI

**Example Session:**
```
>>> submit Create RSI strategy with buy below 30, sell above 70
📝 Request: Create RSI strategy with buy below 30, sell above 70
...
✅ Submitted: workflow_20251108_120000

>>> list
📂 Available Workflows:
   📄 workflow_20251108_120000
      Name: CLI: Create RSI strategy...
      Tasks: 1

>>> status workflow_20251108_120000
🔍 Checking status: workflow_20251108_120000
📊 Workflow: workflow_20251108_120000
   Status: queued

>>> exit
👋 Goodbye!
```

### 2. Single Command Mode

Submit a single request and exit:

```cmd
python cli.py --request "Create MACD crossover strategy"
```

Check workflow status:

```cmd
python cli.py --status workflow_20251108_120000
```

List all workflows:

```cmd
python cli.py --list
```

### 3. PowerShell/CMD Direct Commands

You can also run commands directly:

**Submit Request:**
```cmd
cd C:\Users\nyaga\Documents\AlgoAgent\multi_agent
C:\Users\nyaga\Documents\AlgoAgent\.venv\Scripts\python.exe cli.py --request "Create Bollinger Bands mean reversion strategy"
```

**Check Status:**
```cmd
C:\Users\nyaga\Documents\AlgoAgent\.venv\Scripts\python.exe cli.py --status workflow_20251108_120000
```

**List Workflows:**
```cmd
C:\Users\nyaga\Documents\AlgoAgent\.venv\Scripts\python.exe cli.py --list
```

## Features

### AI Mode vs Template Mode

The CLI automatically detects if `GOOGLE_API_KEY` is set in the `.env` file:

- **AI Mode** (✅ if API key present): Uses Gemini API to generate TodoLists
- **Template Mode** (📋 if no API key): Uses predefined templates

### Workflow Management

1. **Submit Request**: Generates TodoList and loads into Orchestrator
2. **Track Progress**: Check workflow status and task completion
3. **List History**: View all submitted workflows

### Output Files

All workflows are saved to: `C:\Users\nyaga\Documents\AlgoAgent\multi_agent\workflows/`

Files created:
- `<workflow_id>_todolist.json` - Generated TodoList
- (Additional artifacts created by agents during execution)

## Example Use Cases

### Example 1: Simple RSI Strategy

```cmd
>>> submit Create simple RSI strategy: buy when RSI < 30, sell when RSI > 70
```

### Example 2: MACD Crossover

```cmd
>>> submit Implement MACD crossover strategy with 12/26/9 periods, buy on bullish cross, sell on bearish cross
```

### Example 3: Moving Average Strategy

```cmd
>>> submit Create MA crossover: buy when 50-day MA crosses above 200-day MA, sell on opposite cross
```

### Example 4: Bollinger Bands

```cmd
>>> submit Build Bollinger Bands strategy: buy when price touches lower band, sell at upper band, 20-period, 2 std dev
```

## Command Reference

### submit <request>

Submit a new strategy request.

**Arguments:**
- `<request>`: Natural language description of the strategy

**Example:**
```cmd
>>> submit Create momentum strategy using RSI and volume
```

**Output:**
- Workflow ID
- TodoList with tasks
- Status (queued/failed)

### status <workflow_id>

Check the status of a workflow.

**Arguments:**
- `<workflow_id>`: Workflow identifier (e.g., `workflow_20251108_120000`)

**Example:**
```cmd
>>> status workflow_20251108_120000
```

**Output:**
- Workflow status (pending/running/completed/failed)
- Task details with status icons
- Results (if available)

### list

List all workflows in the system.

**Example:**
```cmd
>>> list
```

**Output:**
- List of all workflows
- Workflow names and IDs
- Creation timestamps
- Number of tasks

### help

Show available commands.

### exit / quit

Exit the CLI.

## Status Icons

- ⏳ Pending - Task queued, not started
- 🔄 Running - Task currently executing
- ✅ Completed - Task finished successfully
- ❌ Failed - Task failed with error

## Troubleshooting

### API Key Not Found

If you see `📋 Template Mode: ENABLED`, the system couldn't find `GOOGLE_API_KEY` in `.env`.

**Solution:**
1. Check `.env` file exists: `C:\Users\nyaga\Documents\AlgoAgent\.env`
2. Verify `GOOGLE_API_KEY=<your-key>` is set
3. Restart CLI

### Workflow Not Found

If `status` command shows "Workflow not found":

**Possible Reasons:**
1. Workflow ID incorrect - use `list` to see available workflows
2. Workflow not loaded into Orchestrator yet
3. Workflow file deleted

**Solution:**
```cmd
>>> list
>>> status <correct_workflow_id>
```

### Import Errors

If you get import errors:

**Solution:**
```cmd
cd C:\Users\nyaga\Documents\AlgoAgent\multi_agent
C:\Users\nyaga\Documents\AlgoAgent\.venv\Scripts\python.exe cli.py
```

Make sure to:
1. Run from `multi_agent` directory
2. Use full path to Python in `.venv`

## Advanced Usage

### Batch Processing

Create a script to submit multiple requests:

**batch_submit.ps1:**
```powershell
$requests = @(
    "Create RSI strategy with buy<30, sell>70",
    "Create MACD crossover strategy",
    "Create Bollinger Bands mean reversion"
)

foreach ($req in $requests) {
    python cli.py --request $req
    Start-Sleep -Seconds 2
}
```

### Monitoring Loop

Monitor workflow status in a loop:

**monitor.ps1:**
```powershell
$workflowId = "workflow_20251108_120000"

while ($true) {
    Clear-Host
    python cli.py --status $workflowId
    Start-Sleep -Seconds 5
}
```

## Next Steps

After submitting a request through the CLI:

1. **Orchestrator** loads the workflow and queues tasks
2. **Coder Agent** generates strategy code (if task assigned)
3. **Tester Agent** validates code (if Docker available)
4. **Artifact Store** commits results to Git

Check the following documentation:
- `E2E_TEST_REPORT.md` - System capabilities
- `AI_E2E_TEST_FINAL_REPORT.md` - AI testing results
- `QUICKSTART.md` - Full system setup

## Support

For issues or questions:
1. Check test reports for system status
2. Review error messages in CLI output
3. Verify `.env` configuration
4. Check `workflows/` directory for generated files

---

**Last Updated:** November 8, 2025  
**Version:** 1.0.0  
**Status:** ✅ Ready for use
