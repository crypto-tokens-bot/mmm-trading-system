import asyncio
import os
import time
import uuid
import logging
from decimal import Decimal

from loguru import logger

from src.connectors.bybit_connector import BybitAsyncConnector
from src.event_manager import EventManager
from src.order_processing.live_order_executor import LiveOrderExecutor
from src.order_processing.order_controller import OrderController
from src.order_processing.order_executor import OrderExecutor

# Configure logger to write logs into logs folder
logger.add(f"../logs/testing.log", level="INFO")

async def create_fake_orders():
    event_manager = EventManager.create_new(mode="live")

    created_ids = event_manager._order_controller.create_order(
        portfolio_id=str(uuid.uuid4()),
        event_manager_id=event_manager.event_manager_id,
        signal_id=str(uuid.uuid4()),
        order_type="market",
        order_category="spot",
        order_side="buy",
        target_price=Decimal("50000"),
        order_status="pending",
        symbol="BTCUSD",
        base_currency="BTC",
        quote_currency="USD",
        initial_quantity=Decimal("0.0001"),
        event_manager=event_manager
    )

    event_manager.start()


if __name__ == "__main__":
    asyncio.run(create_fake_orders())
