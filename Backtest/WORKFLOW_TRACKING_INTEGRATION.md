# Workflow Tracking Integration Guide

This guide shows how to integrate the workflow tracking system with your Django backend API.

## Backend Integration

### 1. Using the Workflow Tracker in API Views

```python
# In your Django view (e.g., strategy_api/views.py)
from django.http import JsonResponse
from Backtest.ai_developer_agent import AIDeveloperAgent
from Backtest.workflow_tracker import WorkflowTracker, create_strategy_generation_workflow
import json

def create_strategy_with_ai_and_progress(request):
    """
    API endpoint that generates a strategy with progress tracking
    """
    if request.method == 'POST':
        data = json.loads(request.body)
        description = data.get('strategy_text', '')
        strategy_name = data.get('name', 'strategy')
        
        # Initialize workflow tracker
        workflow_data = {}
        
        def progress_callback(workflow: WorkflowTracker):
            """
            Callback to capture workflow state updates
            """
            nonlocal workflow_data
            workflow_data = workflow.to_dict()
            # Optional: Send real-time updates via WebSocket/SSE here
            print(f"Progress: {workflow.get_progress_summary()['overall_percentage']}%")
        
        # Initialize AI developer agent
        agent = AIDeveloperAgent(
            api_key="your-gemini-api-key",
            memory_type="buffer"
        )
        
        # Generate strategy with progress tracking
        result = agent.generate_and_test_strategy(
            description=description,
            strategy_name=strategy_name,
            auto_fix=True,
            progress_callback=progress_callback  # Pass the callback
        )
        
        # Include workflow state in response
        response_data = {
            'success': result['success'],
            'message': result.get('message', ''),
            'strategy': result.get('strategy_data', {}),
            'workflow': result.get('workflow', workflow_data),  # Include workflow state
            'ai_validation': {
                'confidence': 'high' if result['success'] else 'low',
                'warnings': result.get('errors', []),
            }
        }
        
        return JsonResponse(response_data)
```

### 2. Real-Time Progress Updates (Optional)

For real-time progress updates, you can use Django Channels with WebSockets:

```python
# consumers.py
from channels.generic.websocket import WebsocketConsumer
import json

class StrategyProgressConsumer(WebsocketConsumer):
    def connect(self):
        self.accept()
    
    def disconnect(self, close_code):
        pass
    
    def receive(self, text_data):
        data = json.loads(text_data)
        
        if data.get('action') == 'generate_strategy':
            description = data.get('description', '')
            
            def progress_callback(workflow):
                # Send progress update to frontend
                self.send(text_data=json.dumps({
                    'type': 'progress_update',
                    'workflow': workflow.to_dict()
                }))
            
            # Run strategy generation
            agent = AIDeveloperAgent(api_key="your-key")
            result = agent.generate_and_test_strategy(
                description=description,
                progress_callback=progress_callback
            )
            
            # Send final result
            self.send(text_data=json.dumps({
                'type': 'completion',
                'result': result
            }))
```

### 3. Polling-Based Progress (Simpler Alternative)

If you don't want to use WebSockets, you can use polling:

```python
# Store workflow states in cache or database
from django.core.cache import cache

def start_strategy_generation(request):
    """Start strategy generation and return task ID"""
    task_id = str(uuid.uuid4())
    
    def progress_callback(workflow):
        # Store workflow state in cache
        cache.set(f'workflow_{task_id}', workflow.to_dict(), timeout=3600)
    
    # Run generation in background (using Celery or threading)
    threading.Thread(
        target=generate_strategy_task,
        args=(task_id, description, progress_callback)
    ).start()
    
    return JsonResponse({'task_id': task_id})

def check_strategy_progress(request, task_id):
    """Check progress of ongoing strategy generation"""
    workflow_data = cache.get(f'workflow_{task_id}')
    
    if workflow_data:
        return JsonResponse({
            'workflow': workflow_data,
            'is_complete': workflow_data['progress_summary']['is_complete']
        })
    else:
        return JsonResponse({'error': 'Task not found'}, status=404)
```

## Frontend Integration

The frontend is already set up to display workflow progress. Here's what happens:

### 1. API Response Structure

Your backend should return:

```json
{
  "success": true,
  "strategy": { ... },
  "workflow": {
    "workflow_name": "Strategy Generation",
    "started_at": "2024-01-20T10:30:00",
    "completed_at": "2024-01-20T10:32:15",
    "steps": [
      {
        "id": "parse_request",
        "title": "Understanding Request",
        "description": "Analyzing your strategy requirements",
        "status": "completed",
        "progress_percentage": 100,
        "started_at": "2024-01-20T10:30:00",
        "completed_at": "2024-01-20T10:30:10",
        "substeps": ["Extracting key parameters", "Validating requirements"],
        "current_substep": null,
        "error_message": null
      },
      {
        "id": "generate_code",
        "title": "Generating Code",
        "description": "Creating Python strategy code",
        "status": "completed",
        "progress_percentage": 100,
        "substeps": ["Building imports", "Creating Strategy class", "Adding init method", "Implementing next method"],
        "current_substep": null
      },
      ...
    ],
    "current_step_index": 7,
    "progress_summary": {
      "workflow_name": "Strategy Generation",
      "total_steps": 8,
      "completed_steps": 8,
      "failed_steps": 0,
      "in_progress_steps": 0,
      "overall_percentage": 100,
      "is_complete": true,
      "duration_seconds": 135
    }
  }
}
```

### 2. Frontend Display

The `Dashboard.tsx` component automatically displays workflow progress:

- **During generation**: Shows active workflow at the top with loading animation
- **After completion**: Shows final workflow state in the message
- **Progress indicators**: Step-by-step progress with percentages
- **Status icons**: ✓ completed, ⏳ pending, 🔄 in progress, ❌ failed

### 3. Workflow States

The frontend handles all workflow states:

- `pending`: Gray with hollow circle icon
- `in_progress`: Blue with spinning loader, shows progress bar
- `completed`: Green with checkmark
- `failed`: Red with alert icon, shows error message
- `skipped`: Gray with skip icon

## Testing the Integration

### 1. Test with Python Directly

```python
from Backtest.ai_developer_agent import AIDeveloperAgent

# Test workflow tracking
agent = AIDeveloperAgent(api_key="your-key")

def print_progress(workflow):
    summary = workflow.get_progress_summary()
    print(f"Progress: {summary['overall_percentage']}%")
    
    current_step = workflow.steps[workflow.current_step_index]
    print(f"Current: {current_step.title} ({current_step.progress_percentage}%)")

result = agent.generate_and_test_strategy(
    description="Create a moving average crossover strategy",
    strategy_name="ma_cross",
    progress_callback=print_progress
)

# Check workflow in result
print(json.dumps(result['workflow'], indent=2))
```

### 2. Test API Endpoint

```bash
# Start strategy generation
curl -X POST http://localhost:8000/api/strategies/api/create_strategy_with_ai/ \
  -H "Content-Type: application/json" \
  -d '{
    "strategy_text": "Moving average crossover strategy",
    "name": "MA Cross",
    "use_gemini": true
  }'

# Response includes workflow state
{
  "workflow": {
    "workflow_name": "Strategy Generation",
    "progress_summary": {
      "overall_percentage": 100,
      "is_complete": true
    }
  }
}
```

### 3. Frontend Testing

1. Open Dashboard in browser
2. Start typing a strategy description
3. Click Send
4. Watch workflow progress display at top of chat
5. See step-by-step progress with percentages
6. View final workflow summary in completed message

## Customization

### Add Custom Workflow Steps

```python
from Backtest.workflow_tracker import WorkflowTracker

# Create custom workflow
tracker = WorkflowTracker("Custom Workflow")
tracker.add_step("validate_input", "Validating Input", "Checking parameters")
tracker.add_step("fetch_data", "Fetching Data", "Getting market data")
tracker.add_step("run_backtest", "Running Backtest", "Testing strategy")
tracker.add_step("generate_report", "Creating Report", "Generating results")

# Use in your code
tracker.start_step("validate_input")
# ... do work ...
tracker.update_step_progress("validate_input", 50, "Checking indicators")
# ... more work ...
tracker.complete_step("validate_input")

# Get state for API response
workflow_data = tracker.to_dict()
```

### Customize Frontend Display

Edit `WorkflowProgress.tsx`:

```tsx
// Change colors
const getStepColor = (status: string) => {
  switch (status) {
    case "completed":
      return "border-green-500 bg-green-50"; // Your custom green
    // ...
  }
};

// Change icons
const getStepIcon = (status: string) => {
  // Use your own icons
};
```

## Troubleshooting

### Workflow Not Displaying

1. Check API response includes `workflow` field
2. Verify workflow structure matches expected format
3. Check browser console for errors
4. Ensure WorkflowProgress component is imported

### Progress Not Updating

1. Verify progress_callback is being called
2. Check workflow state is being updated in backend
3. For real-time updates, ensure WebSocket/polling is working
4. Check cache/database for stored workflow states

### Performance Issues

1. Limit substep updates (don't update on every line)
2. Use throttling for progress updates (max 1 per second)
3. Consider background tasks for long operations
4. Cache workflow states appropriately

## Best Practices

1. **Always include workflow in API responses** - Frontend expects it
2. **Use meaningful step names** - Users see these
3. **Update progress regularly** - But not too frequently (throttle)
4. **Handle errors gracefully** - Mark steps as failed with error messages
5. **Skip unnecessary steps** - Use skip_step() for conditional logic
6. **Test with slow operations** - Ensure progress updates work
7. **Log workflow state** - Helpful for debugging
8. **Consider background tasks** - Don't block API responses

## Next Steps

1. ✅ Backend integration complete
2. ✅ Frontend displaying workflow
3. 🔄 Add real-time updates (WebSocket/SSE) - Optional
4. 🔄 Test with actual strategy generation
5. 🔄 Add error handling and retries
6. 🔄 Monitor performance and optimize
