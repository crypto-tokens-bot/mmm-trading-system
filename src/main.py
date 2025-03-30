import asyncio
import os
import sys
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
from src.portfolio import Portfolio
from src.strategy.abstract_strategy import AbstractStrategy
from src.strategy.random_strategy import RandomStrategy

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
        target_price=Decimal("30000"),
        order_status="pending",
        symbol="BTC/USDT",
        base_currency="BTC",
        quote_currency="USDT",
        initial_quantity=Decimal("0.0001")
    )

    event_manager.start()


async def create_fake_strategy():
    event_manager = EventManager.create_new(mode="live")
    event_manager.start()
    strategy = AbstractStrategy.create_strategy(RandomStrategy, event_manager.event_manager_id, "BTC/USDT", "Random", {})
    strategy.start()
    time.sleep(10)
    strategy.stop()
    event_manager.stop()

async def create_fake_portfolio():
    event_manager = EventManager.create_new(mode="live")
    event_manager.start()
    strategy = AbstractStrategy.create_strategy(RandomStrategy, event_manager.event_manager_id, "BTC/USDT", "Random", {})
    strategy.start()

    portfolio = Portfolio.create_portfolio(
        event_manager_id=event_manager.event_manager_id,
        risk_controller_id=str(uuid.uuid4()),
        portfolio_name="My Test Portfolio",
        managed_assets={"BTC": 0.5, "ETH": 2},
        currency="USDT",
        initial_balance=10000,
        exchange="bybit"
    )

    event_manager.subscribe_portfolio_to_strategy(portfolio, strategy.strategy_id)

    time.sleep(10)
    strategy.stop()
    event_manager.stop()


if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(create_fake_portfolio())
