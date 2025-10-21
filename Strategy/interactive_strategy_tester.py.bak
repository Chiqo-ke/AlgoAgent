"""
Interactive Strategy Tester - User-friendly interface to test strategy validation
Allows users to interact with the system as they would in production.
"""

import sys
import os
from pathlib import Path
from datetime import datetime
import json
from typing import Dict

# Add Strategy directory to path
sys.path.insert(0, str(Path(__file__).parent))

from strategy_validator import StrategyValidatorBot
from examples import EXAMPLE_1_EMA_CROSSOVER, EXAMPLE_2_RSI_MEAN_REVERSION, EXAMPLE_3_SCALPING_NUMBERED


class InteractiveStrategyTester:
    """Interactive interface for testing strategy validation system."""
    
    def __init__(self):
        """Initialize the tester."""
        self.bot = None
        self.username = "test_user"
        self.session_strategies = []
        self.print_banner()
    
    def print_banner(self):
        """Print welcome banner."""
        print("\n" + "=" * 80)
        print("  ALGOAGENT STRATEGY VALIDATOR - Interactive Testing Mode")
        print("=" * 80)
        print("\n  Test the strategy validation system with AI-powered analysis")
        print("  Using Gemini API for intelligent recommendations\n")
        print("=" * 80 + "\n")
    
    def print_menu(self):
        """Print main menu."""
        print("\n" + "-" * 80)
        print("MAIN MENU")
        print("-" * 80)
        print("1. Enter a new strategy (free text)")
        print("2. Enter a strategy (numbered steps)")
        print("3. Load example strategy")
        print("4. Analyze strategy from URL")
        print("5. View session history")
        print("6. Configure settings")
        print("7. Help / Usage guide")
        print("8. Exit")
        print("-" * 80)
    
    def get_username(self):
        """Get username from user."""
        print("\n📝 First, let's set up your session\n")
        username = input("Enter your username (default: test_user): ").strip()
        if username:
            self.username = username
        print(f"\n✓ Welcome, {self.username}!")
    
    def initialize_bot(self, use_gemini=True, strict_mode=False):
        """Initialize the strategy validator bot."""
        print(f"\n🤖 Initializing Strategy Validator Bot...")
        print(f"   Username: {self.username}")
        print(f"   Gemini AI: {'Enabled' if use_gemini else 'Disabled'}")
        print(f"   Strict Mode: {'On' if strict_mode else 'Off'}")
        
        self.bot = StrategyValidatorBot(
            username=self.username,
            strict_mode=strict_mode,
            use_gemini=use_gemini
        )
        print("✓ Bot initialized successfully\n")
    
    def enter_freetext_strategy(self):
        """Allow user to enter strategy as free text."""
        print("\n" + "=" * 80)
        print("ENTER STRATEGY (Free Text)")
        print("=" * 80)
        print("\nDescribe your trading strategy in plain English.")
        print("Include entry rules, exit rules, position sizing, and risk management.")
        print("\nExample:")
        print("  'Buy when 50 EMA crosses above 200 EMA. Set stop loss at 2%.")
        print("   Take profit at 5%. Risk 1% of account per trade.'\n")
        print("Enter your strategy (press Enter twice when done):")
        print("-" * 80)
        
        lines = []
        empty_count = 0
        while empty_count < 2:
            line = input()
            if line.strip():
                lines.append(line)
                empty_count = 0
            else:
                empty_count += 1
        
        strategy_text = "\n".join(lines).strip()
        
        if not strategy_text:
            print("\n⚠ No strategy entered. Returning to menu.")
            return
        
        self.process_strategy(strategy_text, "freetext")
    
    def enter_numbered_strategy(self):
        """Allow user to enter strategy as numbered steps."""
        print("\n" + "=" * 80)
        print("ENTER STRATEGY (Numbered Steps)")
        print("=" * 80)
        print("\nEnter your strategy as numbered steps.")
        print("\nExample:")
        print("  1. Entry: Buy when RSI < 30")
        print("  2. Exit: Sell when RSI > 70")
        print("  3. Stop: 2% below entry")
        print("  4. Size: Risk 1% per trade\n")
        print("Enter your steps (press Enter twice when done):")
        print("-" * 80)
        
        lines = []
        empty_count = 0
        while empty_count < 2:
            line = input()
            if line.strip():
                lines.append(line)
                empty_count = 0
            else:
                empty_count += 1
        
        strategy_text = "\n".join(lines).strip()
        
        if not strategy_text:
            print("\n⚠ No strategy entered. Returning to menu.")
            return
        
        self.process_strategy(strategy_text, "numbered")
    
    def load_example_strategy(self):
        """Load and process an example strategy."""
        print("\n" + "=" * 80)
        print("EXAMPLE STRATEGIES")
        print("=" * 80)
        print("\n1. EMA Crossover Strategy")
        print("2. RSI Mean Reversion Strategy")
        print("3. Scalping Strategy (Numbered Steps)")
        print("4. Back to Main Menu")
        
        choice = input("\nSelect example (1-4): ").strip()
        
        examples = {
            "1": ("EMA Crossover", EXAMPLE_1_EMA_CROSSOVER),
            "2": ("RSI Mean Reversion", EXAMPLE_2_RSI_MEAN_REVERSION),
            "3": ("Scalping Strategy", EXAMPLE_3_SCALPING_NUMBERED)
        }
        
        if choice in examples:
            name, strategy_text = examples[choice]
            print(f"\n📋 Loading: {name}")
            print("-" * 80)
            print(strategy_text)
            print("-" * 80)
            self.process_strategy(strategy_text, "auto")
        elif choice == "4":
            return
        else:
            print("\n⚠ Invalid choice.")
    
    def analyze_url(self):
        """Analyze strategy from URL."""
        print("\n" + "=" * 80)
        print("ANALYZE STRATEGY FROM URL")
        print("=" * 80)
        print("\nEnter a URL containing a trading strategy:")
        print("(YouTube videos, blog posts, articles, etc.)\n")
        
        url = input("URL: ").strip()
        
        if not url:
            print("\n⚠ No URL entered. Returning to menu.")
            return
        
        if not url.startswith("http"):
            print("\n⚠ Invalid URL. Must start with http:// or https://")
            return
        
        self.process_strategy(url, "url")
    
    def process_strategy(self, strategy_text: str, input_type: str = "auto"):
        """Process a strategy through the validator."""
        print("\n" + "=" * 80)
        print("PROCESSING STRATEGY...")
        print("=" * 80)
        
        if not self.bot:
            self.initialize_bot()
        
        # Process the strategy
        print("\n⏳ Analyzing strategy with AI assistance...")
        result = self.bot.process_input(strategy_text, input_type)
        
        # Display results
        self.display_results(result, strategy_text)
        
        # Save to session history
        self.session_strategies.append({
            "timestamp": datetime.now().isoformat(),
            "input": strategy_text[:100] + "..." if len(strategy_text) > 100 else strategy_text,
            "status": result["status"],
            "result": result
        })
        
        # Offer next actions
        self.offer_next_actions(result)
    
    def display_results(self, result: Dict, original_input: str):
        """Display validation results in a user-friendly format."""
        print("\n" + "=" * 80)
        print("VALIDATION RESULTS")
        print("=" * 80)
        
        status = result.get("status", "unknown")
        
        if status == "success":
            print("\n✓ STATUS: Strategy validated successfully")
            
            # Display canonicalized steps
            print("\n" + "-" * 80)
            print("CANONICALIZED STEPS")
            print("-" * 80)
            steps = result.get("canonicalized_steps", "")
            print(steps if steps else "No steps generated")
            
            # Display classification
            print("\n" + "-" * 80)
            print("CLASSIFICATION & METADATA")
            print("-" * 80)
            classification = result.get("classification", "")
            print(classification if classification else "No classification")
            
            # Display recommendations
            print("\n" + "-" * 80)
            print("AI-POWERED RECOMMENDATIONS")
            print("-" * 80)
            recommendations = result.get("recommendations", "")
            print(recommendations if recommendations else "No recommendations")
            
            # Display confidence and next actions
            print("\n" + "-" * 80)
            print("CONFIDENCE & NEXT ACTIONS")
            print("-" * 80)
            confidence = result.get("confidence", "unknown")
            print(f"Confidence Level: {confidence.upper()}")
            
            next_actions = result.get("next_actions", [])
            if next_actions:
                print("\nSuggested Next Actions:")
                for i, action in enumerate(next_actions, 1):
                    print(f"  {i}. {action}")
            
            # Show warnings if any
            warnings = result.get("warnings", [])
            if warnings:
                print("\n" + "-" * 80)
                print("⚠ WARNINGS")
                print("-" * 80)
                for warning in warnings:
                    print(f"  • {warning}")
        
        elif status == "error":
            print("\n❌ STATUS: Validation failed")
            print(f"\nError: {result.get('message', 'Unknown error')}")
            
            issues = result.get("issues", [])
            if issues:
                print("\nIssues detected:")
                for issue in issues:
                    print(f"  • {issue}")
        
        elif status == "approval_required":
            print("\n⚠ STATUS: Approval required")
            print(f"\n{result.get('message', 'This action requires approval')}")
        
        print("\n" + "=" * 80)
    
    def offer_next_actions(self, result: Dict):
        """Offer interactive next actions based on results."""
        if result.get("status") != "success":
            input("\nPress Enter to continue...")
            return
        
        print("\nWhat would you like to do next?")
        print("1. View canonical JSON")
        print("2. Save results to file")
        print("3. Modify strategy")
        print("4. Return to main menu")
        
        choice = input("\nSelect action (1-4): ").strip()
        
        if choice == "1":
            self.show_canonical_json(result)
        elif choice == "2":
            self.save_results(result)
        elif choice == "3":
            print("\n(Strategy modification not yet implemented)")
            input("Press Enter to continue...")
        elif choice == "4":
            return
        else:
            print("\n⚠ Invalid choice.")
    
    def show_canonical_json(self, result: Dict):
        """Display canonical JSON in formatted view."""
        print("\n" + "=" * 80)
        print("CANONICAL JSON SCHEMA")
        print("=" * 80)
        
        json_str = result.get("canonical_json", "{}")
        try:
            json_obj = json.loads(json_str)
            formatted = json.dumps(json_obj, indent=2)
            print(f"\n{formatted}")
        except:
            print(f"\n{json_str}")
        
        print("\n" + "=" * 80)
        input("\nPress Enter to continue...")
    
    def save_results(self, result: Dict):
        """Save results to file."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"strategy_result_{timestamp}.json"
        
        try:
            with open(filename, 'w') as f:
                json.dump(result, f, indent=2)
            print(f"\n✓ Results saved to: {filename}")
        except Exception as e:
            print(f"\n❌ Error saving file: {e}")
        
        input("\nPress Enter to continue...")
    
    def view_session_history(self):
        """View strategies analyzed in this session."""
        print("\n" + "=" * 80)
        print("SESSION HISTORY")
        print("=" * 80)
        
        if not self.session_strategies:
            print("\nNo strategies analyzed yet in this session.")
        else:
            for i, item in enumerate(self.session_strategies, 1):
                print(f"\n{i}. [{item['status'].upper()}] {item['timestamp']}")
                print(f"   Input: {item['input']}")
        
        input("\nPress Enter to continue...")
    
    def configure_settings(self):
        """Configure bot settings."""
        print("\n" + "=" * 80)
        print("CONFIGURATION")
        print("=" * 80)
        
        print("\n1. Enable/Disable Gemini AI")
        print("2. Toggle Strict Mode")
        print("3. Change Username")
        print("4. Back to Main Menu")
        
        choice = input("\nSelect option (1-4): ").strip()
        
        if choice == "1":
            use_gemini = input("\nEnable Gemini AI? (y/n): ").strip().lower() == 'y'
            self.initialize_bot(use_gemini=use_gemini, strict_mode=self.bot.strict_mode if self.bot else False)
        elif choice == "2":
            strict = input("\nEnable Strict Mode? (y/n): ").strip().lower() == 'y'
            self.initialize_bot(use_gemini=self.bot.use_gemini if self.bot else True, strict_mode=strict)
        elif choice == "3":
            self.get_username()
            self.bot = None
        elif choice == "4":
            return
    
    def show_help(self):
        """Show help and usage guide."""
        print("\n" + "=" * 80)
        print("HELP & USAGE GUIDE")
        print("=" * 80)
        
        help_text = """
OVERVIEW:
This interactive tester allows you to test the AlgoAgent Strategy Validator system.
The system uses AI (Gemini API) to analyze trading strategies and provide intelligent
recommendations.

FEATURES:
• Multi-format input: Free text, numbered steps, or URLs
• AI-powered analysis and recommendations
• Security guardrails to detect risky strategies
• Canonical JSON schema output
• Classification and risk assessment

HOW TO USE:
1. Enter your trading strategy in plain English or numbered steps
2. The system will analyze and structure your strategy
3. Review the canonicalized steps, classification, and recommendations
4. Save results or modify your strategy

INPUT FORMATS:
• Free text: "Buy when price breaks resistance. Sell at 5% profit."
• Numbered: "1. Buy when RSI < 30  2. Sell when RSI > 70"
• URL: Paste a link to a YouTube video, blog post, or article

AI FEATURES:
• Extracts strategy steps from unstructured text
• Identifies missing elements (stops, sizing, etc.)
• Generates prioritized recommendations
• Suggests test parameters and improvements

SECURITY:
• Detects pump-and-dump schemes
• Warns about excessive risk
• Blocks credential requests
• Requires approval for live trading

For more information, see the Strategy/README.md file.
        """
        
        print(help_text)
        input("\nPress Enter to continue...")
    
    def run(self):
        """Run the interactive tester."""
        self.get_username()
        self.initialize_bot()
        
        while True:
            self.print_menu()
            choice = input("\nSelect option (1-8): ").strip()
            
            if choice == "1":
                self.enter_freetext_strategy()
            elif choice == "2":
                self.enter_numbered_strategy()
            elif choice == "3":
                self.load_example_strategy()
            elif choice == "4":
                self.analyze_url()
            elif choice == "5":
                self.view_session_history()
            elif choice == "6":
                self.configure_settings()
            elif choice == "7":
                self.show_help()
            elif choice == "8":
                print("\n👋 Thank you for using AlgoAgent Strategy Validator!")
                print("=" * 80 + "\n")
                break
            else:
                print("\n⚠ Invalid option. Please select 1-8.")


def main():
    """Main entry point."""
    tester = InteractiveStrategyTester()
    try:
        tester.run()
    except KeyboardInterrupt:
        print("\n\n👋 Interrupted by user. Exiting...")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
