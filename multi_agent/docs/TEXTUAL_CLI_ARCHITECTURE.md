# Textual CLI Integration Architecture

## Overview

This document describes the architecture for integrating the multi-agent trading strategy development system with a Textual-based CLI and Django REST backend, enabling real-time workflow monitoring, interactive agent control, and seamless user interaction.

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         Textual CLI (TUI)                           │
│  ┌────────────────┬────────────────┬─────────────────┬───────────┐ │
│  │  Workflow      │  Agent         │  Task           │   Logs    │ │
│  │  Dashboard     │  Activity Feed │  Progress       │  Viewer   │ │
│  └────────────────┴────────────────┴─────────────────┴───────────┘ │
│          │                    │                    │                │
│          └────────────── HTTP REST + WebSocket ────────────────────┘
│
├─────────────────────────────────────────────────────────────────────┤
│                   Django REST Backend (Port 8000)                   │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │  Workflow API (NEW)                                          │  │
│  │  - POST /api/workflows/          (Submit strategy request)   │  │
│  │  - GET  /api/workflows/{id}/     (Get workflow status)       │  │
│  │  - GET  /api/workflows/          (List workflows)            │  │
│  │  - PATCH /api/workflows/{id}/pause/   (Pause)                │  │
│  │  - PATCH /api/workflows/{id}/resume/  (Resume)               │  │
│  │  - DELETE /api/workflows/{id}/   (Cancel)                    │  │
│  │  - GET  /api/workflows/{id}/tasks/    (Get task details)     │  │
│  │  - GET  /api/workflows/{id}/events/   (Get event history)    │  │
│  │  - WS   /ws/workflows/{id}/      (Real-time event stream)    │  │
│  └─────────────────┬────────────────────────────────────────────┘  │
│                    │                                                │
│  ┌─────────────────▼────────────────────────────────────────────┐  │
│  │  Backend Bridge Service (NEW)                                │  │
│  │  ┌────────────────────────────────────────────────────────┐  │  │
│  │  │  MessageBusListener                                    │  │  │
│  │  │  - Subscribes to workflow.lifecycle                   │  │  │
│  │  │  - Subscribes to task.updates                         │  │  │
│  │  │  - Subscribes to agent.results                        │  │  │
│  │  │  - Subscribes to test.results                         │  │  │
│  │  │  - Subscribes to artifact.events                      │  │  │
│  │  │  - Subscribes to approval.requests                    │  │  │
│  │  └────────────────────────────────────────────────────────┘  │  │
│  │  ┌────────────────────────────────────────────────────────┐  │  │
│  │  │  EventForwarder                                        │  │  │
│  │  │  - Forwards events to Django Channels                 │  │  │
│  │  │  - Manages WebSocket group broadcasts                 │  │  │
│  │  │  - Sends heartbeats and error messages                │  │  │
│  │  └────────────────────────────────────────────────────────┘  │  │
│  │  ┌────────────────────────────────────────────────────────┐  │  │
│  │  │  OrchestratorClient                                    │  │  │
│  │  │  - submit_workflow(request, auto_execute, ...)        │  │  │
│  │  │  - get_workflow_status(workflow_id)                   │  │  │
│  │  │  - pause_workflow(workflow_id)                        │  │  │
│  │  │  - resume_workflow(workflow_id)                       │  │  │
│  │  │  - cancel_workflow(workflow_id)                       │  │  │
│  │  │  - list_workflows(user_id, status, limit)             │  │  │
│  │  └────────────────────────────────────────────────────────┘  │  │
│  └─────────────────┬────────────────────────────────────────────┘  │
└────────────────────┼───────────────────────────────────────────────┘
                     │ Redis Message Bus
┌────────────────────▼───────────────────────────────────────────────┐
│                   Multi-Agent System                               │
│  ┌──────────────┬──────────────┬──────────────┬──────────────┐    │
│  │ Orchestrator │  Message Bus │   Planner    │   Agents     │    │
│  │              │   (Redis)    │              │  - Coder     │    │
│  │  - Workflow  │              │  - TodoList  │  - Tester    │    │
│  │    dispatch  │  - Channels: │    generator │  - Debugger  │    │
│  │  - Task      │    · workflow│  - Gemini    │  - Architect │    │
│  │    tracking  │    · task    │    API       │              │    │
│  │  - State     │    · agent   │              │  - LLM       │    │
│  │    mgmt      │    · test    │              │    router    │    │
│  │  - Auto-fix  │    · artifact│              │  - Learning  │    │
│  └──────────────┴──────────────┴──────────────┴──────────────┘    │
│                                                                     │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │  Artifact Store                                              │ │
│  │  - Backtest/codes/*.py     (Generated strategies)            │ │
│  │  - tests/*.py              (Test files)                      │ │
│  │  - artifacts/*.csv         (Backtest results)                │ │
│  │  - Git branches: ai/generated/{workflow}/{task}              │ │
│  └──────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
```

## Component Responsibilities

### 1. Textual CLI (User Interface)

**Location:** `AlgoAgent/multi_agent/textual_cli/`

**Purpose:** Rich terminal UI for workflow interaction

**Features:**
- Multi-panel dashboard (workflows, agents, tasks, logs)
- Real-time event streaming display
- Keyboard-driven navigation
- Interactive workflow controls
- Artifact browsing
- Agent health monitoring

**Key Interactions:**
- HTTP REST calls to Django backend for CRUD operations
- WebSocket connection for real-time event streaming
- JWT authentication with token refresh
- Graceful reconnection on network failures

---

### 2. Django REST Backend (API Layer)

**Location:** `RMS-Backend-main/backend2/workflow_api/` (NEW)

**Purpose:** RESTful API and WebSocket gateway

**Components:**

#### Models
```python
class Workflow(models.Model):
    workflow_id = CharField(primary_key=True)
    user = ForeignKey(User)
    request = TextField()
    status = CharField(choices=WorkflowStatus)
    created_at = DateTimeField(auto_now_add=True)
    todo_list = JSONField()
    auto_fix_mode = BooleanField()
    
class Task(models.Model):
    task_id = CharField(primary_key=True)
    workflow = ForeignKey(Workflow)
    description = TextField()
    agent = CharField()
    status = CharField(choices=TaskStatus)
    started_at = DateTimeField(null=True)
    completed_at = DateTimeField(null=True)
    
class Event(models.Model):
    event_id = CharField(primary_key=True)
    workflow = ForeignKey(Workflow)
    event_type = CharField()
    timestamp = DateTimeField()
    data = JSONField()
```

#### ViewSets
```python
class WorkflowViewSet(viewsets.ModelViewSet):
    def create(request):      # POST /api/workflows/
    def retrieve(pk):         # GET /api/workflows/{id}/
    def list():               # GET /api/workflows/
    @action def pause(pk):    # PATCH /api/workflows/{id}/pause/
    @action def resume(pk):   # PATCH /api/workflows/{id}/resume/
    def destroy(pk):          # DELETE /api/workflows/{id}/
    @action def tasks(pk):    # GET /api/workflows/{id}/tasks/
    @action def events(pk):   # GET /api/workflows/{id}/events/
```

#### WebSocket Consumer
```python
class WorkflowConsumer(AsyncWebsocketConsumer):
    async def connect():
        # Authenticate JWT token
        # Join workflow-specific channel group
        # Send initial workflow status
        
    async def workflow_event(event):
        # Receive event from EventForwarder
        # Send to WebSocket client
        
    async def disconnect():
        # Leave channel group
```

---

### 3. Backend Bridge (Integration Layer)

**Location:** `AlgoAgent/multi_agent/backend_bridge/`

**Purpose:** Bridge multi-agent system with Django backend

**Components:**

#### MessageBusListener
- Subscribes to all 6 message bus channels
- Routes events to EventForwarder
- Logs agent activity for monitoring
- Handles event filtering and transformation

#### EventForwarder
- Forwards events to Django Channels layer
- Manages WebSocket group broadcasts
- Sends heartbeats (every 30s)
- Handles error messaging

#### OrchestratorClient
- High-level API for workflow management
- Wraps Orchestrator and Planner services
- Publishes lifecycle events
- Provides user-friendly interface

---

### 4. Multi-Agent System (Core Logic)

**Location:** `AlgoAgent/multi_agent/`

**Purpose:** AI-driven strategy development

**No Changes Required** - existing implementation is compatible

**Event Flow:**
1. Orchestrator receives workflow from OrchestratorClient
2. Dispatches tasks to agents via message bus
3. Agents publish progress events (TASK_STARTED, TASK_PROGRESS, etc.)
4. MessageBusListener captures events
5. EventForwarder broadcasts to WebSocket clients
6. Textual CLI displays real-time updates

---

## Message Flow Sequences

### Sequence 1: Workflow Submission

```
User (Textual CLI)
    │
    │ 1. Type strategy request
    │ "Create RSI strategy with 30/70 levels"
    │
    ├──HTTP POST──> Django Backend (/api/workflows/)
    │                   │
    │                   │ 2. Validate request & authenticate
    │                   │
    │                   ├──> OrchestratorClient.submit_workflow()
    │                   │        │
    │                   │        │ 3. Planner generates TodoList
    │                   │        │
    │                   │        ├──> Orchestrator.create_workflow()
    │                   │        │        │
    │                   │        │        │ 4. Publish WORKFLOW_CREATED
    │                   │        │        │
    │                   │        │        └──> Message Bus (workflow.lifecycle)
    │                   │        │                  │
    │                   │        │                  ├──> MessageBusListener
    │                   │        │                  │        │
    │                   │        │                  │        └──> EventForwarder
    │                   │        │                  │                  │
    │                   │        │                  │                  └──> Django Channels
    │                   │        │                  │
    │                   │        │ 5. Start execution (if auto_execute)
    │                   │        │
    │                   │        └──> Orchestrator.execute_workflow()
    │                   │
    │                   │ 6. Save to database (Workflow model)
    │                   │
    │<──HTTP 201──────┤
    │   {workflow_id, status, todo_list}
    │
    │ 7. Connect WebSocket for real-time updates
    │
    ├──WS CONNECT──> Django Backend (/ws/workflows/{id}/)
    │                   │
    │                   │ Join channel group: "workflow_{id}"
    │                   │
    │<──WS CONNECTED──┤
    │
    │ 8. Receive real-time events
    │
    │<──WS MESSAGE────┤ {"event_type": "TASK_DISPATCHED", ...}
    │<──WS MESSAGE────┤ {"event_type": "TASK_STARTED", ...}
    │<──WS MESSAGE────┤ {"event_type": "TASK_COMPLETED", ...}
```

### Sequence 2: Real-Time Event Streaming

```
Coder Agent                Message Bus              MessageBusListener       EventForwarder      Django Channels      Textual CLI
    │                           │                           │                       │                   │                  │
    │ 1. Complete task          │                           │                       │                   │                  │
    │                           │                           │                       │                   │                  │
    ├─PUBLISH───────────────────>│ TASK_COMPLETED          │                       │                   │                  │
    │   (agent.results)          │                           │                       │                   │                  │
    │                            │                           │                       │                   │                  │
    │                            ├─SUBSCRIBE CALLBACK───────>│                       │                   │                  │
    │                            │                           │                       │                   │                  │
    │                            │                           │ 2. Handle event       │                   │                  │
    │                            │                           │                       │                   │                  │
    │                            │                           ├─forward_event()──────>│                   │                  │
    │                            │                           │                       │                   │                  │
    │                            │                           │                       │ 3. Serialize      │                  │
    │                            │                           │                       │                   │                  │
    │                            │                           │                       ├─group_send()─────>│                  │
    │                            │                           │                       │  (workflow_{id})  │                  │
    │                            │                           │                       │                   │                  │
    │                            │                           │                       │                   │ 4. Broadcast     │
    │                            │                           │                       │                   │                  │
    │                            │                           │                       │                   ├─WS SEND─────────>│
    │                            │                           │                       │                   │                  │
    │                            │                           │                       │                   │                  │ 5. Update UI
    │                            │                           │                       │                   │                  │ (Task: ✓)
```

### Sequence 3: Workflow Control (Pause)

```
User (Textual CLI)
    │
    │ 1. Press 'p' to pause
    │
    ├──HTTP PATCH──> Django Backend (/api/workflows/{id}/pause/)
    │                    │
    │                    │ 2. Validate state transition
    │                    │
    │                    ├──> OrchestratorClient.pause_workflow()
    │                    │        │
    │                    │        │ 3. Update workflow status
    │                    │        │
    │                    │        ├──> Orchestrator (status = PAUSED)
    │                    │        │
    │                    │        │ 4. Publish WORKFLOW_PAUSED event
    │                    │        │
    │                    │        └──> Message Bus
    │                    │                 │
    │                    │                 └──> EventForwarder ──> WebSocket
    │                    │
    │<──HTTP 200────────┤
    │   {status: "paused"}
    │
    │<──WS MESSAGE──────┤ {"event_type": "WORKFLOW_PAUSED"}
    │
    │ 5. Display "Workflow Paused" in UI
```

---

## User Interaction Points

### When Users Can Interact with Multi-Agent System

#### 1. **Workflow Submission** (Primary Entry Point)

**When:** Anytime user wants to create a new trading strategy

**How:**
- Textual CLI: Type natural language request in submission panel
- Example: "Create RSI strategy with 30/70 levels and 50 SMA filter"

**System Actions:**
- Planner converts request to TodoList
- Orchestrator creates workflow
- Auto-execution begins (if enabled)

**User Sees:**
- Workflow ID assigned
- TodoList tasks displayed
- Progress indicators appear

---

#### 2. **Real-Time Monitoring** (Passive Interaction)

**When:** Workflow is running

**How:**
- Textual CLI automatically streams events via WebSocket
- No user action required

**User Sees:**
- Agent activity feed (thinking, actions, errors)
- Task progress bars
- Test results as they complete
- Artifact creation notifications
- Log stream with timestamps

**UI Updates:**
```
[10:30:15] TASK_DISPATCHED   → Coder Agent: Generate RSI strategy
[10:30:16] AGENT_THINKING    → Analyzing RSI indicator requirements
[10:32:45] TASK_COMPLETED    → ✓ strategy_rsi.py created
[10:32:50] TEST_STARTED      → Running pytest in Docker sandbox
[10:33:15] TEST_PASSED       → ✓ 12 tests passed, coverage 92%
```

---

#### 3. **Workflow Control** (Active Interaction)

**When:** User wants to pause, resume, or cancel

**How:**
- Keyboard shortcuts:
  - `p` = Pause current workflow
  - `r` = Resume paused workflow
  - `c` = Cancel workflow
  - `Enter` = View task details

**System Actions:**
- State transition (RUNNING → PAUSED → RUNNING)
- Event broadcast to all connected clients
- In-progress tasks complete before pausing

**User Sees:**
- Status change indicator
- Confirmation message
- Updated workflow list

---

#### 4. **Task Drill-Down** (Exploratory Interaction)

**When:** User wants details about a specific task

**How:**
- Navigate to task in list
- Press `Enter` or `d` for details

**User Sees:**
```
┌─ Task Details: task_1 ─────────────────────────────┐
│ Description: Generate RSI strategy with indicators  │
│ Agent: coder_agent                                  │
│ Status: ✓ COMPLETED                                 │
│ Started: 2026-01-07 10:30:15                        │
│ Duration: 185 seconds                               │
│ Retry Count: 0                                      │
│                                                     │
│ Artifacts:                                          │
│   • strategy_rsi.py (4.5 KB)                        │
│   • test_rsi_strategy.py (2.1 KB)                   │
│                                                     │
│ LLM Info:                                           │
│   Model: claude-sonnet-4.5                          │
│   Tokens: 3421                                      │
│   Cost: $0.05                                       │
│                                                     │
│ [v] View Code  [t] Run Tests  [ESC] Close           │
└─────────────────────────────────────────────────────┘
```

---

#### 5. **Artifact Browsing** (Result Inspection)

**When:** Workflow completed or task finished

**How:**
- Navigate to Artifacts panel
- Select file to view
- Press `o` to open in editor

**User Sees:**
```
┌─ Artifacts ─────────────────────────────────────────┐
│ Workflow: wf_20260107_103000_abc123                │
│                                                     │
│ [✓] strategy_rsi.py          4.5 KB   Code         │
│ [✓] test_rsi_strategy.py     2.1 KB   Tests        │
│ [✓] trades.csv               12.3 KB  Results      │
│ [✓] equity_curve.csv         8.7 KB   Results      │
│ [✓] test_report.json         1.2 KB   Report       │
│                                                     │
│ [Enter] View  [o] Open  [d] Download  [ESC] Back    │
└─────────────────────────────────────────────────────┘
```

**Actions:**
- View: Display content in CLI
- Open: Launch external editor ($EDITOR)
- Download: Save to local directory

---

#### 6. **Approval Workflow** (Human-in-Loop)

**When:** Strategy ready for live deployment (requires manual approval)

**How:**
- System pauses at APPROVAL_REQUIRED event
- User reviews test results and code
- Chooses approve/deny

**User Sees:**
```
┌─ APPROVAL REQUIRED ─────────────────────────────────┐
│ Strategy: RSI 30/70                                 │
│ Workflow: wf_20260107_103000_abc123                │
│                                                     │
│ ✓ All tests passed (12/12)                         │
│ ✓ Code coverage: 92%                               │
│ ✓ Security scan: No issues                         │
│ ✓ Backtest return: +15.3%                          │
│                                                     │
│ Ready for LIVE deployment?                         │
│                                                     │
│ [a] Approve  [d] Deny  [v] View Details            │
└─────────────────────────────────────────────────────┘
```

**System Actions:**
- Approval: Proceeds to deployment
- Denial: Workflow marked as completed (no deployment)

---

#### 7. **Error Handling & Auto-Fix** (Transparent Interaction)

**When:** Test fails or task errors occur

**How:**
- If `auto_fix_mode=true`: System handles automatically
- If `auto_fix_mode=false`: User prompted for action

**Auto-Fix Enabled (Default):**
```
[10:35:00] TEST_FAILED       → Entry signal logic error
[10:35:01] AGENT_ACTION      → Debugger analyzing failure
[10:35:15] TASK_DISPATCHED   → Fix task created (task_1_fix_1)
[10:35:20] TASK_STARTED      → Coder Agent: Fixing entry logic
[10:37:30] TASK_COMPLETED    → ✓ Fix applied
[10:37:35] TEST_PASSED       → ✓ All tests passed
```

**Auto-Fix Disabled:**
```
┌─ TEST FAILED ───────────────────────────────────────┐
│ Task: task_2 (Test RSI strategy)                    │
│ Error: AssertionError: Expected profit > 0          │
│                                                     │
│ Failed Test: test_entry_signal                     │
│ Line 45: assert profit > 0, got -150.5             │
│                                                     │
│ Options:                                            │
│ [r] Retry Task                                      │
│ [f] Auto-fix with Debugger                         │
│ [v] View Full Error Log                            │
│ [c] Cancel Workflow                                 │
└─────────────────────────────────────────────────────┘
```

---

#### 8. **Multi-Workflow Management**

**When:** User has multiple strategies in development

**How:**
- Navigate between workflows using tabs or list
- Press `1-9` for quick workflow switching
- Press `n` to create new workflow

**User Sees:**
```
┌─ Active Workflows ──────────────────────────────────┐
│ [1] RSI 30/70       ████████░░ 80%  Running          │
│ [2] MACD Cross      ██████████ 100% Completed        │
│ [3] Bollinger       ███░░░░░░░ 30%  Running          │
│                                                     │
│ [Enter] Focus  [n] New  [d] Delete  [a] Archive     │
└─────────────────────────────────────────────────────┘
```

---

## Key Design Decisions

### 1. **Why Textual for CLI?**
- Rich terminal UI with modern widgets
- Async/await support (perfect for WebSocket)
- Cross-platform (Windows, Linux, macOS)
- No GUI required (works over SSH)
- Keyboard-driven (fast navigation)

### 2. **Why Django Channels for WebSocket?**
- Already using Django REST framework
- Native integration with Django auth
- Channel groups for targeted broadcasting
- Redis backend for scaling
- Production-ready

### 3. **Why Bridge Layer?**
- Decouples multi-agent system from web framework
- Enables multiple frontends (CLI, web, mobile)
- Message bus remains framework-agnostic
- Easy to test components in isolation
- Can run agents without Django

### 4. **Why Event-Driven Architecture?**
- Real-time updates without polling
- Scalable (Redis pub/sub)
- Audit trail (all events logged)
- Replay capability for debugging
- Extensible (add new event types easily)

---

## Implementation Roadmap

### Phase 1: Backend Bridge (Completed)
✅ MessageBusListener implementation
✅ EventForwarder implementation
✅ OrchestratorClient implementation
✅ API documentation (OpenAPI spec)

### Phase 2: Django Integration (Next)
- [ ] Create workflow_api Django app
- [ ] Implement models (Workflow, Task, Event)
- [ ] Implement WorkflowViewSet (REST API)
- [ ] Implement WorkflowConsumer (WebSocket)
- [ ] Add JWT authentication
- [ ] Database migrations

### Phase 3: Textual CLI (Next)
- [ ] Create textual_cli package structure
- [ ] Implement main app layout (panels)
- [ ] HTTP client with auth
- [ ] WebSocket client
- [ ] Workflow submission screen
- [ ] Real-time dashboard

### Phase 4: Advanced Features
- [ ] Keyboard shortcuts
- [ ] Task drill-down
- [ ] Artifact viewer
- [ ] Log filtering
- [ ] Agent health monitoring
- [ ] Multi-workflow tabs

### Phase 5: Polish & Testing
- [ ] Integration tests
- [ ] Error handling
- [ ] Reconnection logic
- [ ] Documentation
- [ ] User guide
- [ ] Demo video

---

## Next Steps

1. **Review architecture** with team
2. **Set up Django project** structure (workflow_api app)
3. **Implement models** and migrations
4. **Create REST API** endpoints
5. **Test WebSocket** event streaming
6. **Build Textual CLI** prototype
7. **Integration testing**
8. **User acceptance testing**

---

## Questions & Decisions

1. **Database choice** for production?
   - Recommended: PostgreSQL (JSON support)
   - Alternative: SQLite (development only)

2. **Redis deployment**?
   - Local: Redis server on localhost
   - Cloud: Redis Cloud or AWS ElastiCache

3. **Authentication**?
   - JWT tokens (existing Django auth)
   - Token refresh every 15 minutes

4. **Rate limiting**?
   - 10 workflow submissions/minute per user
   - 5 concurrent WebSocket connections per user

5. **Deployment**?
   - Docker Compose (backend + Redis + agents)
   - Textual CLI runs locally, connects to remote backend

---

## Contact

- **Architecture questions:** See ARCHITECTURE.md
- **API documentation:** See docs/api/README.md
- **Implementation details:** See backend_bridge/ source code
