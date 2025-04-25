import random
from typing import Dict, Any, Optional

from src.config.logger_config import logger
from src.market_data.market_analysis import MarketAnalysis
from src.strategy.abstract_strategy import AbstractStrategy


class RandomStrategy(AbstractStrategy):
    """
    Simple strategy that randomly generates BUY and SELL signals.
    """

    def __init__(
            self,
            strategy_id: str,
            event_manager_id: str,
            trading_pair: str,
            strategy_name: str,
            parameters: Dict[str, Any] | None = None,
    ):
        """
        :param strategy_id: Unique strategy UUID.
        :param event_manager_id: UUID of the owning event manager.
        :param trading_pair: Symbol to trade, e.g. 'BTC/USDT'.
        :param parameters: Optional custom settings (unused here).
        """
        super().__init__(
            strategy_id=strategy_id,
            event_manager_id=event_manager_id,
            trading_pair=trading_pair,
            strategy_name=strategy_name,
            parameters=parameters or {},
        )

        self.last_time = None
        self.file_path: Optional[str] = None
        self.sma = None

        logger.info(f"Strategy {self.strategy_name} initialized for {self.trading_pair}")

    def on_new_data(self, file_path: str):
        logger.debug(f"Strategy {self.strategy_name} got new data on {file_path}")
        self.file_path = file_path
        self.sma = MarketAnalysis.get_sma(self.file_path)
        self.target_price = MarketAnalysis.get_target_price(self.file_path)
        self.last_time = MarketAnalysis.get_last_time(self.file_path)
        self.check_entry_signal()
        self.check_exit_signal()

    def check_entry_signal(self):
        """
        Generate a BUY signal with 50% probability.
        """
        if random.random() < 0.1:
            self._generate_signal_event("buy", self.last_time)

    def check_exit_signal(self):
        """
        Generate a SELL signal with 50% probability.
        """
        if random.random() < 0.1:
            self._generate_signal_event("sell", self.last_time)