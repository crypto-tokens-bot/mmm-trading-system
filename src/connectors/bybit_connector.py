# bybit_connector.py

import ccxt.async_support as ccxt
from src import AsyncExchangeConnector


class BybitAsyncConnector(AsyncExchangeConnector):
    """
    Asynchronous connector for Bybit exchange, based on the AsyncExchangeConnector base class.
    """

    def __init__(self, api_key: str = None, api_secret: str = None, testnet: bool = False):
        """
        Initializes the Bybit connector with API credentials and optional sandbox mode.

        :param api_key: API key for authentication.
        :param api_secret: API secret for authentication.
        :param testnet: If True, enables sandbox mode (if supported by Bybit).
        """
        super().__init__(exchange=ccxt.bybit, api_key=api_key, api_secret=api_secret, testnet=testnet)
