import time

from abc import ABC
from datetime import datetime
from multiprocessing.util import debug
from typing import Any

import ccxt
from clickhouse_connect.datatypes.numeric import Decimal

from src.config.logger_config import logger

import pandas as pd

from src.db.queries.orders import get_order_by_id, update_order_status, update_order_exchange_id


class ExchangeConnector(ABC):
    """
    Abstract class for connecting to cryptocurrency exchanges via ccxt.
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

    @staticmethod
    def get_exchange_connector(exchange_name, testnet=True):
        from src.connectors.bybit_connector import BybitConnector
        if exchange_name == 'bybit':
            return BybitConnector(testnet=testnet)

    def get_ticker(self, symbol):
        return self._exchange.fetch_ticker(symbol)

    def get_order_book(self, symbol, limit=None):
        return self._exchange.fetch_order_book(symbol, limit)

    def fetch_ohlcv_with_retry(self, symbol, timeframe, since=None, limit=100, max_retries=5, delay=1, **kwargs):
        attempt = 0
        while attempt < max_retries:
            try:
                data = exchange.fetch_ohlcv(
                    symbol=symbol,
                    timeframe=timeframe,
                    since=since,
                    limit=limit,
                    params=kwargs
                )
                if data:
                    return data
                else:
                    logger.warning(f"No data returned. Retry {attempt + 1}/{max_retries}")
            except Exception as e:
                logger.warning(f"Error fetching OHLCV: {e}. Retry {attempt + 1}/{max_retries}")
            attempt += 1
            time.sleep(delay)

        logger.error(f"Failed to fetch OHLCV after {max_retries} attempts.")
        return []

    def fetch_ohlcv(
            self,
            symbol: str,
            timeframe: str,
            start_time,
            end_time: datetime | int | None = None,
            limit: int = 100,
            max_retries=5,
            delay=1,
            **kwargs
    ) -> Any:
        """
        Fetches historical OHLCV (Open, High, Low, Close, Volume) candle data from the exchange.

        :param symbol: Trading pair symbol (e.g., "BTC/USDT").
        :param timeframe: Time interval (e.g., "1m", "1h", "1d").
        :param start_time: Start timestamp for fetching data.
        :param end_time: End timestamp (datetime or milliseconds) to filter results.
        :param limit: Maximum number of candles to fetch (default: 100).
        :param kwargs: Additional parameters for the exchange API.
        :return: Pandas DataFrame containing OHLCV data.
        """

        attempt = 1
        while attempt <= max_retries:
            try:
                ohlcv = self._exchange.fetch_ohlcv(
                    symbol=symbol,
                    timeframe=timeframe,
                    since=start_time,
                    limit=limit,
                    params=kwargs,
                )
                # if end_time is not None:
                #     end_ms = self._to_millis(end_time)
                #     ohlcv = [c for c in ohlcv if c[0] <= end_ms]
                debug(ohlcv)
                if ohlcv:
                    ohlcv_df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
                    ohlcv_df['timestamp'] = pd.to_datetime(ohlcv_df['timestamp'], unit='ms')
                    return ohlcv_df
                else:
                    logger.warning(f"No data returned. Retry {attempt}/{max_retries}")
            except Exception as e:
                logger.warning(f"Error fetching OHLCV: {e}. Retry {attempt}/{max_retries}")
            attempt += 1
            time.sleep(delay)

        logger.error(f"Failed to fetch OHLCV after {max_retries} attempts.")
        return []


    def create_order(self, coin, order_type, side, amount, price=None, params=None):
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
        if params is None:
            params = {}
        if price is not None:
            result = self._exchange.create_order(coin, order_type, side, amount, price, params=params)
        else:
            result = self._exchange.create_order(coin, order_type, side, amount, params=params)
        return result

    def get_order_info(
            self,
            order_exchange_id: str,
            symbol: str | None = None
    ):
        try:
            order = self._exchange.fetch_closed_order(
                id=order_exchange_id,
                symbol=symbol
            )
            return order
        except ccxt.OrderNotFound as e:
            pass

        try:
            order = self._exchange.fetch_open_order(
                id=order_exchange_id,
                symbol=symbol
            )
            return order
        except ccxt.OrderNotFound as e:
            pass

        orders = self._exchange.fetch_canceled_orders(
            symbol=symbol
        )
        for order in orders:
            if order['info']['orderId'] == order_exchange_id:
                return order

        return None

    def create_spot_order(self, order_id):
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
            result = self.create_order(order_details['symbol'], order_details['order_type'],
                                       order_details['order_side'], order_details['initial_quantity'])
            last_order = None
            while last_order is None:
                last_order = self.get_order_info(result['id'], result['symbol'])
                time.sleep(1)
            order_exchange_id = last_order['id']
            update_order_status(order_id, "executing")
            update_order_exchange_id(order_id, order_exchange_id)
            return order_id
        except Exception as e:
            logger.error(f"Failed to create spot order for order_id {order_id}: {e}")
            raise

    def create_conditional_order(self, order_id):
        """
        Retrieves order details from the database using the provided order_id, places a market stop-loss order via CCXT,
        waits for the exchange to process the order, and then updates the order status in the database to "executing".

        :param order_id: The unique identifier of the order record in the database.
        :return: The order object returned by the exchange.
        :raises Exception: If no open order is found after placing the market stop-loss order.
        """
        try:
            order_details = get_order_by_id(order_id)[0]
            result = self.create_order(order_details['symbol'], order_details['order_type'],
                                       order_details['order_side'], order_details['initial_quantity'],
                                       params={'triggerPrice': order_details['target_price'], 'reduceOnly': True})
            last_order = None
            while last_order is None:
                last_order = self.get_order_info(result['id'], result['symbol'])
                time.sleep(1)
            order_exchange_id = last_order['id']
            update_order_status(order_id, "untriggered")
            update_order_exchange_id(order_id, order_exchange_id)
            return order_id
        except Exception as e:
            logger.error(f"Failed to create conditional order for order_id {order_id}: {e}")
            raise