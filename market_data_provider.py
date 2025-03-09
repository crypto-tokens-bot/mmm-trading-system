import asyncio
import pandas as pd
from datetime import datetime
from typing import Dict, List, Tuple
from connectors.async_exchange_connector import AsyncExchangeConnector


class MarketDataProvider:
    """
    Market Data Provider that fetches market data, saves it to a file, and notifies subscribed strategies.
    """

    def __init__(self, exchange_connector: AsyncExchangeConnector, data_directory: str = "data"):
        """
        Initializes the market data provider.

        :param exchange_connector: Instance of an async exchange connector.
        :param data_directory: Directory where the data will be stored.
        """
        self.exchange_connector = exchange_connector
        self.data_directory = data_directory
        self.subscribers: Dict[Tuple[str, str], List] = {}  # {(symbol, timeframe): [strategy1, strategy2]}
        self.pairs = set()  # Set of (symbol, timeframe) to track active data requests

    def subscribe(self, strategy, symbol: str, timeframe: str):
        """
        Allows strategies to subscribe to market data updates.

        :param strategy: The strategy instance subscribing to data updates.
        :param symbol: Trading pair symbol (e.g., "BTC/USDT").
        :param timeframe: Time interval (e.g., "1m", "1h", "1d").
        """
        key = (symbol, timeframe)
        if key not in self.subscribers:
            self.subscribers[key] = []
        self.subscribers[key].append(strategy)
        self.pairs.add(key)  # Track the pair for automatic fetching

    def unsubscribe(self, strategy, symbol: str, timeframe: str):
        """
        Allows strategies to unsubscribe from market data updates.

        :param strategy: The strategy instance unsubscribing from data updates.
        :param symbol: Trading pair symbol.
        :param timeframe: Time interval.
        """
        key = (symbol, timeframe)
        if key in self.subscribers:
            self.subscribers[key].remove(strategy)
            if not self.subscribers[key]:  # If no more subscribers, remove the key
                del self.subscribers[key]
                self.pairs.discard(key)

    async def run(self):
        """
        Continuously fetches market data for all subscribed pairs in a round-robin fashion.
        """
        while True:
            for symbol, timeframe in self.pairs.copy():  # Iterate through all active pairs
                await self.fetch_and_store_data(symbol, timeframe)
                await asyncio.sleep(1)  # Short delay between requests to avoid rate limits

    async def fetch_and_store_data(self, symbol: str, timeframe: str, limit: int = 100):
        """
        Fetches historical OHLCV data, saves it as a CSV file, and notifies subscribed strategies.

        :param symbol: Trading pair symbol (e.g., "BTC/USDT").
        :param timeframe: Time interval (e.g., "1m", "1h", "1d").
        :param limit: Maximum number of candles to fetch (default: 100).
        """
        try:
            df = await self.exchange_connector.fetch_ohlcv(symbol, timeframe, limit=limit)
            file_path = f"{self.data_directory}/{symbol.replace('/', '_')}_{timeframe}.csv"
            df.to_csv(file_path, index=False)
            print(f"📁 Data saved to {file_path}")

            # Notify subscribed strategies (fire-and-forget approach)
            self.notify_subscribers(symbol, timeframe, file_path)

        except Exception as e:
            print(f"❌ Error fetching data for {symbol} {timeframe}: {e}")

    def notify_subscribers(self, symbol: str, timeframe: str, file_path: str):
        """
        Notifies all subscribed strategies that new data is available.

        :param symbol: Trading pair symbol.
        :param timeframe: Time interval.
        :param file_path: Path to the saved data file.
        """
        key = (symbol, timeframe)
        if key in self.subscribers:
            for strategy in self.subscribers[key]:
                asyncio.create_task(strategy.on_new_data(file_path))  # Fire-and-forget
