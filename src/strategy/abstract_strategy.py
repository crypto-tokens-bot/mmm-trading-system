import threading
import time
from abc import ABC, abstractmethod
from decimal import Decimal
from typing import Dict, Any, Optional

from src.config.logger_config import logger

from src.db.queries.events import add_event
from src.db.queries.strategies import add_strategy, get_strategy_by_id



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
    def from_id(strategy_id: str) -> "AbstractStrategy | None":
        """
        Load a strategy from the database and return an instantiated subclass.

        :param strategy_id: Primary-key of the strategy row.
        :return: Concrete strategy object or ``None`` on failure / not found.
        """
        try:
            strategy = get_strategy_by_id(strategy_id)
            if strategy is None:
                logger.error(f"Strategy with id {strategy_id} not found")
                return None

            strategy_cls = None

            if strategy['strategy_type'] == "Random":
                from src.strategy.random_strategy import RandomStrategy
                strategy_cls = RandomStrategy
            if strategy_cls is None:
                logger.error(f"Unknown strategy_type {strategy['strategy_type']} for strategy id {strategy_id}" )
                return None

            return strategy_cls(
                strategy_id=str(strategy['strategy_id']),
                event_manager_id=str(strategy['event_manager_id']),
                trading_pair=strategy['trading_pair'],
                strategy_name=strategy['strategy_name'],
                parameters=strategy['parameters'],
            )

        except Exception as exc:
            logger.exception(f"Failed to build strategy instance for id {strategy_id}: {exc}")
            return None
