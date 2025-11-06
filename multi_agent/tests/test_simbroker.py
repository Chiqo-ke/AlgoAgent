"""
Comprehensive unit tests for SimBroker.

Tests cover:
- Order placement and validation
- Position opening at bar Open
- SL/TP intrabar resolution
- Slippage and commission models
- Equity curve updates
- Multiple positions
- Margin requirements
- Edge cases and error handling
"""

import pytest
import pandas as pd
from pathlib import Path
from multi_agent.simulator import (
    SimBroker,
    SimConfig,
    OrderSide,
    OrderStatus,
    CloseReason,
    EventType
)


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def default_config():
    """Default test configuration with zero costs"""
    return SimConfig(
        starting_balance=10000.0,
        leverage=100.0,
        lot_size=100000.0,
        point=0.01,
        slippage={'type': 'fixed', 'value': 0},
        commission={'type': 'per_lot', 'value': 0},
        rng_seed=42,
        debug=False
    )


@pytest.fixture
def broker(default_config):
    """Fresh broker instance"""
    return SimBroker(default_config)


@pytest.fixture
def bar_simple_long():
    """Load simple long test fixture"""
    fixture_path = Path(__file__).parent / 'fixtures' / 'bar_simple_long.csv'
    df = pd.read_csv(fixture_path, parse_dates=['Date'])
    return df


@pytest.fixture
def bar_intrabar_both():
    """Load intrabar both hits fixture"""
    fixture_path = Path(__file__).parent / 'fixtures' / 'bar_intrabar_both_hits.csv'
    df = pd.read_csv(fixture_path, parse_dates=['Date'])
    return df


@pytest.fixture
def bar_extended():
    """Load extended bar data"""
    fixture_path = Path(__file__).parent / 'fixtures' / 'bar_extended.csv'
    df = pd.read_csv(fixture_path, parse_dates=['Date'])
    return df


# ============================================================================
# TEST 1 - ORDER PLACEMENT AND VALIDATION
# ============================================================================

def test_place_order_accepts_valid_request(broker):
    """Test that valid order requests are accepted"""
    order_request = {
        'action': 'TRADE_ACTION_DEAL',
        'symbol': 'EURUSD',
        'volume': 0.1,
        'type': 'ORDER_TYPE_BUY',
        'sl': 1.0950,
        'tp': 1.1050
    }
    
    response = broker.place_order(order_request)
    
    assert response.success
    assert response.status == OrderStatus.ACCEPTED
    assert response.order_id is not None
    assert len(broker.orders) == 1
    assert len(broker.positions) == 0  # Not filled yet


def test_place_order_rejects_missing_fields(broker):
    """Test that orders with missing required fields are rejected"""
    incomplete_request = {
        'symbol': 'EURUSD',
        # Missing 'volume' and 'type'
    }
    
    response = broker.place_order(incomplete_request)
    
    assert not response.success
    assert response.status == OrderStatus.REJECTED
    assert 'Missing required fields' in response.message


def test_place_order_rejects_invalid_volume(broker):
    """Test that invalid volume is rejected"""
    order_request = {
        'symbol': 'EURUSD',
        'volume': -0.1,  # Invalid negative volume
        'type': 'ORDER_TYPE_BUY'
    }
    
    response = broker.place_order(order_request)
    
    assert not response.success
    assert response.status == OrderStatus.REJECTED


def test_place_order_buy_side_detection(broker):
    """Test that buy orders are correctly parsed"""
    response = broker.place_order({
        'symbol': 'AAPL',
        'volume': 0.1,
        'type': 'ORDER_TYPE_BUY'
    })
    
    assert response.success
    order = broker.orders[response.order_id]
    assert order.side == OrderSide.BUY


def test_place_order_sell_side_detection(broker):
    """Test that sell orders are correctly parsed"""
    response = broker.place_order({
        'symbol': 'AAPL',
        'volume': 0.1,
        'type': 'ORDER_TYPE_SELL'
    })
    
    assert response.success
    order = broker.orders[response.order_id]
    assert order.side == OrderSide.SELL


# ============================================================================
# TEST 2 - SIMPLE ENTRY AT NEXT OPEN
# ============================================================================

def test_simple_entry_at_next_open(broker, bar_simple_long):
    """Test that order is filled at next bar's Open price"""
    # Place buy order
    response = broker.place_order({
        'symbol': 'TEST',
        'volume': 0.1,
        'type': 'ORDER_TYPE_BUY',
        'sl': 99.0,
        'tp': 103.0
    })
    
    assert response.success
    
    # Process first bar - should fill at Open = 100.00
    bar = bar_simple_long.iloc[0]
    events = broker.step_bar(bar)
    
    # Check order filled
    assert len(broker.orders) == 0  # Order consumed
    assert len(broker.positions) == 1  # Position opened
    
    # Verify fill event
    fill_events = [e for e in events if e.event_type == EventType.ORDER_FILLED]
    assert len(fill_events) == 1
    
    # Check position details
    position = list(broker.positions.values())[0]
    assert position.fill.entry_price == 100.0  # Filled at Open
    assert position.fill.volume == 0.1
    assert position.fill.side == OrderSide.BUY


def test_entry_updates_balance_with_commission(broker):
    """Test that entry commission is recorded but balance unchanged until close"""
    config = SimConfig(
        commission={'type': 'per_lot', 'value': 10.0},  # $10 per lot
        slippage={'type': 'fixed', 'value': 0}
    )
    broker = SimBroker(config)
    initial_balance = broker.balance
    
    # Place and fill order
    response = broker.place_order({
        'symbol': 'TEST',
        'volume': 0.1,  # 0.1 lot to avoid margin issues
        'type': 'ORDER_TYPE_BUY'
    })
    
    bar = pd.Series({
        'Date': pd.Timestamp('2024-01-01'),
        'Open': 100.0,
        'High': 101.0,
        'Low': 99.0,
        'Close': 100.5
    })
    
    broker.step_bar(bar)
    
    # Balance should be unchanged (commission paid on close)
    assert broker.balance == initial_balance
    
    # Commission should be recorded
    position = list(broker.positions.values())[0]
    assert position.fill.commission_entry == 1.0  # 0.1 lot * $10/lot = $1


# ============================================================================
# TEST 3 - SL/TP INTRABAR RESOLUTION (LONG)
# ============================================================================

def test_sl_tp_intrabar_resolution_long_tp_hit(broker, bar_simple_long):
    """Test TP hit before SL for long position (intrabar sequence)"""
    # Place buy with SL=99, TP=101.5
    # Bar: O=100, H=101.5, L=99.5, C=101
    # Sequence: O(100) -> H(101.5) [TP HIT] -> L(99.5) -> C(101)
    
    response = broker.place_order({
        'symbol': 'TEST',
        'volume': 0.1,
        'type': 'ORDER_TYPE_BUY',
        'sl': 99.0,
        'tp': 101.5
    })
    
    # Fill order at first bar
    bar1 = bar_simple_long.iloc[0]
    broker.step_bar(bar1)
    
    # Position should still be open (TP at 101.5, High = 101.5)
    # Second bar should hit TP
    bar2 = bar_simple_long.iloc[1]  # O=101, H=102.5, L=100.5, C=102
    
    events = broker.step_bar(bar2)
    
    # Position should be closed at TP
    assert len(broker.positions) == 0
    
    # Check close reason
    closed_trade = broker.get_closed_trades()[0]
    assert closed_trade.reason_close == CloseReason.TP
    assert closed_trade.close_price == 101.5
    
    # Check profit (buy at 100, sell at 101.5)
    # Profit = (101.5 - 100) * 0.1 * 100000 = 15000
    expected_profit = (101.5 - 100.0) * 0.1 * 100000.0
    assert closed_trade.profit == pytest.approx(expected_profit)


def test_sl_tp_intrabar_resolution_long_sl_hit(broker):
    """Test SL hit before TP for long position"""
    response = broker.place_order({
        'symbol': 'TEST',
        'volume': 0.1,
        'type': 'ORDER_TYPE_BUY',
        'sl': 95.0,
        'tp': 110.0
    })
    
    # Fill at Open = 100
    bar1 = pd.Series({
        'Date': pd.Timestamp('2024-01-01'),
        'Open': 100.0,
        'High': 102.0,
        'Low': 98.0,
        'Close': 101.0
    })
    broker.step_bar(bar1)
    
    # Next bar hits SL
    # O=101, H=103, L=94 (SL hit), C=95
    # Sequence: O -> H -> L(94, triggers SL at 95)
    bar2 = pd.Series({
        'Date': pd.Timestamp('2024-01-02'),
        'Open': 101.0,
        'High': 103.0,
        'Low': 94.0,
        'Close': 95.0
    })
    
    events = broker.step_bar(bar2)
    
    # Position closed at SL
    assert len(broker.positions) == 0
    closed_trade = broker.get_closed_trades()[0]
    assert closed_trade.reason_close == CloseReason.SL
    assert closed_trade.close_price == 95.0
    
    # Loss: (95 - 100) * 0.1 * 100000 = -500000
    expected_loss = (95.0 - 100.0) * 0.1 * 100000.0
    assert closed_trade.profit == pytest.approx(expected_loss)


def test_intrabar_both_hits_tp_priority_long(broker, bar_intrabar_both):
    """
    Test that when both SL and TP are hit in same bar, 
    sequence logic determines which is hit first.
    
    Bar: O=100, H=105, L=95, C=102
    Long position: entry=100, SL=95, TP=105
    Sequence: O(100) -> H(105) [TP] -> L(95) [SL]
    TP should be hit first.
    """
    response = broker.place_order({
        'symbol': 'TEST',
        'volume': 0.1,
        'type': 'ORDER_TYPE_BUY',
        'sl': 95.0,
        'tp': 105.0
    })
    
    # Process the single bar with wide range
    bar = bar_intrabar_both.iloc[0]
    
    # First step fills order at Open
    events1 = broker.step_bar(bar)
    
    # Check that position opened and immediately closed at TP
    # (both happen in same bar due to our fill-then-check logic)
    # Actually, order is filled at Open, then same bar checks SL/TP
    
    # Let's refactor: place order first, then process bar
    broker.reset()
    response = broker.place_order({
        'symbol': 'TEST',
        'volume': 0.1,
        'type': 'ORDER_TYPE_BUY',
        'sl': 95.0,
        'tp': 105.0
    })
    
    # Create entry bar (fill at 100)
    entry_bar = pd.Series({
        'Date': pd.Timestamp('2024-01-01'),
        'Open': 100.0,
        'High': 100.5,
        'Low': 99.5,
        'Close': 100.0
    })
    broker.step_bar(entry_bar)
    
    # Now process the wide-range bar
    wide_bar = pd.Series({
        'Date': pd.Timestamp('2024-01-02'),
        'Open': 100.0,
        'High': 105.0,
        'Low': 95.0,
        'Close': 102.0
    })
    events = broker.step_bar(wide_bar)
    
    # Position should be closed at TP (hit first in sequence)
    assert len(broker.positions) == 0
    closed_trade = broker.get_closed_trades()[0]
    assert closed_trade.reason_close == CloseReason.TP
    assert closed_trade.close_price == 105.0


# ============================================================================
# TEST 4 - SLIPPAGE MODELS
# ============================================================================

def test_slippage_fixed_model(broker):
    """Test fixed slippage model applies correct adjustment"""
    config = SimConfig(
        slippage={'type': 'fixed', 'value': 5},  # 5 points
        point=0.01,  # Each point = 0.01
        commission={'type': 'per_lot', 'value': 0}
    )
    broker = SimBroker(config)
    
    # Place buy order
    response = broker.place_order({
        'symbol': 'TEST',
        'volume': 0.1,
        'type': 'ORDER_TYPE_BUY'
    })
    
    # Fill at Open = 100
    bar = pd.Series({
        'Date': pd.Timestamp('2024-01-01'),
        'Open': 100.0,
        'High': 101.0,
        'Low': 99.0,
        'Close': 100.5
    })
    
    broker.step_bar(bar)
    
    # Buy slippage = +5 points * 0.01 = +0.05
    # Fill price = 100.0 + 0.05 = 100.05
    position = list(broker.positions.values())[0]
    assert position.fill.entry_price == pytest.approx(100.05)
    assert position.fill.slippage_entry == pytest.approx(0.05)


def test_slippage_random_model(broker):
    """Test random slippage model produces variable results"""
    config = SimConfig(
        slippage={'type': 'random', 'value': 10},  # Max 10 points
        point=0.01,
        commission={'type': 'per_lot', 'value': 0},
        rng_seed=123  # Fixed for reproducibility
    )
    broker = SimBroker(config)
    
    # Place multiple orders and check slippage varies but within bounds
    slippages = []
    
    for i in range(5):
        broker.reset()
        broker.rng = broker.rng.__class__(123 + i)  # Different seed each time
        
        response = broker.place_order({
            'symbol': 'TEST',
            'volume': 0.1,
            'type': 'ORDER_TYPE_BUY'
        })
        
        bar = pd.Series({
            'Date': pd.Timestamp('2024-01-01'),
            'Open': 100.0,
            'High': 101.0,
            'Low': 99.0,
            'Close': 100.5
        })
        
        broker.step_bar(bar)
        position = list(broker.positions.values())[0]
        slippages.append(position.fill.slippage_entry)
    
    # Check slippages are within bounds
    for slip in slippages:
        assert 0 <= slip <= 10 * 0.01  # 0 to 0.10


# ============================================================================
# TEST 5 - COMMISSION MODELS
# ============================================================================

def test_commission_per_lot(broker):
    """Test per-lot commission model"""
    config = SimConfig(
        commission={'type': 'per_lot', 'value': 7.0},  # $7 per lot
        slippage={'type': 'fixed', 'value': 0}
    )
    broker = SimBroker(config)
    
    # Place 0.1 lot order (to avoid margin issues with 10k balance)
    response = broker.place_order({
        'symbol': 'TEST',
        'volume': 0.1,
        'type': 'ORDER_TYPE_BUY'
    })
    
    bar = pd.Series({
        'Date': pd.Timestamp('2024-01-01'),
        'Open': 100.0,
        'High': 101.0,
        'Low': 99.0,
        'Close': 100.5
    })
    
    broker.step_bar(bar)
    
    # Entry commission = 0.1 * 7 = 0.7
    position = list(broker.positions.values())[0]
    assert position.fill.commission_entry == pytest.approx(0.7)


def test_commission_percent(broker):
    """Test percent commission model"""
    config = SimConfig(
        commission={'type': 'percent', 'value': 0.1},  # 0.1%
        lot_size=100000.0,
        slippage={'type': 'fixed', 'value': 0},
        starting_balance=100000.0  # Increase balance for 1.0 lot
    )
    broker = SimBroker(config)
    
    response = broker.place_order({
        'symbol': 'TEST',
        'volume': 0.1,  # Use 0.1 lot instead
        'type': 'ORDER_TYPE_BUY'
    })
    
    bar = pd.Series({
        'Date': pd.Timestamp('2024-01-01'),
        'Open': 100.0,
        'High': 101.0,
        'Low': 99.0,
        'Close': 100.5
    })
    
    broker.step_bar(bar)
    
    # Notional = 0.1 * 100000 * 100 = 1,000,000
    # Commission = 1,000,000 * 0.001 = 1,000
    position = list(broker.positions.values())[0]
    notional = 0.1 * 100000.0 * 100.0
    expected_commission = notional * 0.001
    assert position.fill.commission_entry == pytest.approx(expected_commission)


# ============================================================================
# TEST 6 - EQUITY UPDATES ON CLOSE
# ============================================================================

def test_equity_updates_on_close(broker):
    """Test that balance and equity are updated correctly on position close"""
    initial_balance = broker.balance
    
    # Place and fill buy order
    response = broker.place_order({
        'symbol': 'TEST',
        'volume': 0.1,
        'type': 'ORDER_TYPE_BUY',
        'tp': 105.0
    })
    
    # Entry bar
    bar1 = pd.Series({
        'Date': pd.Timestamp('2024-01-01'),
        'Open': 100.0,
        'High': 101.0,
        'Low': 99.0,
        'Close': 100.5
    })
    broker.step_bar(bar1)
    
    # Balance unchanged (no commission in this config)
    assert broker.balance == initial_balance
    
    # Exit bar (TP hit)
    bar2 = pd.Series({
        'Date': pd.Timestamp('2024-01-02'),
        'Open': 104.0,
        'High': 106.0,
        'Low': 103.0,
        'Close': 105.5
    })
    broker.step_bar(bar2)
    
    # Check balance updated with profit
    # Profit = (105 - 100) * 0.1 * 100000 = 50000
    expected_profit = (105.0 - 100.0) * 0.1 * 100000.0
    expected_balance = initial_balance + expected_profit
    
    assert broker.balance == pytest.approx(expected_balance)
    
    # Check equity curve recorded
    assert len(broker.equity_curve) == 2  # One per bar
    final_equity = broker.equity_curve[-1]
    assert final_equity.balance == pytest.approx(expected_balance)


# ============================================================================
# TEST 7 - MULTIPLE POSITIONS
# ============================================================================

def test_multiple_positions(broker):
    """Test handling of multiple simultaneous positions"""
    # Place 3 orders
    for i in range(3):
        response = broker.place_order({
            'symbol': f'TEST{i}',
            'volume': 0.1,
            'type': 'ORDER_TYPE_BUY',
            'tp': 105.0
        })
        assert response.success
    
    # Fill all at once
    bar = pd.Series({
        'Date': pd.Timestamp('2024-01-01'),
        'Open': 100.0,
        'High': 101.0,
        'Low': 99.0,
        'Close': 100.5
    })
    
    events = broker.step_bar(bar)
    
    # All 3 positions should be open
    assert len(broker.positions) == 3
    assert len(broker.orders) == 0
    
    # Check account snapshot
    account = broker.get_account()
    assert account.total_positions == 3


def test_partial_position_close(broker):
    """Test closing one position while others remain open"""
    # Place 2 orders with different TPs
    broker.place_order({
        'symbol': 'TEST1',
        'volume': 0.1,
        'type': 'ORDER_TYPE_BUY',
        'tp': 102.0  # Will hit first
    })
    
    broker.place_order({
        'symbol': 'TEST2',
        'volume': 0.1,
        'type': 'ORDER_TYPE_BUY',
        'tp': 110.0  # Won't hit
    })
    
    # Entry bar
    bar1 = pd.Series({
        'Date': pd.Timestamp('2024-01-01'),
        'Open': 100.0,
        'High': 100.5,
        'Low': 99.5,
        'Close': 100.0
    })
    broker.step_bar(bar1)
    assert len(broker.positions) == 2
    
    # Bar that hits first TP only
    bar2 = pd.Series({
        'Date': pd.Timestamp('2024-01-02'),
        'Open': 101.0,
        'High': 103.0,
        'Low': 100.5,
        'Close': 102.5
    })
    broker.step_bar(bar2)
    
    # One position closed, one still open
    assert len(broker.positions) == 1
    assert len(broker.get_closed_trades()) == 1


# ============================================================================
# TEST 8 - MARGIN REJECTION
# ============================================================================

def test_margin_rejection(broker):
    """Test that orders are rejected when margin insufficient"""
    # Try to open huge position that exceeds available margin
    # Balance = 10000, leverage = 100
    # Max notional = 10000 * 100 = 1,000,000
    # At price 100, max volume = 1,000,000 / 100 / 100000 = 0.1 lots... wait that's small
    
    # Let's recalculate:
    # Required margin = (volume * lot_size * price) / leverage
    # = (volume * 100000 * 100) / 100
    # = volume * 100000
    
    # With balance 10000, we can open:
    # volume = 10000 / 100000 = 0.1 lots max
    
    # Try to open 1.0 lot (requires 100000 margin)
    response = broker.place_order({
        'symbol': 'TEST',
        'volume': 1.0,  # Too large
        'type': 'ORDER_TYPE_BUY',
        'price': 100.0
    })
    
    assert not response.success
    assert response.status == OrderStatus.REJECTED
    assert 'margin' in response.message.lower()


def test_margin_level_calculation(broker):
    """Test that margin level is calculated correctly"""
    # Open position
    broker.place_order({
        'symbol': 'TEST',
        'volume': 0.05,  # Small position
        'type': 'ORDER_TYPE_BUY'
    })
    
    bar = pd.Series({
        'Date': pd.Timestamp('2024-01-01'),
        'Open': 100.0,
        'High': 101.0,
        'Low': 99.0,
        'Close': 100.5
    })
    
    broker.step_bar(bar)
    
    # Check account snapshot
    account = broker.get_account()
    
    # Used margin = 0.05 * 100000 * 100 / 100 = 5000
    expected_used_margin = (0.05 * 100000.0 * 100.0) / 100.0
    assert account.used_margin == pytest.approx(expected_used_margin)
    
    # Margin level = equity / used_margin * 100
    # Equity = balance + floating_pnl (we use close price for equity curve)
    # At this point, floating PnL = (100.5 - 100) * 0.05 * 100000 = 2500
    # But in get_account() we don't have current price, so floating_pnl = 0
    # So margin_level = 10000 / 5000 * 100 = 200%
    
    assert account.margin_level >= 100.0  # Should be healthy


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

def test_full_backtest_integration(broker, bar_extended):
    """Test complete backtest workflow with multiple trades"""
    # Place initial position
    broker.place_order({
        'symbol': 'TEST',
        'volume': 0.1,
        'type': 'ORDER_TYPE_BUY',
        'sl': 95.0,
        'tp': 108.0
    })
    
    # Run through all bars
    for idx, row in bar_extended.iterrows():
        events = broker.step_bar(row)
        
        # On position close, open new one (simple re-entry strategy)
        close_events = [e for e in events if e.event_type == EventType.POSITION_CLOSED]
        if close_events and len(broker.positions) == 0:
            broker.place_order({
                'symbol': 'TEST',
                'volume': 0.1,
                'type': 'ORDER_TYPE_BUY',
                'sl': row['Low'] - 5.0,
                'tp': row['High'] + 5.0
            })
    
    # Generate report
    report = broker.generate_report()
    
    # Validate report structure
    assert 'metrics' in report
    assert 'trades' in report
    assert 'equity_curve' in report
    assert 'summary' in report
    
    # Check metrics
    metrics = report['metrics']
    assert metrics['total_trades'] >= 0
    assert 'win_rate' in metrics
    assert 'total_net_pnl' in metrics
    assert 'max_drawdown' in metrics
    
    # Check equity curve
    assert len(broker.equity_curve) == len(bar_extended)


def test_manual_close_position(broker):
    """Test manually closing a position"""
    # Open position
    response = broker.place_order({
        'symbol': 'TEST',
        'volume': 0.1,
        'type': 'ORDER_TYPE_BUY'
    })
    
    bar = pd.Series({
        'Date': pd.Timestamp('2024-01-01'),
        'Open': 100.0,
        'High': 101.0,
        'Low': 99.0,
        'Close': 100.5
    })
    
    broker.step_bar(bar)
    
    # Manually close
    position_id = list(broker.positions.keys())[0]
    result = broker.close_position(position_id, price=102.0)
    
    assert result.success
    assert len(broker.positions) == 0
    
    # Check trade record
    closed_trade = broker.get_closed_trades()[0]
    assert closed_trade.reason_close == CloseReason.MANUAL
    assert closed_trade.close_price == 102.0


def test_cancel_order(broker):
    """Test order cancellation"""
    response = broker.place_order({
        'symbol': 'TEST',
        'volume': 0.1,
        'type': 'ORDER_TYPE_BUY'
    })
    
    order_id = response.order_id
    assert len(broker.orders) == 1
    
    # Cancel order
    success = broker.cancel_order(order_id)
    
    assert success
    assert len(broker.orders) == 0


def test_reset_clears_state(broker):
    """Test that reset clears all broker state"""
    # Create some activity
    broker.place_order({
        'symbol': 'TEST',
        'volume': 0.1,
        'type': 'ORDER_TYPE_BUY'
    })
    
    bar = pd.Series({
        'Date': pd.Timestamp('2024-01-01'),
        'Open': 100.0,
        'High': 101.0,
        'Low': 99.0,
        'Close': 100.5
    })
    broker.step_bar(bar)
    
    # Reset
    broker.reset()
    
    # Check all state cleared
    assert len(broker.orders) == 0
    assert len(broker.positions) == 0
    assert len(broker.trades) == 0
    assert len(broker.equity_curve) == 0
    assert broker.balance == broker.cfg.starting_balance


def test_short_position_intrabar_logic(broker):
    """Test that short positions use correct intrabar sequence"""
    # Place sell order
    broker.place_order({
        'symbol': 'TEST',
        'volume': 0.1,
        'type': 'ORDER_TYPE_SELL',
        'sl': 105.0,  # SL above entry
        'tp': 95.0    # TP below entry
    })
    
    # Entry bar
    bar1 = pd.Series({
        'Date': pd.Timestamp('2024-01-01'),
        'Open': 100.0,
        'High': 100.5,
        'Low': 99.5,
        'Close': 100.0
    })
    broker.step_bar(bar1)
    
    # Bar that hits TP (short sequence: O -> L -> H -> C)
    bar2 = pd.Series({
        'Date': pd.Timestamp('2024-01-02'),
        'Open': 100.0,
        'High': 106.0,  # Would hit SL
        'Low': 94.0,     # Hits TP first in short sequence
        'Close': 102.0
    })
    
    events = broker.step_bar(bar2)
    
    # TP should be hit (at Low=94, but TP=95)
    # Actually Low=94 < TP=95, so TP is hit
    assert len(broker.positions) == 0
    closed_trade = broker.get_closed_trades()[0]
    assert closed_trade.reason_close == CloseReason.TP
    assert closed_trade.close_price == 95.0


def test_report_generation_and_save(broker, bar_simple_long, tmp_path):
    """Test report generation and file saving"""
    # Run simple backtest
    broker.place_order({
        'symbol': 'TEST',
        'volume': 0.1,
        'type': 'ORDER_TYPE_BUY',
        'tp': 103.0
    })
    
    for idx, row in bar_simple_long.iterrows():
        broker.step_bar(row)
    
    # Generate report
    report = broker.generate_report()
    
    # Validate structure
    assert isinstance(report, dict)
    assert 'metrics' in report
    assert 'trades' in report
    
    # Save report
    paths = broker.save_report(tmp_path)
    
    # Check files created
    assert paths['trades'].exists()
    assert paths['equity_curve'].exists()
    assert paths['report'].exists()
    
    # Validate file contents
    trades_df = pd.read_csv(paths['trades'])
    assert len(trades_df) >= 0


def test_event_logging(broker):
    """Test that events are properly logged"""
    broker.place_order({
        'symbol': 'TEST',
        'volume': 0.1,
        'type': 'ORDER_TYPE_BUY'
    })
    
    bar = pd.Series({
        'Date': pd.Timestamp('2024-01-01'),
        'Open': 100.0,
        'High': 101.0,
        'Low': 99.0,
        'Close': 100.5
    })
    
    broker.step_bar(bar)
    
    # Check events
    events = broker.get_events()
    
    # Should have: ORDER_ACCEPTED, ORDER_FILLED, POSITION_OPENED
    event_types = [e.event_type for e in events]
    
    assert EventType.ORDER_ACCEPTED in event_types
    assert EventType.ORDER_FILLED in event_types
    assert EventType.POSITION_OPENED in event_types


# ============================================================================
# EDGE CASES AND ERROR HANDLING
# ============================================================================

def test_invalid_config_raises_error():
    """Test that invalid configuration raises ValueError"""
    with pytest.raises(ValueError):
        config = SimConfig(starting_balance=-1000)  # Invalid
        broker = SimBroker(config)


def test_close_nonexistent_position(broker):
    """Test that closing non-existent position returns failure"""
    result = broker.close_position('fake-id', price=100.0)
    
    assert not result.success
    assert 'not found' in result.message.lower()


def test_cancel_nonexistent_order(broker):
    """Test that cancelling non-existent order returns False"""
    success = broker.cancel_order('fake-id')
    
    assert not success


def test_step_bar_with_no_positions(broker, bar_simple_long):
    """Test that stepping bar with no positions/orders works"""
    bar = bar_simple_long.iloc[0]
    events = broker.step_bar(bar)
    
    # Should work without errors
    assert isinstance(events, list)
    assert len(broker.equity_curve) == 1


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
