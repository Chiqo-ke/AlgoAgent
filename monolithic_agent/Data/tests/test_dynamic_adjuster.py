import pytest
import os
from Data.dynamic_code_adjuster import insert_snippet_if_missing
from Data.gemini_integrator import GeminiIntegrator

@pytest.fixture
def mock_adapter_file(tmp_path):
    """Creates a temporary adapter file for testing."""
    file_path = tmp_path / "mock_adapter.py"
    initial_content = """
import pandas as pd

def SMA(df: pd.DataFrame, params: dict) -> pd.DataFrame:
    return df # Dummy implementation

def EMA(df: pd.DataFrame, params: dict) -> pd.DataFrame:
    return df # Dummy implementation
"""
    file_path.write_text(initial_content)
    return str(file_path)


def test_insert_snippet_when_missing(mock_adapter_file):
    indicator_to_add = "VIX"
    gemini = GeminiIntegrator() # Using the mock implementation
    
    # Get the mock snippet from the mock GeminiIntegrator
    snippet = gemini.suggest_code_update(indicator_to_add)
    
    # Ensure the snippet is not just a comment
    assert not snippet.startswith("#")

    # Call the function to insert the snippet
    changed = insert_snippet_if_missing(mock_adapter_file, indicator_to_add, snippet)

    # Assert that the file was changed
    assert changed is True

    # Read the file and check that the new function is present
    with open(mock_adapter_file, 'r') as f:
        content = f.read()
    
    assert "def VIX(df: pd.DataFrame, params: dict)" in content
    assert "def SMA(df: pd.DataFrame, params: dict)" in content # Ensure old content is still there


def test_do_not_insert_snippet_when_present(mock_adapter_file):
    indicator_to_add = "SMA" # This indicator already exists in the mock file
    gemini = GeminiIntegrator()
    snippet = gemini.suggest_code_update(indicator_to_add)

    # Get original file content for comparison
    with open(mock_adapter_file, 'r') as f:
        original_content = f.read()

    # Call the function
    changed = insert_snippet_if_missing(mock_adapter_file, indicator_to_add, snippet)

    # Assert that the file was NOT changed
    assert changed is False

    # Read the content again and assert it's identical to the original
    with open(mock_adapter_file, 'r') as f:
        new_content = f.read()
    
    assert new_content == original_content
