"""
AI Developer Agent with Memory and Terminal Access
===================================================

An AI agent that can:
1. Generate trading strategies using Gemini
2. Run strategies in .venv terminal
3. Parse test results and errors
4. Iteratively fix code based on errors
5. Maintain conversation memory across sessions

Features:
- LangChain conversation memory
- Terminal command execution
- Error analysis and code fixing
- Reference card system for available commands
- Iterative test-fix-retest loops

Version: 1.0.0
"""

import os
import sys
import json
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import logging

# LangChain imports - Updated for LangChain 1.0+
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI

# Add parent directory
sys.path.append(str(Path(__file__).parent.parent))

from Backtest.terminal_executor import TerminalExecutor, ExecutionResult, ExecutionStatus
from Backtest.gemini_strategy_generator import GeminiStrategyGenerator
from Backtest.workflow_tracker import WorkflowTracker, create_strategy_generation_workflow, StepStatus
from dotenv import load_dotenv

logger = logging.getLogger(__name__)


class AIDeveloperAgent:
    """
    AI Developer Agent with terminal access and memory
    """
    
    def __init__(
        self,
        memory_type: str = "buffer",  # "buffer" or "summary"
        max_iterations: int = 5,
        model_name: str = "gemini-2.0-flash"
    ):
        """
        Initialize AI Developer Agent
        
        Args:
            memory_type: Type of memory ("buffer" or "summary")
            max_iterations: Max iterations for test-fix loops
            model_name: Gemini model name to use
        """
        load_dotenv()
        
        # Initialize components using RequestRouter
        try:
            from . import request_router
            
            # Get models from RequestRouter
            generative_model = request_router.get_generative_model(model_name=model_name)
            chat_model = request_router.get_chat_model(model_name=model_name, temperature=0.7)
            
            # Initialize strategy generator with the model
            self.strategy_generator = GeminiStrategyGenerator(model=generative_model, model_name=model_name)
            
            # Initialize LangChain LLM
            self.llm = chat_model
            
            logger.info(f"AIDeveloperAgent initialized with RequestRouter (model: {model_name})")
            
        except Exception as e:
            raise ValueError(f"Failed to initialize AIDeveloperAgent with RequestRouter: {e}")
        
        # Initialize components
        self.terminal = TerminalExecutor()
        
        # Initialize chat history (simplified for LangChain 1.0+)
        self.chat_history = ChatMessageHistory()
        self.memory_type = memory_type
        self.max_iterations = max_iterations
        self.session_history = []
        
        # Load reference cards
        self.reference_cards = self._load_reference_cards()
        
        logger.info("AIDeveloperAgent initialized")
    
    def _load_reference_cards(self) -> Dict[str, Any]:
        """Load reference cards for available commands and scripts"""
        codes_dir = Path(__file__).parent / "codes"
        
        reference = {
            "available_scripts": [],
            "commands": {
                "run_strategy": "python codes/<strategy_name>.py",
                "run_backtest": "python strategy_manager.py --run <name>",
                "run_all": "python strategy_manager.py --run-all",
                "generate_strategy": "python gemini_strategy_generator.py '<description>' -o <output>.py",
                "list_strategies": "python strategy_manager.py --status"
            },
            "common_imports": {
                "backtesting.py": [
                    "from backtesting import Backtest, Strategy",
                    "from backtesting.lib import crossover",
                    "from backtesting.test import SMA"
                ],
                "data": [
                    "from Data.data_fetcher import fetch_historical_data"
                ],
                "indicators": [
                    "import pandas_ta as ta",
                    "import pandas as pd",
                    "import numpy as np"
                ]
            }
        }
        
        # Scan for available scripts
        if codes_dir.exists():
            for py_file in codes_dir.glob("*.py"):
                if py_file.name.startswith("__"):
                    continue
                reference["available_scripts"].append({
                    "name": py_file.stem,
                    "path": str(py_file),
                    "command": f"python {py_file.relative_to(self.terminal.project_root)}"
                })
        
        return reference
    
    def chat(self, user_message: str, context: Optional[Dict[str, Any]] = None) -> str:
        """
        Chat with the AI developer
        
        Args:
            user_message: User's message/request
            context: Optional context (execution results, errors, etc.)
        
        Returns:
            AI response
        """
        # Build context string
        context_str = ""
        if context:
            context_str = f"\n\nContext:\n{json.dumps(context, indent=2)}"
        
        # Add reference cards to system message
        system_prompt = f"""You are an expert AI developer agent specialized in creating and testing trading strategies.

You have access to:
1. Terminal executor to run Python scripts in .venv
2. Strategy generator using Gemini AI
3. Error analysis and code fixing capabilities
4. Conversation memory to track progress

Available commands:
{json.dumps(self.reference_cards['commands'], indent=2)}

Available scripts in codes folder:
{json.dumps([s['name'] for s in self.reference_cards['available_scripts']], indent=2)}

Common imports:
{json.dumps(self.reference_cards['common_imports'], indent=2)}

When a user asks you to test code:
1. Run the script using terminal executor
2. Analyze the results
3. If errors occur, suggest specific fixes
4. If requested, apply fixes and retest
5. Iterate until code works or max iterations reached

Always provide specific, actionable responses with code examples when relevant.
"""
        
        # Get chat history
        chat_history = self.chat_history.messages
        
        # Build messages
        messages = [SystemMessage(content=system_prompt)]
        messages.extend(chat_history)
        messages.append(HumanMessage(content=user_message + context_str))
        
        # Get response
        response = self.llm.invoke(messages)
        
        # Save to history
        self.chat_history.add_user_message(user_message)
        self.chat_history.add_ai_message(response.content)
        
        # Log session
        self.session_history.append({
            "timestamp": datetime.now().isoformat(),
            "user": user_message,
            "ai": response.content,
            "context": context
        })
        
        return response.content
    
    def generate_and_test_strategy(
        self,
        description: str,
        strategy_name: Optional[str] = None,
        auto_fix: bool = True,
        progress_callback: Optional[callable] = None
    ) -> Dict[str, Any]:
        """
        Generate a strategy and iteratively test and fix it
        
        Args:
            description: Natural language strategy description
            strategy_name: Optional strategy name
            auto_fix: Whether to automatically fix errors
            progress_callback: Callback for progress updates (receives workflow state dict)
        
        Returns:
            Dictionary with final status, code, results, and workflow state
        """
        logger.info(f"Generate and test: {description}")
        
        # Create workflow tracker
        tracker = create_strategy_generation_workflow(on_update=progress_callback)
        
        # Step 1: Parse request
        tracker.start_step("parse_request")
        tracker.update_step_progress("parse_request", 30, "Reading strategy description")
        
        if not strategy_name:
            strategy_name = f"ai_strategy_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        tracker.update_step_progress("parse_request", 70, "Validating completeness")
        tracker.complete_step("parse_request")
        
        # Step 2: Generate strategy
        tracker.start_step("generate_code")
        print("\n" + "="*80)
        print("STEP 1: Generating Strategy Code")
        print("="*80)
        
        try:
            tracker.update_step_progress("generate_code", 20, "Setting up imports and structure")
            tracker.update_step_progress("generate_code", 50, "Implementing indicators")
            code = self.strategy_generator.generate_strategy(description, strategy_name)
            tracker.update_step_progress("generate_code", 90, "Adding documentation")
            tracker.complete_step("generate_code")
        except Exception as e:
            tracker.fail_step("generate_code", str(e))
            return {
                "success": False,
                "stage": "generation",
                "error": str(e),
                "workflow": tracker.to_dict(),
                "code": None,
                "results": None
            }
        
        # Step 3: Save strategy file
        tracker.start_step("save_file")
        tracker.update_step_progress("save_file", 30, "Creating file name")
        
        output_file = self.terminal.project_root / "Backtest" / "codes" / f"{strategy_name}.py"
        
        tracker.update_step_progress("save_file", 70, "Writing code to file")
        output_file.write_text(code, encoding='utf-8')
        
        tracker.complete_step("save_file")
        print(f"✓ Strategy generated: {output_file}")
        
        # Step 4: Run initial test
        tracker.start_step("initial_test")
        iteration = 0
        last_result = None
        
        while iteration < self.max_iterations:
            iteration += 1
            
            step_id = "initial_test" if iteration == 1 else "retest"
            
            if iteration == 1:
                print("\n" + "="*80)
                print(f"STEP 2: Testing Strategy (Iteration {iteration}/{self.max_iterations})")
                print("="*80)
                tracker.update_step_progress("initial_test", 20, "Loading Python environment")
            else:
                if tracker.get_step("retest").status != StepStatus.IN_PROGRESS:
                    tracker.start_step("retest")
                print(f"\n" + "="*80)
                print(f"STEP 2.{iteration}: Retesting Strategy (Iteration {iteration}/{self.max_iterations})")
                print("="*80)
                tracker.update_step_progress("retest", 20, "Re-executing strategy")
            
            # Run script
            tracker.update_step_progress(step_id, 50, "Executing strategy code")
            result = self.terminal.run_script(output_file)
            last_result = result
            
            tracker.update_step_progress(step_id, 80, "Parsing results")
            
            # Check result
            if result.status == ExecutionStatus.SUCCESS:
                tracker.complete_step(step_id)
                
                # Skip error analysis and fixes if successful
                if iteration == 1:
                    tracker.skip_step("error_analysis", "No errors found")
                    tracker.skip_step("apply_fixes", "No fixes needed")
                
                # Step 8: Final validation
                tracker.start_step("final_validation")
                tracker.update_step_progress("final_validation", 50, "Extracting performance metrics")
                
                print(f"✅ Strategy executed successfully!")
                print(f"\nMetrics:")
                for key, value in result.summary.items():
                    if key not in ['exit_code', 'success', 'error_count', 'warning_count']:
                        print(f"  {key}: {value}")
                
                tracker.update_step_progress("final_validation", 90, "Generating summary report")
                tracker.complete_step("final_validation")
                tracker.complete_workflow()
                
                return {
                    "success": True,
                    "stage": "execution",
                    "iterations": iteration,
                    "code": code,
                    "results": result.summary,
                    "output": result.stdout,
                    "workflow": tracker.to_dict()
                }
            
            # Error occurred
            tracker.fail_step(step_id, f"{len(result.errors)} errors found")
            
            print(f"❌ Execution failed")
            print(f"\nErrors ({len(result.errors)}):")
            for err in result.errors:
                print(f"  - {err['type']}: {err['message']}")
                if err.get('file'):
                    print(f"    File: {err['file']}, Line: {err['line']}")
            
            if not auto_fix or iteration >= self.max_iterations:
                break
            
            # Step 5: Error analysis
            if iteration == 1:
                tracker.start_step("error_analysis")
            tracker.update_step_progress("error_analysis", 30, "Parsing error messages")
            
            print(f"\n" + "="*80)
            print(f"STEP 3.{iteration}: Analyzing and Fixing Errors")
            print("="*80)
            
            tracker.update_step_progress("error_analysis", 70, "Determining fix strategy")
            tracker.complete_step("error_analysis")
            
            # Step 6: Apply fixes
            if iteration == 1:
                tracker.start_step("apply_fixes")
            
            tracker.update_step_progress("apply_fixes", 20, "Generating fix patches")
            
            # Ask AI to fix
            fix_request = self._create_fix_request(code, result)
            fixed_code = self._fix_code_with_ai(fix_request)
            
            if fixed_code and fixed_code != code:
                tracker.update_step_progress("apply_fixes", 70, "Applying code changes")
                
                # Save fixed code
                output_file.write_text(fixed_code, encoding='utf-8')
                code = fixed_code
                
                tracker.update_step_progress("apply_fixes", 90, "Saving updated code")
                tracker.complete_step("apply_fixes")
                
                print("✓ Code updated with fixes")
            else:
                tracker.fail_step("apply_fixes", "Could not generate fix")
                print("✗ Could not generate fix")
                break
        
        # Failed after max iterations
        tracker.complete_workflow()
        
        return {
            "success": False,
            "stage": "execution",
            "iterations": iteration,
            "code": code,
            "results": last_result.summary if last_result else None,
            "errors": last_result.errors if last_result else None,
            "last_output": last_result.stderr if last_result else None,
            "workflow": tracker.to_dict()
        }
    
    def _create_fix_request(self, code: str, result: ExecutionResult) -> str:
        """Create a fix request for the AI"""
        error_details = "\n".join([
            f"{i+1}. {err['type']}: {err['message']}" + 
            (f"\n   File: {err['file']}, Line: {err['line']}" if err.get('file') else "")
            for i, err in enumerate(result.errors)
        ])
        
        return f"""The following Python strategy code has errors:

```python
{code}
```

Errors encountered:
{error_details}

Stderr output:
```
{result.stderr[:1000]}
```

Please provide the complete fixed code that resolves these errors. Return ONLY the Python code, no explanations.
Make sure to:
1. Fix all import errors
2. Fix all syntax errors
3. Fix all runtime errors
4. Ensure all required functions exist
5. Use proper backtesting.py patterns

Return the complete working code:
"""
    
    def _fix_code_with_ai(self, fix_request: str) -> Optional[str]:
        """Use AI to fix the code"""
        try:
            messages = [
                SystemMessage(content="You are an expert Python developer. Fix code errors and return complete working code."),
                HumanMessage(content=fix_request)
            ]
            
            response = self.llm.invoke(messages)
            
            # Extract code from response
            fixed_code = self._extract_code(response.content)
            return fixed_code
        
        except Exception as e:
            logger.error(f"Failed to fix code: {e}")
            return None
    
    def _extract_code(self, response: str) -> str:
        """Extract Python code from AI response"""
        # Remove markdown code blocks
        if "```python" in response:
            parts = response.split("```python")
            if len(parts) > 1:
                code = parts[1].split("```")[0]
                return code.strip()
        
        if "```" in response:
            parts = response.split("```")
            if len(parts) >= 3:
                return parts[1].strip()
        
        # Return as-is if no code blocks
        return response.strip()
    
    def test_existing_strategy(self, script_path: Path) -> ExecutionResult:
        """
        Test an existing strategy file
        
        Args:
            script_path: Path to Python strategy file
        
        Returns:
            ExecutionResult
        """
        return self.terminal.run_script(script_path)
    
    def save_session(self, output_path: Optional[Path] = None):
        """
        Save session history to JSON
        
        Args:
            output_path: Optional path (defaults to session_<timestamp>.json)
        """
        if not output_path:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = self.terminal.project_root / "Backtest" / "logs" / f"session_{timestamp}.json"
        
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(self.session_history, f, indent=2)
        
        logger.info(f"Session saved to {output_path}")
    
    def get_reference_cards(self) -> str:
        """Get formatted reference cards"""
        return json.dumps(self.reference_cards, indent=2)


def interactive_mode():
    """Run AI Developer Agent in interactive mode"""
    print("="*80)
    print("AI Developer Agent - Interactive Mode")
    print("="*80)
    print("\nCommands:")
    print("  generate <description> - Generate and test a strategy")
    print("  test <file> - Test an existing strategy")
    print("  chat <message> - Chat with AI developer")
    print("  reference - Show reference cards")
    print("  save - Save session")
    print("  exit - Exit")
    print()
    
    agent = AIDeveloperAgent()
    
    while True:
        try:
            user_input = input("\n> ").strip()
            
            if not user_input:
                continue
            
            if user_input.lower() == "exit":
                print("Saving session...")
                agent.save_session()
                print("Goodbye!")
                break
            
            if user_input.lower() == "reference":
                print("\n" + agent.get_reference_cards())
                continue
            
            if user_input.lower() == "save":
                agent.save_session()
                print("✓ Session saved")
                continue
            
            if user_input.lower().startswith("generate "):
                description = user_input[9:].strip()
                result = agent.generate_and_test_strategy(description, auto_fix=True)
                
                if result['success']:
                    print(f"\n✅ Strategy successfully created and tested!")
                    print(f"Iterations: {result['iterations']}")
                    print(f"\nResults: {json.dumps(result['results'], indent=2)}")
                else:
                    print(f"\n❌ Failed at stage: {result['stage']}")
                    if result.get('errors'):
                        print(f"Errors: {json.dumps(result['errors'], indent=2)}")
                continue
            
            if user_input.lower().startswith("test "):
                filepath = user_input[5:].strip()
                script_path = Path(filepath)
                
                if not script_path.is_absolute():
                    script_path = agent.terminal.project_root / "Backtest" / "codes" / filepath
                
                if not script_path.exists():
                    print(f"File not found: {script_path}")
                    continue
                
                print(f"Testing {script_path.name}...")
                result = agent.test_existing_strategy(script_path)
                
                print(f"\nStatus: {result.status.value}")
                print(f"Exit Code: {result.exit_code}")
                
                if result.errors:
                    print(f"\nErrors:")
                    for err in result.errors:
                        print(f"  - {err['type']}: {err['message']}")
                
                if result.status == ExecutionStatus.SUCCESS:
                    print(f"\nMetrics:")
                    for key, value in result.summary.items():
                        print(f"  {key}: {value}")
                
                continue
            
            if user_input.lower().startswith("chat "):
                message = user_input[5:].strip()
                response = agent.chat(message)
                print(f"\nAI: {response}")
                continue
            
            # Default: treat as chat
            response = agent.chat(user_input)
            print(f"\nAI: {response}")
        
        except KeyboardInterrupt:
            print("\n\nInterrupted. Saving session...")
            agent.save_session()
            break
        except Exception as e:
            print(f"\nError: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    import argparse
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    parser = argparse.ArgumentParser(description='AI Developer Agent with Terminal Access')
    parser.add_argument('-i', '--interactive', action='store_true', help='Run in interactive mode')
    parser.add_argument('-g', '--generate', type=str, help='Generate and test strategy from description')
    parser.add_argument('-t', '--test', type=str, help='Test existing strategy file')
    parser.add_argument('--no-fix', action='store_true', help='Disable automatic fixing')
    
    args = parser.parse_args()
    
    if args.interactive:
        interactive_mode()
    elif args.generate:
        agent = AIDeveloperAgent()
        result = agent.generate_and_test_strategy(args.generate, auto_fix=not args.no_fix)
        
        if result['success']:
            print(f"\n✅ Strategy successfully created!")
            print(f"Iterations: {result['iterations']}")
        else:
            print(f"\n❌ Failed: {result.get('error', 'Unknown error')}")
            sys.exit(1)
    elif args.test:
        agent = AIDeveloperAgent()
        script_path = Path(args.test)
        
        if not script_path.is_absolute():
            script_path = agent.terminal.project_root / "Backtest" / "codes" / args.test
        
        result = agent.test_existing_strategy(script_path)
        
        print(f"Status: {result.status.value}")
        if result.status != ExecutionStatus.SUCCESS:
            sys.exit(1)
    else:
        parser.print_help()
