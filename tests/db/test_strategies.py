import pytest
from src.db.queries.strategies import add_strategy, get_strategy_by_id
from uuid import uuid4

# Generate test UUIDs
TEST_STRATEGY_ID = uuid4()
TEST_EVENT_MANAGER_ID = uuid4()

def test_add_and_get_strategy():
    """Test inserting and retrieving a strategy from the database."""

    add_strategy(
        strategy_id=TEST_STRATEGY_ID,
        event_manager_id=TEST_EVENT_MANAGER_ID,
        trading_pair="BTC/USDT",
        strategy_name="Test Strategy",
        status="active",
        parameters="{}"
    )

    strategy = get_strategy_by_id(TEST_STRATEGY_ID)

    # Validate strategy data
    assert strategy, "Strategy not found!"
    strategy = strategy[0]
    assert strategy["strategy_id"] == TEST_STRATEGY_ID, "Strategy ID does not match!"
    assert strategy["strategy_name"] == "Test Strategy", "Strategy name does not match!"
    assert strategy["parameters"] == "{}", "Strategy parameters do not match!"
