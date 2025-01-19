import time
import ccxt.async_support as ccxt
from datetime import datetime
from base_connector import AsyncExchangeConnector


class BybitAsyncConnector(AsyncExchangeConnector):
    """
    Асинхронный коннектор к бирже Bybit с использованием ccxt.
    """

    def __init__(self, api_key: str = None, api_secret: str = None, testnet: bool = False):
        """
        :param api_key: API-ключ Bybit (может быть None для публичных эндпоинтов).
        :param api_secret: Секретный ключ Bybit (может быть None для публичных эндпоинтов).
        :param testnet: True, если нужно включить sandbox-режим (set_sandbox_mode).
        """
        # Параметры для инициализации ccxt.bybit
        config = {
            'apiKey': api_key,
            'secret': api_secret,
            'enableRateLimit': True
        }
        self._exchange = ccxt.bybit(config)

        # Включаем sandbox-режим, если нужно (Bybit Testnet)
        # Учтите, что ccxt.bybit в sandbox-моде работает только для некоторых эндпоинтов,
        # и реальные исторические данные на тестнете могут быть ограничены
        if testnet:
            self._exchange.set_sandbox_mode(True)

    async def fetch_instruments(self, **kwargs):
        """
        Загрузить список торговых инструментов (markets) с Bybit.

        ccxt делает это через load_markets(); при первом вызове сходит к API, потом кэширует.
        """
        markets = await self._exchange.load_markets(reload=True)
        return markets

    async def fetch_ohlcv(
        self,
        symbol: str,
        timeframe: str = '1h',
        start_time: datetime | int | None = None,
        end_time: datetime | int | None = None,
        limit: int = 100,
        **kwargs
    ):
        """
        Получить исторические свечи (OHLCV) для указанного symbol и timeframe.
        В ccxt стандартный метод: fetch_ohlcv(symbol, timeframe, since=..., limit=..., ...)
        """
        since = None
        if start_time is not None:
            since = self._to_millis(start_time)

        # ccxt не поддерживает 'end_time' напрямую во всех биржах.
        # Обычно нужно вызывать fetch_ohlcv несколькими партиями, если хотим полный диапазон.
        # Для упрощения возьмём только since + limit.

        ohlcv = await self._exchange.fetch_ohlcv(
            symbol=symbol,
            timeframe=timeframe,
            since=since,
            limit=limit,
            params=kwargs  # Доп.параметры, если нужны
        )

        # Если end_time нужен строго, придётся фильтровать результат вручную.
        if end_time is not None:
            end_ms = self._to_millis(end_time)
            # Фильтруем свечи, у которых timestamp <= end_ms
            ohlcv = [c for c in ohlcv if c[0] <= end_ms]

        return ohlcv

    async def close(self):
        """
        Закрыть соединение (ccxt.async_support требует явного закрытия сеанса).
        """
        await self._exchange.close()

    @staticmethod
    def _to_millis(t: datetime | int) -> int:
        """
        Преобразовать datetime или секунды Unix time в миллисекунды.
        """
        if isinstance(t, datetime):
            return int(t.timestamp() * 1000)
        elif isinstance(t, int):
            # Предположим, что число < 10^11 — это секунды
            return t * 1000 if t < 10**11 else t
        else:
            raise TypeError("start_time/end_time must be datetime or int")
