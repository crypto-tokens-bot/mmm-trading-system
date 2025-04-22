import threading
import time
from abc import ABC, abstractmethod
from decimal import Decimal
from typing import Dict, Any, Optional

from src.config.logger_config import logger

from src.db.queries.events import add_event
from src.db.queries.strategies import add_strategy



class AbstractStrategy(ABC):
    """
    Abstract base class for trading strategies.
    Defines a common interface for starting, stopping, and generating signals.
    """

    def __init__(self, strategy_id, event_manager_id, trading_pair: str, strategy_name: str,
                 parameters: Dict[str, Any]):
        self.strategy_id = strategy_id
        self.event_manager_id = event_manager_id
        self.trading_pair = trading_pair
        self.strategy_name = strategy_name
        self.parameters = parameters
        self.target_price = Optional[Decimal] | None
        logger.info(f"[{self.strategy_name}] Strategy created.")


    def _generate_signal_event(self, direction: str, executed_time):
        """
        Create a new SignalEvent in the event manager.
        """
        add_event(event_manager_id=self.event_manager_id, event_type="SignalEvent", priority=2,
                  payload={"strategy_id": self.strategy_id,
                           "strategy_name": self.strategy_name,
                           "trading_pair": self.trading_pair,
                           "direction": direction,
                           "target_price": str(self.target_price),
                           "executed_time": executed_time})
        logger.info(f"[{self.strategy_name}] SignalEvent created: {direction}")

    @abstractmethod
    def on_new_data(self, file_path: str):
        pass

    @abstractmethod
    def check_entry_signal(self):
        """
        Determine whether to generate an entry signal (BUY).
        """
        pass

    @abstractmethod
    def check_exit_signal(self):
        """
        Determine whether to generate an exit signal (SELL).
        """
        pass

    @staticmethod
    def create_strategy(strategy_class, event_manager_id: str, trading_pair: str,
                        strategy_name: str, parameters: Dict[str, Any]):
        """
        Create a strategy record in the database and return an instance of the strategy.

        :param strategy_class: Class of the strategy to instantiate.
        :param event_manager_id: ID of the event manager to use.
        :param trading_pair: Symbol to trade.
        :param strategy_name: Name of the strategy.
        :param parameters: Strategy-specific parameters.
        :return: Strategy instance.
        """
        strategy_id = add_strategy(event_manager_id, trading_pair, strategy_name, parameters)
        logger.info(f"Strategy {strategy_name} registered in DB.")
        return strategy_class(strategy_id, event_manager_id, trading_pair, strategy_name, parameters)
