import ccxt
import pandas as pd
from datetime import timedelta
from loguru import logger

from src.connectors.exchange_connector import ExchangeConnector


class HistoricalDataFeed:
    """
    HistoricalDataFeed simulates real-time market data using historical OHLCV data
    from a cryptocurrency exchange via the ccxt library.

    :param exchange_name: Name of the exchange (e.g., 'binance').
    :param symbol: Trading pair symbol (e.g., 'BTC/USDT').
    :param timeframe: Timeframe for OHLCV data (e.g., '1m').
    :param start_date: Start date for historical data fetching.
    :param step: Time increment to move forward after each fetch.
    """

    def __init__(self, exchange_name, symbol, timeframe='1m', start_date='2024-01-01', step=timedelta(minutes=1)):
        self.exchange = ExchangeConnector.get_exchange_connector(exchange_name, testnet=False)
        self.symbol = symbol
        self.timeframe = timeframe
        self.current_time = pd.Timestamp(start_date)
        self.step = step

    def fetch_ohlcv(self, limit=100):
        """
        Fetch the next chunk of historical OHLCV data and advance the internal clock.

        :param limit: Number of OHLCV entries to fetch.
        :return: DataFrame containing OHLCV data.
        """
        since = int(self.current_time.timestamp() * 1000)

        try:
            ohlcv = self.exchange.fetch_ohlcv(
                self.symbol,
                timeframe=self.timeframe,
                start_time=since,
                limit=limit
            )


            df = pd.DataFrame(
                ohlcv,
                columns=['timestamp', 'open', 'high', 'low', 'close', 'volume']
            )
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')

            if not df.empty:
                self.current_time = df['timestamp'].iloc[-1] + self.step
            else:
                logger.warning("Received empty OHLCV data.")
                return None

            return df

        except Exception as e:
            logger.error(f"Failed to load historical data: {e}")
            return pd.DataFrame()