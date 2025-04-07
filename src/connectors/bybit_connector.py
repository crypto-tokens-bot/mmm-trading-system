# bybit_connector.py
import os
import ccxt

from src.connectors.exchange_connector import ExchangeConnector


class BybitConnector(ExchangeConnector):
    """
    Asynchronous connector for Bybit exchange, based on the AsyncExchangeConnector base class.
    """

    def __init__(self, testnet: bool = False):
        """
        Initializes the Bybit connector with API credentials and optional sandbox mode.

        :param testnet: If True, enables sandbox mode (if supported by Bybit).
        """
        api_key = os.getenv('BYBIT_API_KEY')
        api_secret = os.getenv('BYBIT_API_SECRET')
        super().__init__(exchange=ccxt.bybit, api_key=api_key, api_secret=api_secret, testnet=testnet)
        self._exchange.options['recvWindow'] = 10000
        self._exchange.options['adjustForTimeDifference'] = True
        # self._exchange.load_time_difference()

