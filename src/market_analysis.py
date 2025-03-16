import asyncio
import threading
import pandas as pd
import logging

# Setup logging configuration at the module level
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MarketAnalysis:
    """
    MarketAnalysis provides tools for loading and analyzing historical price data for cryptocurrency assets.
    It uses the ccxt library for interacting with various cryptocurrency exchanges.

    This class is implemented as a thread-safe Singleton.
    """

    _instance = None
    _instance_lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        """
        Implements the Singleton pattern in a thread-safe manner.

        :return: The single instance of MarketAnalysis.
        """
        with cls._instance_lock:
            if cls._instance is None:
                cls._instance = super(MarketAnalysis, cls).__new__(cls)
            return cls._instance

    def __init__(self, exchange, symbol):
        """
        Initializes an instance of MarketAnalysis.

        :param exchange: The exchange instance used for data retrieval.
        :param symbol: The trading pair symbol for which data will be fetched.
        """
        if hasattr(self, '_initialized') and self._initialized:
            return
        self.exchange = exchange
        self.symbol = symbol
        self.df = None
        self._lock = threading.Lock()
        self._initialized = True
        logger.info("MarketAnalysis instance created for symbol: %s", symbol)

    async def get_ohlcv(self, timeframe='1d', since=None, limit=None):
        """
        Retrieves historical OHLCV data for the specified trading pair and timeframe.

        :param timeframe: Timeframe for the data (e.g., '1d' for one day).
        :param since: Start timestamp in milliseconds for data retrieval. If None, retrieval starts from the earliest available date.
        :param limit: Maximum number of records to return. If None, the exchange's default is used.
        :return: A pandas DataFrame with columns 'timestamp', 'open', 'high', 'low', 'close', 'volume', where 'timestamp' is converted to datetime format.
        :raises Exception: If fetching or processing of data fails.
        """
        try:
            logger.info("Fetching OHLCV data for %s with timeframe %s", self.symbol, timeframe)
            ohlcv = await self.exchange.get_ohlcv(self.symbol, since, limit, timeframe)
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            with self._lock:
                self.df = df
            logger.info("OHLCV data fetched successfully for %s", self.symbol)
            return df
        except Exception as e:
            logger.exception("Error fetching OHLCV data: %s", e)
            raise

    def get_rsi(self, period=14):
        """
        Calculates the Relative Strength Index (RSI) for closing prices.

        :param period: The period over which to calculate the RSI.
        :return: A pandas Series containing the RSI values.
        :raises ValueError: If the DataFrame is not loaded.
        :raises Exception: For other calculation errors.
        """
        try:
            logger.info("Calculating RSI with period %d", period)
            with self._lock:
                if self.df is None:
                    raise ValueError("DataFrame is not loaded. Please call get_ohlcv first.")
                delta = self.df['close'].diff()
                avg_gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
                avg_loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
                rs = avg_gain / avg_loss
                rsi = 100 - (100 / (1 + rs))
            logger.info("RSI calculation completed")
            return rsi
        except Exception as e:
            logger.exception("Error calculating RSI: %s", e)
            raise

    def get_macd(self, fast_period=12, slow_period=26, signal_period=9):
        """
        Calculates the Moving Average Convergence Divergence (MACD).

        :param fast_period: The period for the fast EMA.
        :param slow_period: The period for the slow EMA.
        :param signal_period: The period for the signal line.
        :return: A tuple of two pandas Series: (MACD line, signal line).
        :raises ValueError: If the DataFrame is not loaded.
        :raises Exception: For other calculation errors.
        """
        try:
            logger.info("Calculating MACD with fast_period=%d, slow_period=%d, signal_period=%d", fast_period,
                        slow_period, signal_period)
            with self._lock:
                if self.df is None:
                    raise ValueError("DataFrame is not loaded. Please call get_ohlcv first.")
                exp1 = self.df['close'].ewm(span=fast_period, adjust=False).mean()
                exp2 = self.df['close'].ewm(span=slow_period, adjust=False).mean()
                macd = exp1 - exp2
                signal = macd.ewm(span=signal_period, adjust=False).mean()
            logger.info("MACD calculation completed")
            return macd, signal
        except Exception as e:
            logger.exception("Error calculating MACD: %s", e)
            raise

    def get_aroon(self, period=25):
        """
        Calculates the Aroon Up and Aroon Down indicators.

        :param period: The period over which to calculate the Aroon indicators.
        :return: A tuple of two pandas Series: (Aroon Up, Aroon Down).
        :raises ValueError: If the DataFrame is not loaded.
        :raises Exception: For other calculation errors.
        """
        try:
            logger.info("Calculating Aroon indicators with period %d", period)
            with self._lock:
                if self.df is None:
                    raise ValueError("DataFrame is not loaded. Please call get_ohlcv first.")
                aroon_up = self.df['high'].rolling(window=period).apply(lambda x: x.argmax(), raw=True) / (
                            period - 1) * 100
                aroon_down = self.df['low'].rolling(window=period).apply(lambda x: x.argmin(), raw=True) / (
                            period - 1) * 100
            logger.info("Aroon indicators calculation completed")
            return aroon_up, aroon_down
        except Exception as e:
            logger.exception("Error calculating Aroon indicators: %s", e)
            raise

    def get_obv(self):
        """
        Calculates the On-Balance Volume (OBV) indicator.

        :return: A pandas Series with the OBV values.
        :raises ValueError: If the DataFrame is not loaded.
        :raises Exception: For other calculation errors.
        """
        try:
            logger.info("Calculating OBV")
            with self._lock:
                if self.df is None:
                    raise ValueError("DataFrame is not loaded. Please call get_ohlcv first.")
                obv = (self.df['volume'] * (~self.df['close'].diff().le(0) * 2 - 1)).cumsum()
            logger.info("OBV calculation completed")
            return obv
        except Exception as e:
            logger.exception("Error calculating OBV: %s", e)
            raise

    def get_stochastic_oscillator(self, k_period=14, d_period=3):
        """
        Calculates the Stochastic Oscillator, including %K and %D lines.

        :param k_period: The period for calculating %K.
        :param d_period: The period for calculating %D (moving average of %K).
        :return: A tuple of two pandas Series: (%K line, %D line).
        :raises ValueError: If the DataFrame is not loaded.
        :raises Exception: For other calculation errors.
        """
        try:
            logger.info("Calculating Stochastic Oscillator with k_period=%d and d_period=%d", k_period, d_period)
            with self._lock:
                if self.df is None:
                    raise ValueError("DataFrame is not loaded. Please call get_ohlcv first.")
                low = self.df['low'].rolling(window=k_period).min()
                high = self.df['high'].rolling(window=k_period).max()
                k_line = 100 * ((self.df['close'] - low) / (high - low))
                d_line = k_line.rolling(window=d_period).mean()
            logger.info("Stochastic Oscillator calculation completed")
            return k_line, d_line
        except Exception as e:
            logger.exception("Error calculating Stochastic Oscillator: %s", e)
            raise

    def get_sma(self, period=30):
        """
        Calculates the Simple Moving Average (SMA) based on closing prices.

        :param period: The period for the SMA calculation.
        :return: A pandas Series with the SMA values.
        :raises ValueError: If the DataFrame is not loaded.
        :raises Exception: For other calculation errors.
        """
        try:
            logger.info("Calculating SMA with period %d", period)
            with self._lock:
                if self.df is None:
                    raise ValueError("DataFrame is not loaded. Please call get_ohlcv first.")
                sma = self.df['close'].rolling(window=period).mean()
            logger.info("SMA calculation completed")
            return sma
        except Exception as e:
            logger.exception("Error calculating SMA: %s", e)
            raise

    def get_ema(self, period=30):
        """
        Calculates the Exponential Moving Average (EMA) based on closing prices.

        :param period: The period for the EMA calculation.
        :return: A pandas Series with the EMA values.
        :raises ValueError: If the DataFrame is not loaded.
        :raises Exception: For other calculation errors.
        """
        try:
            logger.info("Calculating EMA with period %d", period)
            with self._lock:
                if self.df is None:
                    raise ValueError("DataFrame is not loaded. Please call get_ohlcv first.")
                ema = self.df['close'].ewm(span=period, adjust=False).mean()
            logger.info("EMA calculation completed")
            return ema
        except Exception as e:
            logger.exception("Error calculating EMA: %s", e)
            raise

    def get_bollinger_bands(self, period=20, std_dev=2):
        """
        Calculates Bollinger Bands.

        :param period: The period for calculating the SMA underlying the Bollinger Bands.
        :param std_dev: The number of standard deviations for the upper and lower bands.
        :return: A tuple of three pandas Series: (upper band, middle band [SMA], lower band).
        :raises ValueError: If the DataFrame is not loaded.
        :raises Exception: For other calculation errors.
        """
        try:
            logger.info("Calculating Bollinger Bands with period %d and std_dev %d", period, std_dev)
            with self._lock:
                if self.df is None:
                    raise ValueError("DataFrame is not loaded. Please call get_ohlcv first.")
                sma = self.df['close'].rolling(window=period).mean()
                rstd = self.df['close'].rolling(window=period).std()
                upper_band = sma + std_dev * rstd
                lower_band = sma - std_dev * rstd
            logger.info("Bollinger Bands calculation completed")
            return upper_band, sma, lower_band
        except Exception as e:
            logger.exception("Error calculating Bollinger Bands: %s", e)
            raise

    def get_momentum(self, period=14):
        """
        Calculates the Momentum indicator based on closing prices.

        :param period: The period for the momentum calculation.
        :return: A pandas Series with the momentum values.
        :raises ValueError: If the DataFrame is not loaded.
        :raises Exception: For other calculation errors.
        """
        try:
            logger.info("Calculating Momentum with period %d", period)
            with self._lock:
                if self.df is None:
                    raise ValueError("DataFrame is not loaded. Please call get_ohlcv first.")
                momentum = self.df['close'].diff(period)
            logger.info("Momentum calculation completed")
            return momentum
        except Exception as e:
            logger.exception("Error calculating Momentum: %s", e)
            raise
