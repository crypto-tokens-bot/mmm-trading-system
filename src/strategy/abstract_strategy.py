import threading
import time
from abc import ABC, abstractmethod
from typing import Dict, Any
from src.config.logger_config import logger

from src.db.queries.events import add_event
from src.db.queries.strategies import add_strategy, update_strategy_status


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
        self._thread = None
        self._running = False

    def start(self):
        """
        Start the strategy in a separate thread and mark it as active in the database.
        """
        self._running = True
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()
        update_strategy_status(self.strategy_id, "active")
        logger.info(f"[{self.strategy_name}] Strategy started.")

    def stop(self):
        """
        Stop the strategy and update its status in the database.
        """
        self._running = False
        if self._thread:
            self._thread.join()
        update_strategy_status(self.strategy_id, "inactive")
        logger.info(f"[{self.strategy_name}] Strategy stopped.")

    def on_new_data(self, file_path: str):
        logger.info(f"[{self.strategy_name}] signal from market data.")

    def _run_loop(self):
        """
        Main strategy loop, periodically checks for entry and exit signals.
        """
        while self._running:
            self.check_entry_signal()
            self.check_exit_signal()
            time.sleep(5)

    def _generate_signal_event(self, direction: str):
        """
        Create a new SignalEvent in the event manager.
        """
        add_event(event_manager_id=self.event_manager_id, event_type="SignalEvent", priority=2,
                  payload={"strategy_id": self.strategy_id,
                           "strategy_name": self.strategy_name,
                           "trading_pair": self.trading_pair,
                           "direction": direction})
        logger.info(f"[{self.strategy_name}] SignalEvent created: {direction}")

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
