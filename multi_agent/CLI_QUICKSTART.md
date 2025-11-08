# Multi-Agent System CLI - Quick Start Guide

## Overview

The CLI provides an interactive command-line interface for submitting strategy requests, executing AI-powered workflows, and monitoring multi-agent task execution. The system automatically generates TodoLists, contracts, and strategy code using Gemini AI with template fallback.

## Features

### 🤖 AI-Powered Workflow Generation
- **Gemini API Integration**: Automatically generates valid TodoLists from natural language
- **Schema-Aware**: Includes complete JSON schema documentation in prompts
- **Validation Loop**: AI sees errors and retries with specific fixes
- **Template Fallback**: Gracefully falls back to template mode if AI fails

### 🔧 Multi-Agent Execution
- **Architect Agent**: Designs contracts, interfaces, and test specifications
- **Coder Agent**: Implements code following contracts with Gemini AI or template
- **Auto-Contract Generation**: Creates contracts automatically for tasks
- **Async Support**: Properly handles async agent methods

### 📋 Workflow Management
- **Submit Requests**: Natural language strategy descriptions
- **Execute Workflows**: Runs all tasks with appropriate agents
- **Status Tracking**: Check workflow progress
- **Artifact Generation**: Produces strategy code, contracts, fixtures

### 💾 Persistent Storage
- **TodoLists**: Saved to `workflows/workflow_*.json`
- **Contracts**: Saved to `workflows/contract_*.json`
- **Code Artifacts**: Generated in `Backtest/codes/`

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
- `execute <id>` - Execute workflow tasks with appropriate agents
- `status <workflow_id>` - Check workflow status
- `list` - List all workflows
- `help` - Show help
- `exit` - Exit CLI
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

## AI-Powered Features

### AI Mode vs Template Mode

The CLI automatically detects if `GEMINI_API_KEY` or `GOOGLE_API_KEY` is set in the `.env` file:

- **🤖 AI Mode** (if API key present): 
  - Uses Gemini API to generate custom TodoLists
  - Schema-aware with validation loop
  - Generates contracts with Architect Agent
  - Creates custom code with Coder Agent
  - Falls back to template if quota exceeded or safety filters triggered
  
- **📋 Template Mode** (if no API key): 
  - Uses predefined TodoList templates
  - Auto-generates contracts for tasks
  - Coder Agent uses template-based code generation
  - Reliable fallback mode

### Multi-Agent Workflow

The CLI orchestrates multiple specialized agents:

1. **Planner Service** (AI-powered)
   - Converts natural language to TodoList
   - Generates 4-step workflow (Data → Indicators → Entry → Exit)
   - Validates against JSON schema
   - Retries with error feedback

2. **Architect Agent** (for indicator tasks)
   - Designs interfaces and contracts
   - Generates test skeletons
   - Creates fixture specifications
   - Outputs: `contracts/contract_*.json`

3. **Coder Agent** (for implementation tasks)
   - Implements code following contracts
   - Generates strategy files
   - Creates test fixtures
   - Outputs: `Backtest/codes/ai_strategy_*.py`

4. **Orchestrator**
   - Manages workflow state
   - Routes tasks to agents
   - Handles dependencies
   - Tracks execution progress

### Workflow Execution Flow

```
User Request → Planner (AI) → TodoList (4 tasks)
                                    ↓
                              Orchestrator
                                    ↓
                  ┌─────────────────┴─────────────────┐
                  ↓                                   ↓
          Architect Agent                      Coder Agent
     (designs contracts)                  (implements code)
                  ↓                                   ↓
         contract_*.json                  ai_strategy_*.py
```

### Auto-Contract Generation

When executing workflows, the CLI automatically:
- Creates contracts for tasks missing `contract_path`
- Saves contracts to `workflows/contract_<task_id>.json`
- Passes contracts to Coder Agent
- Enables proper interface-driven development

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

### Example 1: Simple RSI Strategy (Auto-Execute)

```cmd
python cli.py --request "Create simple RSI strategy: buy when RSI < 30, sell when RSI > 70" --run
```

**Output:**
```
✓ TodoList created (4 tasks)
✓ Workflow loaded: wf_abc123
🔄 Auto-executing workflow...
  ✓ task_data_loading completed
  ✓ task_indicators completed (Architect Agent)
  ✓ task_entry completed
  ✓ task_exit completed
✅ Execution complete!
```

### Example 2: MACD Crossover with Architect

```cmd
>>> submit Create MACD crossover strategy with 12/26/9 parameters
```

**Generated Workflow:**
1. **Data Loading** (Coder) - Implements `fetch_and_prepare_data()`
2. **Indicators** (Architect) - Designs MACD contract and interfaces
3. **Entry Conditions** (Coder) - Implements MACD bullish cross logic
4. **Exit Conditions** (Coder) - Implements bearish cross + SL/TP

### Example 3: EMA Crossover with Custom Parameters

```cmd
>>> submit Create EMA crossover: buy when 30 EMA crosses above 50 EMA, stop loss 10 pips, take profit 40 pips
```

### Example 4: Bollinger Bands Mean Reversion

```cmd
>>> submit Build Bollinger Bands strategy: buy when price touches lower band, sell at upper band, 20-period, 2 std dev
```

### Example 5: Execute Existing Workflow

```cmd
>>> execute wf_abc123
```

Or in single command:
```cmd
python cli.py --execute wf_abc123
```

## Detailed Command Reference

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

## Troubleshooting

### API Quota Exceeded (429 Error)

**Symptom:**
```
ERROR: 429 You exceeded your current quota, please check your plan and billing details
```

**Causes:**
- Gemini API free tier limit: 50 requests/day
- Multiple workflow submissions in short time
- Previous test runs exhausted quota

**Solutions:**

1. **Wait for Quota Reset** (Recommended)
   - Free tier resets every 24 hours
   - Error message includes retry delay (e.g., "Please try again in 45s")
   
2. **Use Template Mode** (Immediate)
   - System automatically falls back to template generation
   - Coder Agent: Always has template fallback
   - Planner: Creates 4-task template TodoList
   - **Note:** Architect Agent currently lacks template fallback (AI-only)

3. **Upgrade API Tier** (Long-term)
   - Switch to paid Gemini API tier for higher quotas
   - Update `.env` with new API key

**Prevention:**
- Track daily API usage
- Use `--run` sparingly during testing
- Develop with template mode when building/debugging

### Safety Filter Triggered (finish_reason=2)

**Symptom:**
```
⚠ AI response blocked by safety filter (finish_reason: SAFETY)
```

**Causes:**
- Gemini API safety filters reject prompt as potentially harmful
- Sensitive keywords in strategy description
- Misinterpreted intent

**Solutions:**
- Rephrase request with neutral language
- Avoid terms like "attack", "exploit", "hack"
- Focus on technical trading terms

### Invalid TodoList Schema

**Symptom:**
```
❌ Validation failed: 'acceptance_criteria' is a required property
```

**Causes:**
- AI generated incomplete TodoList
- Schema validation failed

**Solutions:**
- System automatically retries with error feedback
- AI receives specific fix instructions
- After 3 retries, falls back to template mode
- **Expected:** Schema awareness improvements mean this rarely happens

### Architect Agent Initialization Error

**Symptom:**
```
ERROR: Failed to initialize Architect Agent
```

**Causes:**
- Missing `GEMINI_API_KEY` in `.env`
- Invalid API key format
- Network connectivity issues

**Solutions:**
1. Verify `.env` file:
   ```
   GEMINI_API_KEY=AIzaSy...your_key
   ```
2. Test API key with simple request:
   ```cmd
   python cli.py --request "Simple test" --run
   ```
3. Check network connection

### Workflow Not Found

**Symptom:**
```
ERROR: Workflow wf_xyz123 not found
```

**Causes:**
- In-memory Orchestrator (no cross-session persistence)
- Workflow created in different CLI session
- Invalid workflow ID

**Solutions:**
- List available workflows:
  ```cmd
  >>> list
  ```
- Submit new workflow if needed
- **Note:** Persistence layer planned for future release

### File Not Found / Import Errors in Generated Code

**Symptom:**
```
ModuleNotFoundError: No module named 'strategies.templates'
```

**Causes:**
- Generated code uses absolute imports
- Missing `__init__.py` files
- Code not in Python path

**Solutions:**
- Generated code saves to `Backtest/codes/`
- Ensure directory structure:
  ```
  AlgoAgent/
    Backtest/
      codes/
        ai_strategy_*.py
  ```
- Import code with proper paths

## Best Practices

### API Quota Management

1. **Plan Requests:**
   - Each `submit` uses 1-2 requests (Planner)
   - Each Architect task uses 1-2 requests
   - Each Coder task with AI uses 1 request
   - Complete workflow: ~4-6 requests total

2. **Daily Budget:**
   - Free tier: ~8-10 workflows/day
   - Save complex requests for production runs

3. **Development Strategy:**
   - Use template mode for development
   - Test with AI mode for validation
   - Reserve quota for production workflows

### Workflow Execution

1. **Incremental Development:**
   ```cmd
   >>> submit [description]  # Generate TodoList
   >>> status                # Review tasks
   >>> execute [id]          # Execute when ready
   ```

2. **Quick Testing:**
   ```cmd
   python cli.py --request "[description]" --run
   ```

3. **Review Before Execution:**
   - Check generated TodoList (`.json` file in `workflows/`)
   - Verify task priorities and dependencies
   - Ensure acceptance criteria make sense

### Multi-Agent Workflows

1. **Architect + Coder Pattern:**
   - Architect designs contracts for complex components (indicators, risk management)
   - Coder implements simple logic (entry/exit, data loading)
   - Review generated contracts before Coder implementation

2. **Task Dependencies:**
   - Data loading → Indicators → Entry → Exit
   - Respect execution order
   - Dependencies automatically enforced by Orchestrator

3. **Contract Management:**
   - Auto-generated contracts save to `workflows/contract_*.json`
   - Review before Coder Agent uses them
   - Modify contracts if needed (manual edit)

## Tips

- 💡 **Start Simple:** Test with basic strategies first (RSI, MA crossover)
- 💡 **Use `--run` Sparingly:** Reserve API quota for production workflows
- 💡 **Review TodoLists:** Check generated JSON before execution
- 💡 **Template Mode:** Reliable fallback when AI unavailable
- 💡 **Architect for Complexity:** Use Architect Agent for indicators/risk management
- 💡 **Track Workflows:** Use `list` and `status` commands frequently

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
