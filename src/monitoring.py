import pandas as pd
import mplfinance as mpf
import os

from src.config.logger_config import logger


class Monitoring:
    def __init__(self, size=(12, 6)):
        self.size = size
        self.ohlc_cols = ['open', 'high', 'low', 'close']
        self.ohlcv_cols = ['open', 'high', 'low', 'close', 'volume']

    def _get_data(self, data_input, needed_cols):
        data = pd.read_csv(data_input)
        data['time'] = pd.to_datetime(data['timestamp'])
        data.set_index('time', inplace=True)

        return data[needed_cols]

    def ohlcv_plot(self, data, type='candle', title='Price Chart', volume=True):
        df = self._get_data(data, self.ohlcv_cols if volume else self.ohlc_cols)
        mpf.plot(df, type=type, style='binance', title=title,
                 volume=volume, figsize=self.size,
                 savefig=data+'.png')