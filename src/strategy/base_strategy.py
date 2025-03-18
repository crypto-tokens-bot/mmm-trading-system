from abc import ABC, abstractmethod
import asyncio
from decimal import *

class BaseStrategy(ABC):

    def __init__(self, exchange, symbol, strategy_id, monitoring):
        self.exchange = exchange
        self.symbol = symbol
        # Экземпляр для получения технических индикаторов заданного токена.
        self.technical_indicators = TechnicalAnalysis(exchange, symbol)
        # strategy_id для связи в clickhouse.
        self.strategy_id = strategy_id
        # Класс мониторинга для добавления в clickhouse.
        self.monitoring = monitoring
        self.info = None

    def update_info(self):
        self.info = self.monitoring.get_strategy_info(self.strategy_id)

    @abstractmethod
    def get_signal(self):
        pass

    async def trading(self):
        while True:
            self.update_info()
            if not self.info['status']:
                break
            await OrderManager.check_loss_order(self.strategy_id, self.monitoring, self.exchange, self.symbol,
                                                Decimal(self.info['balance']))
            try:
                signal = await self.get_signal()
                print(self.info['name'] + ":\nSignal: " + str(signal))
                if signal == 1:
                    await OrderManager.place_buy_order(strategy_id=self.strategy_id, monitoring=self.monitoring,
                                                       exchange=self.exchange,
                                                       token_symbol=self.symbol,
                                                       balance=Decimal(self.info['balance']),
                                                       stop_loss=Decimal(self.info['settings']['loss_coef']))
                    print('Buy\n----------------------')
                elif signal == -1:
                    await OrderManager.place_sell_order(
                        strategy_id=self.strategy_id, monitoring=self.monitoring,
                        exchange=self.exchange,
                        token_symbol=self.symbol,
                        balance=Decimal(self.info['balance']),
                        order_size=self.info['assetsNumber'])
                    print('Sell\n----------------------')
                else:
                    print('Hold')
            except Exception as err:
                print(err)

            await asyncio.sleep(10)  # Пауза в 10 секунд

        await self.exchange.close()

    def stop_strategy(self):
        pass
