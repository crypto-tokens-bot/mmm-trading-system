import pandas as pd
import mplfinance as mpf
import os
import threading
import time

from src.config.logger_config import logger

from src.connectors.exchange_connector import ExchangeConnector
from src.db.queries.portfolios import get_portfolio_by_id, update_portfolio_status, update_portfolio_prices, \
    get_all_portfolios


class Monitoring:
    def __init__(self, size=(12, 6)):
        self.size = size
        self.ohlc_cols = ['open', 'high', 'low', 'close']
        self.ohlcv_cols = ['open', 'high', 'low', 'close', 'volume']
        self._exchange = ExchangeConnector.get_exchange_connector("bybit")
        self._is_running = True
        self.thread = threading.Thread(target=self._price_update_loop, daemon=True)
        self.thread.start()

    def _price_update_loop(self):
        while self._is_running:
            try:
                portfolios_ids = get_all_portfolios()
                for portfolio in portfolios_ids:
                    portfolio_id = str(portfolio['portfolio_id'])
                    portfolio_info = get_portfolio_by_id(portfolio_id)[0]
                    current_prices = {}
                    base_currency = portfolio_info['currency']

                    for asset in portfolio_info['managed_assets']:
                        if asset == base_currency:
                            current_prices[asset] = 1
                        else:
                            price = self._exchange.get_order_book(asset + "/" + base_currency, limit=1)
                            price = price['bids'][0][0]
                            current_prices[asset] = price
                    update_portfolio_prices(portfolio_id, current_prices)

                logger.success("Prices updated successfully")
            except Exception as e:
                logger.error(f"Error updating prices: {e}")
            time.sleep(300)
        logger.info("Price update loop stopped")

    def stop(self):
        self._is_running = False
        logger.info("Stopping price update loop")