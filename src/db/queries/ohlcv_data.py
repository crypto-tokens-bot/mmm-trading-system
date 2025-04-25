from datetime import datetime, UTC

import pandas as pd

from src.config.logger_config import logger
from src.db.db_connection import execute_query, get_db_client


def add_ohlcv_data(csv_path: str, symbol: str, timeframe: str):
    try:
        df = pd.read_csv(csv_path)

        required_cols = ['timestamp', 'open', 'high', 'low', 'close', 'volume']
        if not all(col in df.columns for col in required_cols):
            raise ValueError(f'CSV missing required columns: {required_cols}')

        df['time'] = pd.to_datetime(df['timestamp'])
        df['symbol'] = symbol
        df['timeframe'] = timeframe
        df['updated_at'] = datetime.now(UTC)

        rows = df[['symbol', 'timeframe', 'time', 'open', 'high', 'low', 'close', 'volume', 'updated_at']].itertuples(index=False, name=None)

        get_db_client().insert(
            table='ohlcv_data',
            data=list(rows)
        )
        logger.debug(f"Inserted {len(df)} rows into ohlcv_data for {symbol} {timeframe}")
    except Exception as e:
        logger.error(f"Failed to insert OHLCV data: {e}")