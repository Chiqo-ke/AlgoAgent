import pytest
from Data.registry import register, get_entry, list_indicators, REGISTRY

# Clear the registry before each test to ensure isolation
@pytest.fixture(autouse=True)
def clear_registry():
    REGISTRY.clear()
    yield

def dummy_callable(*args, **kwargs):
    pass

def test_register_indicator():
    register("TestIndicator", dummy_callable, ["close"], ["test_output"], {"param1": 10})
    entry = get_entry("testindicator")
    assert entry is not None
    assert entry["callable"] == dummy_callable
    assert entry["inputs"] == ["close"]
    assert entry["outputs"] == ["test_output"]
    assert entry["defaults"] == {"param1": 10}
    assert entry["source_hint"] == "custom"

def test_register_indicator_case_insensitivity():
    register("TestIndicator", dummy_callable, ["close"], ["test_output"])
    entry = get_entry("testindicator")
    assert entry is not None
    entry_upper = get_entry("TESTINDICATOR")
    assert entry_upper is not None
    assert entry == entry_upper

def test_get_entry_non_existent():
    entry = get_entry("NonExistentIndicator")
    assert entry is None

def test_list_indicators_empty():
    indicators = list_indicators()
    assert indicators == []

def test_list_indicators_with_entries():
    register("IndicatorA", dummy_callable, ["close"], ["outputA"])
    register("IndicatorB", dummy_callable, ["open"], ["outputB"])
    indicators = list_indicators()
    assert "indicatora" in indicators
    assert "indicatorb" in indicators
    assert len(indicators) == 2

def test_register_with_no_defaults():
    register("NoDefaults", dummy_callable, ["high"], ["no_defaults_output"])
    entry = get_entry("nodefaults")
    assert entry["defaults"] == {}

def test_register_with_different_source_hint():
    register("TalibIndicator", dummy_callable, ["close"], ["talib_output"], source_hint="talib")
    entry = get_entry("talibindicator")
    assert entry["source_hint"] == "talib"