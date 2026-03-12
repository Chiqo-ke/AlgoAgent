
import os
import sys
import unittest
from pathlib import Path
import logging

# Ensure the root directory is in the Python path
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

from Backtest.gemini_strategy_generator import GeminiStrategyGenerator
from Backtest.bot_executor import get_bot_executor

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TestEndToEndStrategyGeneration(unittest.TestCase):

    def setUp(self):
        """Set up the test environment."""
        self.generator = GeminiStrategyGenerator()
        self.executor = get_bot_executor()
        self.strategy_description = "A simple moving average crossover strategy using 20 and 50-period EMAs."
        self.strategy_name = "EmaCrossoverTestStrategy"
        self.output_dir = Path(__file__).parent / "codes"
        self.output_dir.mkdir(exist_ok=True)
        self.output_file = self.output_dir / f"{self.strategy_name}.py"

    def tearDown(self):
        """Clean up generated files after the test."""
        if self.output_file.exists():
            try:
                self.output_file.unlink()
                logger.info(f"Cleaned up {self.output_file}")
            except OSError as e:
                logger.error(f"Error cleaning up file {self.output_file}: {e}")

    def test_generate_save_and_execute_strategy(self):
        """
        Test the full end-to-end process:
        1. Generate a strategy from a description.
        2. Save it to a file.
        3. Execute the generated file as a backtest.
        4. Check if the execution was successful and a results file was created.
        """
        logger.info("--- Starting E2E Test: Generate, Save, and Execute ---")

        # 1. Generate and Save
        logger.info(f"Generating strategy: '{self.strategy_description}'")
        saved_path, _ = self.generator.generate_and_save(
            description=self.strategy_description,
            output_path=str(self.output_file),
            strategy_name=self.strategy_name,
            execute_after_generation=False  # We will execute it manually
        )
        self.assertTrue(saved_path.exists(), "Strategy file was not created.")
        self.assertEqual(saved_path, self.output_file)
        logger.info(f"Strategy successfully saved to {saved_path}")

        # Verify file content
        content = saved_path.read_text()
        self.assertIn(f"class {self.strategy_name}", content, "Strategy class name not found in file.")
        self.assertIn("def run_backtest", content, "run_backtest function not found in file.")
        logger.info("File content verified.")

        # 2. Execute the generated strategy
        logger.info(f"Executing generated strategy file: {self.output_file}")
        execution_result = self.executor.execute_bot(
            strategy_file=str(self.output_file),
            strategy_name=self.strategy_name,
            description=self.strategy_description,
            test_symbol="MSFT",
            test_period_days=90  # Use a shorter period for a quick test
        )

        # 3. Assert the results
        logger.info(f"Execution finished. Success: {execution_result.success}")
        if not execution_result.success:
            logger.error(f"Execution Error: {execution_result.error}")
            logger.error(f"Stderr: {execution_result.stderr}")

        self.assertTrue(execution_result.success, "Bot execution failed.")
        self.assertIsNone(execution_result.error, f"Execution resulted in an error: {execution_result.error}")
        
        self.assertIsNotNone(execution_result.results_file, "Results file path is missing.")
        results_path = Path(execution_result.results_file)
        self.assertTrue(results_path.exists(), "Execution did not produce a results file.")
        
        logger.info(f"Execution successful. Results file created at: {results_path}")
        logger.info("--- E2E Test Passed ---")


if __name__ == "__main__":
    unittest.main()
