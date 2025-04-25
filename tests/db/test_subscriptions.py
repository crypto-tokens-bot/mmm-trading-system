import pytest
from src.db.queries.strategy_subscriptions import add_strategy_subscription, get_subscriptions_by_portfolio
from uuid import uuid4

# Generate test UUIDs
TEST_PORTFOLIO_ID = uuid4()
TEST_STRATEGY_ID = uuid4()

def test_add_and_get_strategy_subscription():
    """Test inserting and retrieving a strategy subscription from the database."""

    add_strategy_subscription(
        portfolio_id=TEST_PORTFOLIO_ID,
        strategy_id=TEST_STRATEGY_ID
    )

    subscriptions = get_subscriptions_by_portfolio(TEST_PORTFOLIO_ID)

    # Validate subscription data
    assert subscriptions, "Subscription not found!"
    subscription = subscriptions[0]
    assert subscription["portfolio_id"] == TEST_PORTFOLIO_ID, "Portfolio ID does not match!"
    assert subscription["strategy_id"] == TEST_STRATEGY_ID, "Strategy ID does not match!"
