import threading
import time
from pathlib import Path
from src.config.logger_config import logger
import os

from typing import Dict, List, Tuple

from src.connectors.exchange_connector import ExchangeConnector


class MarketDataProvider(threading.Thread):
    """
    Market Data Provider that automatically starts fetching market data,
    saves it to files, and notifies subscribed strategies.
    Implemented as a Singleton to ensure only one instance exists.
    """
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, exchange_connector: ExchangeConnector, data_directory: str = "market_data_test"):
        """
        Initializes and automatically starts the market data provider.

        :param exchange_connector: Instance of an exchange connector (required).
        :param data_directory: Directory where the data will be stored.
        """
        if self._initialized:
            return

        if exchange_connector is None:
            raise ValueError("Exchange connector must be provided")

        super().__init__()
        self.exchange_connector = exchange_connector
        self.data_directory = data_directory
        self.subscribers: Dict[Tuple[str, str], List] = {}
        self.pairs = set()
        self._running = True
        super().start()
        self._initialized = True

        logger.debug("MarketDataProvider initialized and started with data directory: {}", data_directory)

    def run(self):
        """Main data fetching loop."""
        logger.debug("Starting market data fetching loop")
        while self._running:
            try:
                for symbol, timeframe in self.pairs.copy():
                    if not self._running:
                        break
                    self.fetch_and_store_data(symbol, timeframe)
                time.sleep(5)
            except Exception as e:
                logger.error("Error in data fetching loop: {}", e)

    def stop(self):
        """Stops the market data provider."""
        try:
            self._running = False
            logger.info(f"MarketDataProvider is shutting down.")
        except Exception as e:
            logger.error(f"Error stopping MarketDataProvider: {e}")

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
            logger.debug("New subscription key created: {}", key)

        self.subscribers[key].append(strategy)
        self.pairs.add(key)  # Track the pair for automatic fetching
        logger.debug(f"Strategy subscribed to {symbol} {timeframe}")

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
            logger.debug("Strategy unsubscribed from {} {}", symbol, timeframe)

            if not self.subscribers[key]:  # If no more subscribers, remove the key
                del self.subscribers[key]
                self.pairs.discard(key)
                logger.info("No more subscribers for {} {}, removing from tracking", symbol, timeframe)

    def fetch_and_store_data(self, symbol: str, timeframe: str, limit: int = 1000):
        """
        Fetches historical OHLCV data, saves it as a CSV file, and notifies subscribed strategies.

        :param symbol: Trading pair symbol (e.g., "BTC/USDT").
        :param timeframe: Time interval (e.g., "1m", "1h", "1d").
        :param limit: Maximum number of candles to fetch (default: 100).
        """
        try:
            logger.debug("Fetching data for {} {} (limit: {})", symbol, timeframe, limit)
            df = self.exchange_connector.fetch_ohlcv(symbol, timeframe, limit=limit)

            file_path = Path(f"{self.data_directory}/{symbol.replace('/', '_')}_{timeframe}.csv")
            file_path.parent.mkdir(parents=True, exist_ok=True)

            temp_path = file_path.with_suffix(".tmp")
            df.to_csv(temp_path, index=False)
            os.replace(temp_path, file_path)

            logger.success("Data saved to {}", file_path)

            self.notify_subscribers(symbol, timeframe, str(file_path))

        except Exception as e:
            logger.error("Error fetching data for {} {}: {}", symbol, timeframe, e)

    def notify_subscribers(self, symbol: str, timeframe: str, file_path: str):
        """
        Notifies all subscribed strategies that new data is available.

        :param symbol: Trading pair symbol.
        :param timeframe: Time interval.
        :param file_path: Path to the saved data file.
        """
        key = (symbol, timeframe)
        if key in self.subscribers:
            logger.debug("Notifying {} subscribers about new data for {} {}",
                         len(self.subscribers[key]), symbol, timeframe)
            for strategy in self.subscribers[key]:
                try:
                    strategy.on_new_data(file_path)
                except Exception as e:
                    logger.error("Error notifying strategy about new data: {}", e)

    def __del__(self):
        """Ensures proper cleanup when the object is destroyed."""
        self.stop()
