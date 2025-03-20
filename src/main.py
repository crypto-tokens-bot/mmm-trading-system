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
    event_manager.start()
    time.sleep(4)
    event_manager.stop()

if __name__ == "__main__":
    asyncio.run(create_fake_orders())
