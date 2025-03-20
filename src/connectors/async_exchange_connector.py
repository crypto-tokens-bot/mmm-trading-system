import asyncio
import json

import ccxt.async_support as ccxt
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any
from loguru import logger

import pandas as pd

from src.db.queries.orders import get_order_by_id

# Configure logger to write logs into logs folder
logger.add(f"../../logs/testing.log", level="INFO")

class AsyncExchangeConnector(ABC):
    """
    Abstract asynchronous class for connecting to cryptocurrency exchanges via ccxt.
    The constructor initializes an instance of ccxt.{exchange_id} in async mode.
    """

    def __init__(
        self,
        exchange,
        api_key: str = None,
        api_secret: str = None,
        testnet: bool = False
    ):
        """
        Initializes the exchange connector with API credentials and optional sandbox mode.

        :param exchange: Exchange object from ccxt.
        :param api_key: API key for authentication.
        :param api_secret: API secret for authentication.
        :param testnet: If True, enables sandbox mode (if supported by the exchange).
        """
        config = {
            'apiKey': api_key,
            'secret': api_secret,
            'enableRateLimit': True
        }
        self._exchange = exchange(config)
        if testnet:
            self._exchange.set_sandbox_mode(True)

    def get_order_book(self, symbol, limit=None):
        return self._exchange.fetch_order_book(symbol, limit)

    async def fetch_ohlcv(
        self,
        symbol: str,
        timeframe: str,
        start_time: datetime | int | None = None,
        end_time: datetime | int | None = None,
        limit: int = 100,
        **kwargs
    ) -> Any:
        """
        Fetches historical OHLCV (Open, High, Low, Close, Volume) candle data from the exchange.

        :param symbol: Trading pair symbol (e.g., "BTC/USDT").
        :param timeframe: Time interval (e.g., "1m", "1h", "1d").
        :param start_time: Start timestamp (datetime or milliseconds) for fetching data.
        :param end_time: End timestamp (datetime or milliseconds) to filter results.
        :param limit: Maximum number of candles to fetch (default: 100).
        :param kwargs: Additional parameters for the exchange API.
        :return: Pandas DataFrame containing OHLCV data.
        """
        since = None
        # if start_time is not None:
        #     since = self._to_millis(start_time)

        ohlcv = await self._exchange.fetch_ohlcv(
            symbol=symbol,
            timeframe=timeframe,
            since=since,
            limit=limit,
            params=kwargs
        )

        # if end_time is not None:
        #     end_ms = self._to_millis(end_time)
        #     ohlcv = [c for c in ohlcv if c[0] <= end_ms]

        ohlcv_df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        ohlcv_df['timestamp'] = pd.to_datetime(ohlcv_df['timestamp'], unit='ms')

        return ohlcv_df

    async def create_order(self, coin, order_type, side, amount, price=None, params={}):
        """
        Places an order on the exchange via CCXT.
        If a price is provided, it is used (e.g., for limit orders); otherwise, the order is sent without a price (e.g., for market orders).

        :param coin: The trading symbol (e.g., "BTC/USDT").
        :param order_type: The type of the order (e.g., "limit" or "market").
        :param side: The order side ("buy" or "sell").
        :param amount: The quantity to order.
        :param price: (Optional) The price at which to order.
        :param params: (Optional) Additional parameters for the exchange.
        :return: The order object returned by the exchange.
        """
        if price is not None:
            result = await self._exchange.create_order(coin, order_type, side, amount, price, params=params)
        else:
            result = await self._exchange.create_order(coin, order_type, side, amount, params=params)
        return result

    async def create_spot_order(self, order_id):
        """
        Retrieves order details from the database using the provided order_id, places a market buy order via CCXT,
        waits for the exchange to process the order, and then updates the order status in the database to "executing".

        :param order_id: The unique identifier of the order record in the database.
        :return: The order object returned by the exchange.
        :raises Exception: If no closed order is found after placing the market buy order.
        """
        try:
            # Retrieve order details from the database.
            order_details = get_order_by_id(order_id)[0]

            response_data = await self.create_order(order_details['symbol'], order_details['order_type'], order_details['order_side'], order_details['initial_quantity'])
            print(response_data)
            print(response_data['info']['orderId'])
            await asyncio.sleep(3)
            print(await self._exchange.fetchOpenOrder(response_data['info']['orderId']))
            await asyncio.sleep(1)
            closed_orders = await self._exchange.fetch_canceled_orders(order_details['symbol'])
            print(closed_orders)
            sorted_by_timestamp = self._exchange.sort_by(closed_orders, 'timestamp', True)
            order = sorted_by_timestamp[0]
            if order is not None:
                # update_order_status(order_id, "executing")
                return order
            else:
                raise Exception("No closed orders found.")
        except Exception as e:
            logger.error(f"Failed to create market buy order for order_id {order_id}: {e}")
            raise


    async def create_market_stop_loss_order(self, order_id):
        """
        Retrieves order details from the database using the provided order_id, places a market stop-loss order via CCXT,
        waits for the exchange to process the order, and then updates the order status in the database to "executing".

        :param order_id: The unique identifier of the order record in the database.
        :return: The order object returned by the exchange.
        :raises Exception: If no open order is found after placing the market stop-loss order.
        """
        try:
            order_details = await get_order_by_id(order_id)
            coin = order_details.get("coin")
            order_size = order_details.get("amount")
            params = order_details.get("params", {})

            response_data = await self.create_order(coin, 'market', 'sell', order_size, params=params)
            await asyncio.sleep(1)
            open_orders = await self._exchange.fetch_open_orders(coin)
            sorted_by_timestamp = self._exchange.sort_by(open_orders, 'timestamp', True)
            order = sorted_by_timestamp[0]
            if order is not None:
                await self.update_order_status(order_id, "executing")
                return order
            else:
                raise Exception("No open orders found.")
        except Exception as e:
            logger.error(f"Failed to create market stop loss order for order_id {order_id}: {e}")
            raise

    async def create_market_take_profit_order(self, order_id):
        """
        Retrieves order details from the database using the provided order_id, places a market take-profit order via CCXT,
        waits for the exchange to process the order, and then updates the order status in the database to "executing".

        :param order_id: The unique identifier of the order record in the database.
        :return: The order object returned by the exchange.
        :raises Exception: If no closed order is found after placing the market take-profit order.
        """
        try:
            order_details = await get_order_by_id(order_id)
            coin = order_details.get("coin")
            order_size = order_details.get("amount")
            params = order_details.get("params", {})

            # For take-profit orders, assume execution as a market sell.
            response_data = await self.create_order(coin, 'market', 'sell', order_size, params=params)
            await asyncio.sleep(1)
            closed_orders = await self._exchange.fetch_closed_orders(coin)
            sorted_by_timestamp = self._exchange.sort_by(closed_orders, 'timestamp', True)
            order = sorted_by_timestamp[0]
            if order is not None:
                await self.update_order_status(order_id, "executing")
                return order
            else:
                raise Exception("No closed orders found for take profit order.")
        except Exception as e:
            logger.error(f"Failed to create market take profit order for order_id {order_id}: {e}")
            raise

    async def close(self):
        """
        Closes the asynchronous connection to the exchange.
        This method should be called to properly clean up resources when the connector is no longer needed.
        """
        await self._exchange.close()

    # def __del__(self):
    #     logger.info("before")
    #     print("before close")
    #     asyncio.run(self.close())
    #     print("after close")
