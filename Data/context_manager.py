# AlgoAgent/Data/context_manager.py

from typing import List, Dict, Any

class ContextManager:
    def __init__(self):
        self._context = {}

    def set_context(self, key: str, value: Any):
        """Sets a specific key-value pair in the context."""
        self._context[key] = value

    def get_context(self, key: str, default: Any = None) -> Any:
        """Retrieves a value from the context, with an optional default."""
        return self._context.get(key, default)

    def update_context(self, new_context: Dict[str, Any]):
        """Updates the entire context with a new dictionary."""
        self._context.update(new_context)

    def get_all_context(self) -> Dict[str, Any]:
        """Returns the entire current context."""
        return self._context.copy()

    def get_required_indicators(self) -> List[Dict[str, Any]]:
        """
        Retrieves the list of required indicators from the context.
        Expected format: [{'name': 'SMA', 'timeperiod': 20}, ...]
        """
        return self._context.get('required_indicators', [])

    def set_required_indicators(self, indicators: List[Dict[str, Any]]):
        """Sets the list of required indicators in the context."""
        self._context['required_indicators'] = indicators

    def get_security_ticker(self) -> str:
        """Retrieves the financial security ticker from the context."""
        return self._context.get('security_ticker', None)

    def set_security_ticker(self, ticker: str):
        """Sets the financial security ticker in the context."""
        self._context['security_ticker'] = ticker

if __name__ == "__main__":
    manager = ContextManager()

    # Set initial context
    manager.set_context('security_ticker', 'AAPL')
    manager.set_required_indicators([
        {'name': 'SMA', 'timeperiod': 20},
        {'name': 'RSI', 'timeperiod': 14}
    ])
    manager.set_context('data_period', '1y')
    manager.set_context('data_interval', '1d')

    print("Initial Context:", manager.get_all_context())

    # Get specific context items
    ticker = manager.get_security_ticker()
    indicators = manager.get_required_indicators()
    period = manager.get_context('data_period')

    print(f"\nTicker: {ticker}")
    print(f"Required Indicators: {indicators}")
    print(f"Data Period: {period}")

    # Update context
    manager.update_context({
        'security_ticker': 'GOOG',
        'data_interval': '1h',
        'new_setting': True
    })

    print("\nUpdated Context:", manager.get_all_context())

    # Add another indicator
    current_indicators = manager.get_required_indicators()
    current_indicators.append({'name': 'MACD'})
    manager.set_required_indicators(current_indicators)

    print("\nContext after adding MACD:", manager.get_all_context())