import pytest
from src.db.queries.orders import add_order, get_order_by_id
from uuid import uuid4

# Generate test UUIDs
TEST_PORTFOLIO_ID = uuid4()
TEST_EVENT_MANAGER_ID =uuid4()

def test_add_and_get_order():
    """Test inserting and retrieving an order from the database."""

    order_id = add_order(
        portfolio_id=TEST_PORTFOLIO_ID,
        event_manager_id=TEST_EVENT_MANAGER_ID,
        signal_id=None,
        order_type="limit",
        order_category="spot",
        order_side="buy",
        order_status="pending",
        base_currency="BTC",
        quote_currency="USDT",
        initial_quantity=1.5,
        target_price=45000,
        symbol="BTCUSDT"
    )

    # Retrieve the order from the database
    order = get_order_by_id(order_id)

    # Validate the order data
    assert order, "Order not found!"
    order = order[0]  # Since result is a list of dicts, take the first result
    assert order["order_id"] == order_id, "Order ID does not match!"
    assert order["order_status"] == "pending", "Order status does not match!"
    assert order["base_currency"] == "BTC", "Base currency does not match!"
    assert order["quote_currency"] == "USDT", "Quote currency does not match!"
