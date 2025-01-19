from abc import ABC, abstractmethod
from typing import Any
from datetime import datetime


class AsyncExchangeConnector(ABC):
    """
    Абстрактный асинхронный класс для подключения к криптобиржам (через ccxt или иные библиотеки).

    Определяет базовые методы:
      - fetch_instruments: получить список торговых инструментов (markets)
      - fetch_ohlcv: получить исторические свечи (OHLCV)
    """

    @abstractmethod
    async def fetch_instruments(self, **kwargs) -> Any:
        """
        Получить список доступных инструментов (пар) с биржи.

        :param kwargs: Доп. параметры, специфичные для конкретной биржи (если есть).
        :return: Данные о маркетах (list или dict).
        """
        pass

    @abstractmethod
    async def fetch_ohlcv(
        self,
        symbol: str,
        timeframe: str,
        start_time: datetime | int | None = None,
        end_time: datetime | int | None = None,
        limit: int = 100,
        **kwargs
    ) -> Any:
        """
        Получить исторические свечи (OHLCV).

        :param symbol: Торговая пара (например, 'BTC/USDT').
        :param timeframe: Интервал свечи (например, '1m', '5m', '1h' и т.д.).
        :param start_time: Начало диапазона (datetime или Unix time); ccxt обычно использует 'since' (в мс).
        :param end_time: Конец диапазона (не все биржи/ccxt поддерживают end_time напрямую).
        :param limit: Максимальное количество свечей за раз.
        :param kwargs: Доп. параметры для конкретного API.
        :return: Список списков или иной формат с данными OHLCV.
        """
        pass
