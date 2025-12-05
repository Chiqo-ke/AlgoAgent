# Strategy Edit Integration Plan - Continuous Flow

## Problem Identified

The user's chat shows a **context continuity issue**:

```
User: "Make a simple ema crossover strategy..."
Agent: "✅ Validates strategy, provides recommendations"

User: "Set a stop loss 10 pips below entry..."
Agent: "⚠️ Treats this as NEW strategy request, not an EDIT"
Agent: "Missing strategy context..."
```

**Root Cause:**
- The `/api/strategies/chat/chat/` endpoint uses `GeminiStrategyIntegrator.chat()`
- This method is a **generic conversational interface** - it doesn't understand edit intent
- It doesn't retrieve or modify canonical strategy schemas
- Each message is treated as standalone, not as a modification request

---

## Current Architecture

### What Exists

**1. Conversation Memory** (`Strategy/conversation_manager.py`)
- ✅ Stores all chat messages with context
- ✅ Links chat sessions to strategies
- ✅ Retrieves conversation history

**2. Generic Chat** (`Strategy/gemini_strategy_integrator.py`)
```python
def chat(self, user_message: str, include_strategy_context: bool = True) -> str:
    # Generic conversational response
    # Does NOT parse edit intent
    # Does NOT modify schemas
    # Just returns AI response text
```

**3. Strategy Validation** (Separate workflow)
- ✅ Can parse canonical schemas
- ✅ Can create/update strategies
- ⚠️ Requires explicit API calls to `/validate_strategy_with_ai/` or `/create_strategy_with_ai/`

**4. Canonical Schema System**
- ✅ Well-defined JSON structure for strategies
- ✅ Validation and parsing logic exists
- ⚠️ Not integrated with chat flow

---

## Solution: Intelligent Edit Detection

### Architecture Changes

```
┌─────────────────────────────────────────────────────┐
│            User Chat Message                        │
└──────────────────┬──────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────┐
│   NEW: Intent Classifier                            │
│   • Detect: CREATE, EDIT, QUESTION, CLARIFY         │
│   • Extract: Parameters being modified              │
└──────────────────┬──────────────────────────────────┘
                   │
         ┌─────────┴──────────┐
         │                    │
         ▼                    ▼
    ┌────────┐          ┌────────────┐
    │ EDIT   │          │ QUESTION   │
    │ Intent │          │ Intent     │
    └────┬───┘          └─────┬──────┘
         │                    │
         ▼                    ▼
┌─────────────────┐    ┌──────────────┐
│ Schema Modifier │    │ Generic Chat │
│ • Get current   │    │ • Just reply │
│   schema        │    │              │
│ • Apply edits   │    └──────────────┘
│ • Validate      │
│ • Save          │
└─────────────────┘
```

### New Components Needed

#### 1. **Intent Classifier** (`Strategy/chat_intent_classifier.py`)

```python
class ChatIntentClassifier:
    """Detects user intent from chat messages"""
    
    def classify(self, message: str, conversation_history: List) -> Dict:
        """
        Returns:
        {
            'intent': 'CREATE' | 'EDIT' | 'QUESTION' | 'CLARIFY',
            'confidence': float,
            'entities': {
                'strategy_id': int,  # if editing existing
                'parameters': {
                    'stop_loss': '10 pips',
                    'take_profit': '50 pips',
                    ...
                }
            }
        }
        """
```

**Detection Patterns:**
- **EDIT intent keywords:**
  - "Set a stop loss..."
  - "Change the EMA period..."
  - "Update the strategy..."
  - "Modify the indicator..."
  - "Add a condition..."

- **CREATE intent keywords:**
  - "Create a strategy..."
  - "Make a new strategy..."
  - "Build a bot..."

- **QUESTION intent:**
  - "How does X work?"
  - "What is Y?"
  - "Why did you..."

#### 2. **Schema Modifier** (`Strategy/schema_modifier.py`)

```python
class StrategySchemaModifier:
    """Applies edits to canonical strategy schemas"""
    
    def modify_schema(self, schema: Dict, edits: Dict, user_message: str) -> Dict:
        """
        Takes current schema + user's edit message
        Returns updated schema
        
        Examples:
        - "Set stop loss 10 pips" → Updates risk_management.stop_loss
        - "Change EMA to 50" → Updates indicators[ema].period
        - "Add RSI < 30 condition" → Adds to entry_conditions
        """
```

#### 3. **Enhanced Chat Handler** (Modify `StrategyChatViewSet.chat()`)

```python
@action(detail=False, methods=['post'])
def chat(self, request):
    """Enhanced with edit detection"""
    
    # 1. Classify intent
    intent_data = classifier.classify(user_message, conversation_history)
    
    if intent_data['intent'] == 'EDIT':
        # 2. Get current strategy schema from context
        strategy = conv_manager.get_session().strategy
        current_schema = strategy.canonical_schema  # Assuming this exists
        
        # 3. Apply modifications
        updated_schema = modifier.modify_schema(
            schema=current_schema,
            edits=intent_data['entities']['parameters'],
            user_message=user_message
        )
        
        # 4. Validate updated schema
        validator = StrategyValidatorBot(...)
        result = validator.validate_schema(updated_schema)
        
        # 5. Update strategy
        strategy.canonical_schema = updated_schema
        strategy.save()
        
        # 6. Return confirmation
        return Response({
            'intent': 'EDIT',
            'updated_schema': updated_schema,
            'validation': result,
            'message': 'Strategy updated successfully!'
        })
    
    else:
        # Generic chat for questions
        return ai.chat(user_message)
```

---

## Implementation Steps

### Phase 1: Schema Retrieval Integration

**Goal:** Ensure strategies store and retrieve canonical schemas

**Files to modify:**
- `strategy_api/models.py` - Add `canonical_schema` JSONField to `Strategy` model
- `strategy_api/serializers.py` - Include schema in serializers
- `strategy_api/views.py` - Save schema when creating/updating strategies

**Migration:**
```python
# Add field
canonical_schema = models.JSONField(
    default=dict,
    help_text="Canonical strategy schema in ChronicQL format"
)
```

### Phase 2: Intent Classification

**New file:** `Strategy/chat_intent_classifier.py`

```python
class ChatIntentClassifier:
    def __init__(self, use_gemini=True):
        self.use_gemini = use_gemini
        if use_gemini:
            self.model = genai.GenerativeModel('gemini-2.0-flash-exp')
    
    def classify(self, message: str, history: List[Dict]) -> Dict:
        """
        Use Gemini to classify intent and extract entities
        """
        prompt = f"""
Analyze this trading strategy chat message and classify the user's intent.

CONVERSATION HISTORY:
{self._format_history(history)}

LATEST USER MESSAGE:
{message}

Classify as one of:
1. CREATE - User wants to create a NEW strategy
2. EDIT - User wants to MODIFY an existing strategy
3. QUESTION - User is asking about strategies or trading
4. CLARIFY - User is providing clarification to a question

If EDIT, extract which parameters are being modified.

Return JSON:
{{
    "intent": "CREATE" | "EDIT" | "QUESTION" | "CLARIFY",
    "confidence": 0.0-1.0,
    "reasoning": "Why you classified this way",
    "entities": {{
        "parameters": {{}},  // e.g. {{"stop_loss": "10 pips", "take_profit": "50 pips"}}
        "indicators": {{}},  // e.g. {{"ema_short": 30, "ema_long": 60}}
        "conditions": []     // New entry/exit conditions
    }}
}}
"""
        
        response = self.model.generate_content(prompt)
        return json.loads(response.text)
```

### Phase 3: Schema Modification

**New file:** `Strategy/schema_modifier.py`

```python
class StrategySchemaModifier:
    """Applies user edits to canonical schemas"""
    
    def __init__(self, use_gemini=True):
        self.use_gemini = use_gemini
        if use_gemini:
            self.model = genai.GenerativeModel('gemini-2.0-flash-exp')
    
    def modify_schema(self, 
                     current_schema: Dict, 
                     user_message: str,
                     extracted_entities: Dict) -> Dict:
        """
        Takes current schema + user's edit message
        Returns updated schema
        
        Args:
            current_schema: The existing canonical schema
            user_message: What the user said
            extracted_entities: Parameters/indicators from intent classifier
            
        Returns:
            Updated canonical schema
        """
        
        prompt = f"""
You are a trading strategy schema editor.

CURRENT STRATEGY SCHEMA:
```json
{json.dumps(current_schema, indent=2)}
```

USER'S EDIT REQUEST:
{user_message}

EXTRACTED PARAMETERS:
{json.dumps(extracted_entities, indent=2)}

Apply the user's modifications to the schema. Return the COMPLETE updated schema.

Rules:
1. Preserve all existing fields that weren't mentioned
2. Update only the fields user wants to change
3. Maintain valid ChronicQL format
4. Add any new indicators/conditions mentioned

Return the complete updated schema as JSON.
```
        
        response = self.model.generate_content(prompt)
        updated_schema = json.loads(response.text)
        
        return updated_schema
```

### Phase 4: Enhanced Chat Endpoint

**Modify:** `strategy_api/views.py` - `StrategyChatViewSet.chat()`

```python
@action(detail=False, methods=['post'])
def chat(self, request):
    """Enhanced with intelligent edit detection"""
    
    serializer = ChatMessageRequestSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        data = serializer.validated_data
        user_message = data['message']
        session_id = data.get('session_id')
        strategy_id = data.get('strategy_id')
        use_context = data.get('use_context', True)
        
        # Get user and conversation manager
        user = request.user if request.user.is_authenticated else None
        conv_manager = ConversationManager(session_id=session_id, user=user)
        
        # Link to strategy if provided
        if strategy_id:
            conv_manager.link_strategy(strategy_id)
        
        # Get conversation history
        history = conv_manager.get_conversation_history()
        
        # ============================================
        # NEW: Classify intent
        # ============================================
        from Strategy.chat_intent_classifier import ChatIntentClassifier
        from Strategy.schema_modifier import StrategySchemaModifier
        
        classifier = ChatIntentClassifier(use_gemini=True)
        intent_data = classifier.classify(user_message, history)
        
        logger.info(f"Classified intent: {intent_data['intent']} (confidence: {intent_data['confidence']})")
        
        # ============================================
        # Handle EDIT intent
        # ============================================
        if intent_data['intent'] == 'EDIT' and intent_data['confidence'] > 0.7:
            session = conv_manager.get_session()
            
            # Get the strategy being edited
            if not session.strategy:
                # No strategy linked - ask user which one
                return Response({
                    'intent': 'CLARIFY_NEEDED',
                    'message': 'Which strategy would you like to edit? Please provide the strategy name or ID.',
                    'session_id': conv_manager.session_id
                })
            
            strategy = session.strategy
            
            # Get current schema
            current_schema = strategy.canonical_schema
            
            if not current_schema:
                return Response({
                    'error': 'Strategy does not have a canonical schema',
                    'message': 'This strategy was created without a schema. Please recreate it.',
                    'session_id': conv_manager.session_id
                })
            
            # Apply modifications
            modifier = StrategySchemaModifier(use_gemini=True)
            updated_schema = modifier.modify_schema(
                current_schema=current_schema,
                user_message=user_message,
                extracted_entities=intent_data['entities']
            )
            
            # Validate updated schema
            from Strategy.strategy_validator import StrategyValidatorBot
            validator = StrategyValidatorBot(
                username=user.username if user else 'anonymous',
                use_gemini=True,
                session_id=conv_manager.session_id,
                user=user
            )
            
            # Convert schema to text for validation
            schema_text = json.dumps(updated_schema, indent=2)
            validation_result = validator.process_input(schema_text, input_type='canonical_json')
            
            if validation_result['status'] == 'success':
                # Update strategy
                strategy.canonical_schema = updated_schema
                strategy.description = updated_schema.get('strategy_description', strategy.description)
                strategy.save()
                
                # Store in conversation
                conv_manager.add_ai_message(
                    f"✅ Strategy updated successfully! Modified: {', '.join(intent_data['entities'].get('parameters', {}).keys())}",
                    metadata={
                        'intent': 'EDIT',
                        'updated_fields': list(intent_data['entities'].get('parameters', {}).keys()),
                        'validation': validation_result
                    }
                )
                
                return Response({
                    'intent': 'EDIT',
                    'success': True,
                    'message': f"✅ Strategy '{strategy.name}' updated successfully!",
                    'updated_schema': updated_schema,
                    'validation': validation_result,
                    'session_id': conv_manager.session_id,
                    'modified_fields': list(intent_data['entities'].get('parameters', {}).keys())
                }, status=status.HTTP_200_OK)
            else:
                # Validation failed
                return Response({
                    'intent': 'EDIT',
                    'success': False,
                    'message': '⚠️ Schema validation failed. Please review the errors.',
                    'errors': validation_result.get('errors', []),
                    'warnings': validation_result.get('warnings', []),
                    'session_id': conv_manager.session_id
                }, status=status.HTTP_400_BAD_REQUEST)
        
        # ============================================
        # Handle CREATE intent
        # ============================================
        elif intent_data['intent'] == 'CREATE':
            # Redirect to create_strategy_with_ai endpoint logic
            # (could extract this to a separate method)
            from Strategy.strategy_validator import StrategyValidatorBot
            
            validator = StrategyValidatorBot(
                username=user.username if user else 'anonymous',
                use_gemini=True,
                session_id=conv_manager.session_id,
                user=user
            )
            
            result = validator.process_input(user_message, input_type='natural_language')
            
            if result['status'] == 'success':
                # Create strategy from result
                # ... (existing create_strategy_with_ai logic)
                pass
            
            return Response({
                'intent': 'CREATE',
                'validation': result,
                'session_id': conv_manager.session_id
            })
        
        # ============================================
        # Handle QUESTION/CLARIFY - Generic chat
        # ============================================
        else:
            ai = GeminiStrategyIntegrator(
                session_id=conv_manager.session_id,
                user=user
            )
            
            ai_response = ai.chat(user_message, include_strategy_context=use_context)
            
            return Response({
                'intent': intent_data['intent'],
                'message': ai_response,
                'session_id': conv_manager.session_id,
                'message_count': conv_manager.get_session().message_count
            }, status=status.HTTP_200_OK)
    
    except Exception as e:
        logger.error(f"Error in enhanced chat endpoint: {e}")
        logger.error(traceback.format_exc())
        return Response({
            'error': 'Internal server error',
            'details': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
```

---

## Benefits

### For Users
✅ **Natural conversational flow** - No need to restart strategy creation
✅ **Iterative refinement** - "Change this", "Add that", "Set this parameter"
✅ **Context preservation** - Agent remembers what's being discussed
✅ **Immediate feedback** - See validation results after each edit

### For Developers
✅ **Modular architecture** - Intent classifier + Schema modifier are reusable
✅ **Extensible** - Easy to add new intent types
✅ **Traceable** - All edits logged in conversation history
✅ **Testable** - Can unit test each component separately

---

## Testing Strategy

### Unit Tests

```python
# test_intent_classifier.py
def test_edit_detection():
    classifier = ChatIntentClassifier()
    
    result = classifier.classify(
        "Set stop loss to 10 pips",
        history=[]
    )
    
    assert result['intent'] == 'EDIT'
    assert 'stop_loss' in result['entities']['parameters']
    assert result['entities']['parameters']['stop_loss'] == '10 pips'

def test_create_detection():
    classifier = ChatIntentClassifier()
    
    result = classifier.classify(
        "Create an EMA crossover strategy",
        history=[]
    )
    
    assert result['intent'] == 'CREATE'
```

### Integration Tests

```python
# test_chat_edit_flow.py
def test_full_edit_flow(api_client, strategy):
    """Test complete edit flow from chat message to schema update"""
    
    # Create chat session linked to strategy
    session = create_chat_session(strategy_id=strategy.id)
    
    # Send edit message
    response = api_client.post('/api/strategies/chat/chat/', {
        'message': 'Set stop loss to 10 pips below entry',
        'session_id': session.session_id,
        'strategy_id': strategy.id
    })
    
    assert response.status_code == 200
    assert response.json()['intent'] == 'EDIT'
    assert response.json()['success'] == True
    
    # Verify strategy was updated
    strategy.refresh_from_db()
    assert strategy.canonical_schema['risk_management']['stop_loss']['value'] == 10
    assert strategy.canonical_schema['risk_management']['stop_loss']['unit'] == 'pips'
```

---

## Migration Path

### Step 1: Add canonical_schema field (Day 1)
```bash
python manage.py makemigrations
python manage.py migrate
```

### Step 2: Implement intent classifier (Day 2)
- Create `Strategy/chat_intent_classifier.py`
- Write unit tests
- Test with sample messages

### Step 3: Implement schema modifier (Day 3)
- Create `Strategy/schema_modifier.py`
- Write unit tests
- Test with sample schemas

### Step 4: Integrate into chat endpoint (Day 4)
- Modify `StrategyChatViewSet.chat()`
- Add error handling
- Test end-to-end flow

### Step 5: User acceptance testing (Day 5)
- Test with real users
- Collect feedback
- Iterate

---

## Success Metrics

- ✅ **Intent classification accuracy** > 90%
- ✅ **Schema modification success rate** > 95%
- ✅ **User satisfaction** - Conversational flow feels natural
- ✅ **Reduced API calls** - Users don't need multiple endpoints for edits
- ✅ **Faster iteration** - Time from idea to tested strategy < 2 minutes

---

## Future Enhancements

### Phase 2 Features
- **Undo/Redo** - "Undo last change"
- **Batch edits** - "Set stop loss to 10 pips AND take profit to 50 pips"
- **Conditional edits** - "Only for long trades, set stop loss to..."
- **Template application** - "Apply the risk management from my other strategy"

### Phase 3 Features
- **Visual diff** - Show before/after comparison of schema
- **Suggested edits** - AI proactively suggests improvements
- **A/B testing** - "Create a variant with different parameters"
- **Backtesting integration** - "Test this change against last year's data"

---

## Conclusion

This integration enables **true continuous flow** in strategy development:

**Before:**
```
User → Validate → Get errors → Go to different endpoint → Update → Validate again
```

**After:**
```
User: "Create EMA strategy"
Agent: "✅ Created!"

User: "Set stop loss 10 pips"
Agent: "✅ Updated! Stop loss now 10 pips."

User: "Add RSI < 30 condition"
Agent: "✅ Added entry condition: RSI < 30"
```

**One conversation, complete strategy development! 🚀**
