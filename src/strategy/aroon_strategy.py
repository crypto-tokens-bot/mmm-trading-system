import asyncio
import os
from dotenv import load_dotenv
from datetime import datetime
from analysis.technical_analysis import TechnicalAnalysis
from decimal import *
from exchange.binance_exchange import BinanceExchange
from exchange.bybit_exchange import BybitExchange
from manager.order_manager import OrderManager
from strategy.base_strategy import BaseStrategy
import time

class AroonStrategy(BaseStrategy):
    def __init__(self, exchange, symbol, strategy_id, monitoring):
        super().__init__(exchange, symbol, strategy_id, monitoring)

    async def calculate_aroon(self):
        await self.technical_indicators.get_ohlcv(timeframe='5m', limit=int(self.info['settings']['limit']))
        up, down = self.technical_indicators.get_aroon()
        aroon_oscillator = up - down
        cross_pos = len(aroon_oscillator) - 1
        for i in range(len(aroon_oscillator) - 1, 0, -1):
            if aroon_oscillator.iloc[-1] > 0 and aroon_oscillator.iloc[i] > 0:
                cross_pos = i
            elif aroon_oscillator.iloc[-1] < 0 and aroon_oscillator.iloc[i] < 0:
                cross_pos = i
            else:
                break
        if cross_pos + self.info['settings']['filter_frames'] < self.info['settings']['limit']:
            if aroon_oscillator.iloc[-1] > 0:
                return 2
            elif aroon_oscillator.iloc[-1] < 0:
                return -2
        if aroon_oscillator.iloc[-1] > 0:
            return 1
        elif aroon_oscillator.iloc[-1] < 0:
            return -1
        return 0

    async def get_signal(self):
        result = await self.calculate_aroon()
        if self.info['openPositions'] and result == -2:
            return -1

        if not self.info['openPositions'] and result == 2:
            return 1

        return 0
