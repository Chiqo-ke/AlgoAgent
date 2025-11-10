"""
Strategy Validator CLI - Command-line interface for the StrategyValidatorBot
Provides interactive and batch modes for strategy validation.
"""

import argparse
import sys
import json
from typing import Optional
from pathlib import Path

from strategy_validator import StrategyValidatorBot, validate_strategy
from examples import get_all_examples, get_example
from system_prompt import get_system_prompt


class StrategyValidatorCLI:
    """Command-line interface for strategy validation."""
    
    def __init__(self, username: str = "cli_user", strict_mode: bool = False):
        """Initialize the CLI."""
        self.username = username
        self.strict_mode = strict_mode
        self.bot = StrategyValidatorBot(username=username, strict_mode=strict_mode)
    
    def interactive_mode(self):
        """Run in interactive mode."""
        print("=" * 70)
        print("Strategy Validator Bot - Interactive Mode")
        print("=" * 70)
        print("\nEnter your trading strategy (type 'help' for commands, 'exit' to quit)")
        print()
        
        while True:
            try:
                # Get input
                print("\n" + "-" * 70)
                user_input = input("Strategy> ").strip()
                
                if not user_input:
                    continue
                
                # Handle commands
                if user_input.lower() == 'exit':
                    print("Goodbye!")
                    break
                elif user_input.lower() == 'help':
                    self._print_help()
                    continue
                elif user_input.lower() == 'examples':
                    self._list_examples()
                    continue
                elif user_input.lower().startswith('example '):
                    example_id = int(user_input.split()[1])
                    self._run_example(example_id)
                    continue
                elif user_input.lower() == 'prompt':
                    self._show_system_prompt()
                    continue
                
                # Process strategy
                print("\nProcessing strategy...\n")
                result = self.bot.process_input(user_input)
                
                if result["status"] == "success":
                    print(self.bot.get_formatted_output())
                else:
                    print(f"\n❌ Error: {result.get('message', 'Unknown error')}")
                    if "issues" in result:
                        for issue in result["issues"]:
                            print(f"  - {issue}")
                
            except KeyboardInterrupt:
                print("\n\nInterrupted. Type 'exit' to quit.")
            except Exception as e:
                print(f"\n❌ Error: {str(e)}")
    
    def process_file(self, file_path: str, output_path: Optional[str] = None):
        """Process strategy from a file."""
        try:
            # Read input file
            with open(file_path, 'r') as f:
                strategy_text = f.read()
            
            print(f"Processing strategy from: {file_path}")
            
            # Process strategy
            result = validate_strategy(strategy_text, username=self.username)
            
            # Prepare output
            if result["status"] == "success":
                output_data = {
                    "input_file": file_path,
                    "status": "success",
                    "canonicalized_steps": result["canonicalized_steps"],
                    "classification": result["classification_detail"],
                    "recommendations": result["recommendations_list"],
                    "confidence": result["confidence"],
                    "canonical_json": json.loads(result["canonical_json"])
                }
            else:
                output_data = {
                    "input_file": file_path,
                    "status": "error",
                    "message": result.get("message"),
                    "issues": result.get("issues", [])
                }
            
            # Write output
            if output_path:
                with open(output_path, 'w') as f:
                    json.dump(output_data, f, indent=2)
                print(f"✓ Output written to: {output_path}")
            else:
                print(json.dumps(output_data, indent=2))
            
            return output_data
            
        except FileNotFoundError:
            print(f"❌ Error: File not found: {file_path}")
            return None
        except Exception as e:
            print(f"❌ Error processing file: {str(e)}")
            return None
    
    def process_text(self, strategy_text: str, format: str = "formatted"):
        """Process strategy from text."""
        result = validate_strategy(strategy_text, username=self.username)
        
        if format == "json":
            print(json.dumps(result, indent=2))
        elif format == "compact":
            if result["status"] == "success":
                print(result["canonical_json"])
            else:
                print(json.dumps(result))
        else:  # formatted
            if result["status"] == "success":
                bot = StrategyValidatorBot(username=self.username)
                bot.process_input(strategy_text)
                print(bot.get_formatted_output())
            else:
                print(f"Error: {result.get('message')}")
    
    def _print_help(self):
        """Print help information."""
        help_text = """
Commands:
  help         - Show this help message
  examples     - List all example strategies
  example N    - Run example strategy N
  prompt       - Show the system prompt
  exit         - Exit the program

To validate a strategy:
  Simply type or paste your strategy description and press Enter.

Supported input formats:
  - Free text: "Buy when EMA crosses. Set stop at 1%."
  - Numbered: "1. Buy at signal 2. Exit at target"
  - URL: "https://youtube.com/watch?v=abc123"
"""
        print(help_text)
    
    def _list_examples(self):
        """List all example strategies."""
        examples = get_all_examples()
        print("\nAvailable Examples:")
        print("=" * 70)
        for ex in examples:
            status = "✓" if ex["should_pass"] is True else "✗" if ex["should_pass"] is False else "🔗"
            print(f"{status} Example {ex['id']}: {ex['name']}")
            print(f"   Type: {ex['expected_type']}, Risk: {ex['expected_risk']}")
        print("\nUse 'example N' to run example N")
    
    def _run_example(self, example_id: int):
        """Run a specific example."""
        example = get_example(example_id)
        if not example:
            print(f"Example {example_id} not found")
            return
        
        print(f"\nRunning Example {example_id}: {example['name']}")
        print("=" * 70)
        print("\nInput:")
        print(example['input'])
        print("\n" + "=" * 70)
        print("Processing...\n")
        
        result = self.bot.process_input(example['input'])
        
        if result["status"] == "success":
            print(self.bot.get_formatted_output())
        else:
            print(f"Error: {result.get('message')}")
            if "issues" in result:
                for issue in result["issues"]:
                    print(f"  - {issue}")
    
    def _show_system_prompt(self):
        """Show the system prompt."""
        prompt = get_system_prompt()
        print("\nSystem Prompt:")
        print("=" * 70)
        print(prompt)


def main():
    """Main entry point for CLI."""
    parser = argparse.ArgumentParser(
        description="Strategy Validator Bot - Canonicalize and validate trading strategies",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        '-i', '--interactive',
        action='store_true',
        help='Run in interactive mode'
    )
    
    parser.add_argument(
        '-f', '--file',
        type=str,
        help='Process strategy from file'
    )
    
    parser.add_argument(
        '-o', '--output',
        type=str,
        help='Output file path (for file mode)'
    )
    
    parser.add_argument(
        '-t', '--text',
        type=str,
        help='Process strategy from command line text'
    )
    
    parser.add_argument(
        '--format',
        choices=['formatted', 'json', 'compact'],
        default='formatted',
        help='Output format (default: formatted)'
    )
    
    parser.add_argument(
        '-u', '--username',
        type=str,
        default='cli_user',
        help='Username for provenance tracking'
    )
    
    parser.add_argument(
        '--strict',
        action='store_true',
        help='Enable strict mode (raise exceptions on violations)'
    )
    
    parser.add_argument(
        '--examples',
        action='store_true',
        help='List all example strategies'
    )
    
    parser.add_argument(
        '--example',
        type=int,
        help='Run specific example by ID'
    )
    
    parser.add_argument(
        '--prompt',
        action='store_true',
        help='Show the system prompt'
    )
    
    args = parser.parse_args()
    
    # Create CLI instance
    cli = StrategyValidatorCLI(username=args.username, strict_mode=args.strict)
    
    # Handle different modes
    if args.prompt:
        cli._show_system_prompt()
    elif args.examples:
        cli._list_examples()
    elif args.example:
        cli._run_example(args.example)
    elif args.interactive:
        cli.interactive_mode()
    elif args.file:
        cli.process_file(args.file, args.output)
    elif args.text:
        cli.process_text(args.text, args.format)
    else:
        # Default to interactive mode
        cli.interactive_mode()


if __name__ == "__main__":
    main()
