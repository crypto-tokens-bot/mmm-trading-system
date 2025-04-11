import random

from src.strategy.abstract_strategy import AbstractStrategy


class RandomStrategy(AbstractStrategy):
    """
    Simple strategy that randomly generates BUY and SELL signals.
    """

    def check_entry_signal(self):
        """
        Generate a BUY signal with 50% probability.
        """
        if random.random() < 0.8:
            self._generate_signal_event("BUY")

    def check_exit_signal(self):
        """
        Generate a SELL signal with 50% probability.
        """
        if random.random() < 0.0:
            self._generate_signal_event("SELL")