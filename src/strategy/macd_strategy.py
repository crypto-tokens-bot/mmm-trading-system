import asyncio
import os
from dotenv import load_dotenv
from datetime import datetime
import time

from src.strategy.base_strategy import BaseStrategy


class MACDStrategy(BaseStrategy):
    def __init__(self, exchange, symbol, strategy_id, monitoring):
        super().__init__(exchange, symbol, strategy_id, monitoring)

    async def calculate_moving_averages(self):
        await self.technical_indicators.get_ohlcv(limit=int(self.info['settings']['limit']))
        macd, signal = self.technical_indicators.get_macd()
        cross_upward = cross_downward = False
        cross_pos = -1
        for i in range(len(macd) - 1, 0, -1):
            cross_pos = i
            if signal[i] < macd[i] and macd[i - 1] <= signal[i - 1]:
                cross_upward = True
                break
            elif macd[i] < signal[i] and macd[i - 1] >= signal[i - 1]:
                cross_downward = True
                break
        if cross_downward:
            if cross_pos + self.info['settings']['filter_days'] < self.info['settings']['limit']:
                return -2
            return -1
        if cross_upward:
            if cross_pos + self.info['settings']['filter_days'] < self.info['settings']['limit']:
                return 2
            else:
                return 1
        return 0

    async def get_signal(self):
        result = await self.calculate_moving_averages()

        if self.info['openPositions']:
            return -1

        if not self.info['openPositions']:
            return 1

        if self.info['openPositions'] and result < 0:
            return -1

        if not self.info['openPositions'] and result == 2:
            return 1

        return 0