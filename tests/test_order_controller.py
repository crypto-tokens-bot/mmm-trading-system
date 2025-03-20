import json
import uuid
from decimal import Decimal

import pytest

from src.order_processing.order_controller import OrderController
from src.event_manager import EventManager  # Using your real EventManager from event_manager.py
from src.db.db_connection import execute_query


def test_create_simple_order():
    """
    Test the creation of a simple (main) order without stop-loss or take-profit.
    Verifies that exactly one new order and one new event are added to the database.
    """
    # 1. Capture the current state of the orders and events tables.
    existing_orders = execute_query("SELECT * FROM orders ORDER BY created_at")
    existing_events = execute_query("SELECT * FROM events ORDER BY created_at")
    old_orders_count = len(existing_orders)
    old_events_count = len(existing_events)

    # 2. Create a new EventManager using its create_new() method.
    my_event_manager = EventManager.create_new("live")

    # 3. Create a main order.
    created_ids = OrderController().create_order(
        portfolio_id=str(uuid.uuid4()),
        event_manager_id=my_event_manager.event_manager_id,
        signal_id=str(uuid.uuid4()),
        order_type="limit",
        order_category="spot",
        order_side="buy",
        target_price=Decimal("50000"),
        order_status="pending",
        symbol="BTCUSD",
        base_currency="BTC",
        quote_currency="USD",
        initial_quantity=Decimal("1"),
        event_manager=my_event_manager
    )

    assert len(created_ids) == 1, "Expected exactly one created order ID."

    new_orders = execute_query("SELECT * FROM orders ORDER BY created_at")
    new_events = execute_query("SELECT * FROM events ORDER BY created_at")

    assert len(new_orders) == old_orders_count + 1, "Exactly one new order should be present."
    assert len(new_events) == old_events_count + 1, "Exactly one new event should be present."

    inserted_order = new_orders[-1]
    inserted_event = new_events[-1]

    assert str(inserted_order["order_id"]) == created_ids[0], "The order_id in the DB does not match the returned ID."
    assert inserted_order["parent_order_id"] is None, "A main order should not have a parent_order_id."

    payload_str = inserted_event["payload"]
    payload_data = json.loads(payload_str)
    assert payload_data["order_id"] == created_ids[0], "The event payload should contain the newly created order ID."


def test_create_order_with_stop_loss_and_take_profit():
    """
    Test the creation of an order with both stop-loss and take-profit.
    Verifies that exactly three new orders (main, stop-loss, take-profit) and three new events
    are added to the database, and that the stop-loss and take-profit orders reference the main order
    via parent_order_id.
    """
    existing_orders = execute_query("SELECT * FROM orders ORDER BY created_at")
    existing_events = execute_query("SELECT * FROM events ORDER BY created_at")
    old_orders_count = len(existing_orders)
    old_events_count = len(existing_events)

    my_event_manager = EventManager.create_new("live")

    controller = OrderController()
    created_ids = controller.create_order(
        portfolio_id=str(uuid.uuid4()),
        event_manager_id=my_event_manager.event_manager_id,
        signal_id=str(uuid.uuid4()),
        order_type="market",
        order_category="spot",
        order_side="buy",
        target_price=Decimal("50000"),
        order_status="pending",
        symbol="BTCUSDT",
        base_currency="BTC",
        quote_currency="USDT",
        initial_quantity=Decimal("0.001"),
        event_manager=my_event_manager,
        stop_loss=Decimal("48000"),
        take_profit=Decimal("52000")
    )

    assert len(created_ids) == 3, "Expected exactly three created order IDs (main, SL, TP)."

    new_orders = execute_query("SELECT * FROM orders ORDER BY created_at")
    new_events = execute_query("SELECT * FROM events ORDER BY created_at")

    assert len(new_orders) == old_orders_count + 3, "Expected three new orders in the database."
    assert len(new_events) == old_events_count + 3, "Expected three new events in the database."

    inserted_orders = new_orders[-3:]

    main_order = next(o for o in inserted_orders if o["order_type"] not in ("stop_loss", "take_profit"))
    stop_loss_order = next(o for o in inserted_orders if o["order_type"] == "stop_loss")
    take_profit_order = next(o for o in inserted_orders if o["order_type"] == "take_profit")

    assert main_order["parent_order_id"] is None, "Main order should not have a parent_order_id."

    assert stop_loss_order["parent_order_id"] == main_order["order_id"], "Stop-loss order must reference the main order."
    assert take_profit_order["parent_order_id"] == main_order["order_id"], "Take-profit order must reference the main order."

    db_ids = {str(main_order["order_id"]), str(stop_loss_order["order_id"]), str(take_profit_order["order_id"])}
    assert set(created_ids) == db_ids, "The set of IDs returned does not match the IDs in the database."

    inserted_events = new_events[-3:]
    for evt in inserted_events:
        payload_str = evt["payload"]
        payload_data = json.loads(payload_str)
        assert payload_data["order_id"] in db_ids, "Each event payload should reference one of the created order IDs."
