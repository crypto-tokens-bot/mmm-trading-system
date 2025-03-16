import json

import ccxt.async_support as ccxt
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any

import pandas as pd


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

    async def close(self):
        """
        Closes the asynchronous connection to the exchange.
        This method should be called to properly clean up resources when the connector is no longer needed.
        """
        await self._exchange.close()
