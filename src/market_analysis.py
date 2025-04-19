import threading
import pandas as pd


class MarketAnalysis:
    """
    Thread‑safe, stateless helper class for computing common TA indicators
    from OHLCV data stored on disk.
    """

    _lock = threading.Lock()

    @staticmethod
    def _load_df(file_path: str) -> pd.DataFrame:
        """
        Load OHLCV data.

        :param file_path: Path to CSV/Parquet containing columns
                          open, high, low, close, volume.
        :return: DataFrame with the data.
        :raises FileNotFoundError: If file is missing.
        :raises ValueError: If columns are incomplete.
        """
        with MarketAnalysis._lock:
            if file_path.endswith(".parquet"):
                df = pd.read_parquet(file_path)
            else:
                df = pd.read_csv(file_path)

            need = {"open", "high", "low", "close", "volume"}
            if not need.issubset(df.columns):
                raise ValueError(f"Input must contain: {', '.join(sorted(need))}")
            return df

    @staticmethod
    def get_rsi(file_path: str, period: int = 14) -> pd.Series:
        """
        :param file_path: OHLCV file.
        :param period: Look‑back window.
        :return: RSI series.
        """
        with MarketAnalysis._lock:
            df = MarketAnalysis._load_df(file_path)
            delta = df["close"].diff()
            gain = delta.clip(lower=0)
            loss = -delta.clip(upper=0)
            rs = gain.rolling(period).mean() / loss.rolling(period).mean()
            return 100 - 100 / (1 + rs)

    @staticmethod
    def get_macd(
        file_path: str,
        fast_period: int = 12,
        slow_period: int = 26,
        signal_period: int = 9,
    ) -> tuple[pd.Series, pd.Series]:
        """
        :param file_path: OHLCV file.
        :param fast_period: Fast EMA span.
        :param slow_period: Slow EMA span.
        :param signal_period: Signal EMA span.
        :return: (MACD line, signal line).
        """
        with MarketAnalysis._lock:
            df = MarketAnalysis._load_df(file_path)
            fast = df["close"].ewm(span=fast_period, adjust=False).mean()
            slow = df["close"].ewm(span=slow_period, adjust=False).mean()
            macd = fast - slow
            signal = macd.ewm(span=signal_period, adjust=False).mean()
            return macd, signal

    @staticmethod
    def get_aroon(file_path: str, period: int = 25) -> tuple[pd.Series, pd.Series]:
        """
        :param file_path: OHLCV file.
        :param period: Look‑back window.
        :return: (Aroon‑Up, Aroon‑Down).
        """
        with MarketAnalysis._lock:
            df = MarketAnalysis._load_df(file_path)
            a_up = df["high"].rolling(period).apply(lambda x: x.argmax(), raw=True)
            a_dn = df["low"].rolling(period).apply(lambda x: x.argmin(), raw=True)
            scale = 100 / (period - 1)
            return a_up * scale, a_dn * scale

    @staticmethod
    def get_obv(file_path: str) -> pd.Series:
        """
        :param file_path: OHLCV file.
        :return: OBV series.
        """
        with MarketAnalysis._lock:
            df = MarketAnalysis._load_df(file_path)
            direction = df["close"].diff().gt(0).replace({True: 1, False: -1}).fillna(0)
            return (df["volume"] * direction).cumsum()

    @staticmethod
    def get_stochastic_oscillator(
        file_path: str, k_period: int = 14, d_period: int = 3
    ) -> tuple[pd.Series, pd.Series]:
        """
        :param file_path: OHLCV file.
        :param k_period: %K window.
        :param d_period: %D SMA window.
        :return: (%K, %D).
        """
        with MarketAnalysis._lock:
            df = MarketAnalysis._load_df(file_path)
            low = df["low"].rolling(k_period).min()
            high = df["high"].rolling(k_period).max()
            k = 100 * (df["close"] - low) / (high - low)
            d = k.rolling(d_period).mean()
            return k, d

    @staticmethod
    def get_sma(file_path: str, period: int = 30) -> pd.Series:
        """
        :param file_path: OHLCV file.
        :param period: Window size.
        :return: SMA series.
        """
        with MarketAnalysis._lock:
            df = MarketAnalysis._load_df(file_path)
            return df["close"].rolling(period).mean()

    @staticmethod
    def get_ema(file_path: str, period: int = 30) -> pd.Series:
        """
        :param file_path: OHLCV file.
        :param period: EMA span.
        :return: EMA series.
        """
        with MarketAnalysis._lock:
            df = MarketAnalysis._load_df(file_path)
            return df["close"].ewm(span=period, adjust=False).mean()

    @staticmethod
    def get_bollinger_bands(
        file_path: str, period: int = 20, std_dev: int = 2
    ) -> tuple[pd.Series, pd.Series, pd.Series]:
        """
        :param file_path: OHLCV file.
        :param period: SMA window.
        :param std_dev: Std‑dev multiplier.
        :return: (upper, middle, lower bands).
        """
        with MarketAnalysis._lock:
            df = MarketAnalysis._load_df(file_path)
            sma = df["close"].rolling(period).mean()
            rstd = df["close"].rolling(period).std()
            upper = sma + std_dev * rstd
            lower = sma - std_dev * rstd
            return upper, sma, lower

    @staticmethod
    def get_momentum(file_path: str, period: int = 14) -> pd.Series:
        """
        :param file_path: OHLCV file.
        :param period: Look‑back difference.
        :return: Momentum series.
        """
        with MarketAnalysis._lock:
            df = MarketAnalysis._load_df(file_path)
            return df["close"].diff(period)
