import pytest
from src.db.queries.portfolios import add_portfolio, get_portfolio_by_id
from uuid import uuid4

# Generate test UUIDs
TEST_EVENT_MANAGER_ID = uuid4()
TEST_RISK_CONTROLLER_ID = uuid4()

def test_add_and_get_portfolio():
    """Test inserting and retrieving a portfolio from the database."""

    portfolio_id = add_portfolio(
        event_manager_id=TEST_EVENT_MANAGER_ID,
        risk_controller_id=TEST_RISK_CONTROLLER_ID,
        portfolio_name="Test Portfolio",
        currency="USDT",
        initial_balance=10000,
        exchange="Binance"
    )

    # Retrieve the portfolio
    portfolio = get_portfolio_by_id(portfolio_id)

    # Validate portfolio data
    assert portfolio, "Portfolio not found!"
    portfolio = portfolio[0]
    assert portfolio["portfolio_id"] == portfolio_id, "Portfolio ID does not match!"
    assert portfolio["portfolio_name"] == "Test Portfolio", "Portfolio name does not match!"
    assert portfolio["currency"] == "USDT", "Currency does not match!"
