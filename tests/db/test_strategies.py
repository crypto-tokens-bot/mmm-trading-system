import pytest
from src.db.queries.strategies import add_strategy, get_strategy_by_id
from uuid import uuid4

# Generate test UUID
TEST_EVENT_MANAGER_ID = uuid4()

def test_add_and_get_strategy():
    """Test inserting and retrieving a strategy from the database."""

    strategy_id = add_strategy(
        event_manager_id=TEST_EVENT_MANAGER_ID,
        trading_pair="BTC/USDT",
        strategy_name="Test Strategy",
        status="active",
        parameters="{}"
    )

    strategy = get_strategy_by_id(strategy_id)

    # Validate strategy data
    assert strategy, "Strategy not found!"
    strategy = strategy[0]
    assert strategy["strategy_id"] == strategy_id, "Strategy ID does not match!"
    assert strategy["strategy_name"] == "Test Strategy", "Strategy name does not match!"
    assert strategy["parameters"] == "{}", "Strategy parameters do not match!"
