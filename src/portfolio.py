import random
from decimal import Decimal

from loguru import logger
from src.db.queries.portfolios import get_portfolio_by_id, add_portfolio
from src.order_processing.order_controller import OrderController

class Portfolio:
    def __init__(self, portfolio_id):
        """
        Initializes a Portfolio object by loading its data from the database.

        :param portfolio_id: Unique identifier of the portfolio.
        :raises ValueError: If the portfolio is not found in the database.
        """
        data = get_portfolio_by_id(portfolio_id)[0]
        if not data:
            raise ValueError(f"Portfolio with id {portfolio_id} not found")

        self.portfolio_id = data['portfolio_id']
        self.risk_controller_id = data['risk_controller_id']
        self.event_manager_id = data['event_manager_id']
        self.portfolio_name = data['portfolio_name']
        self.managed_assets = data['managed_assets']
        self.currency = data['currency']
        self.initial_balance = data['initial_balance']
        self.exchange = data['exchange']

        logger.info(f"Initialized portfolio: {self.portfolio_id} - {self.portfolio_name}")

    @staticmethod
    def create_portfolio(event_manager_id, risk_controller_id, portfolio_name, managed_assets, currency, initial_balance, exchange):
        """
        Creates a new portfolio in the database.

        :param event_manager_id: ID of the associated event manager.
        :param risk_controller_id: ID of the associated risk controller.
        :param portfolio_name: Name of the portfolio.
        :param managed_assets: Assets managed by the portfolio (e.g., list or dict of asset names).
        :param currency: The base currency in which the portfolio is denominated (e.g., 'USD').
        :param initial_balance: Initial balance of the portfolio in base currency.
        :param exchange: Name of the exchange where the portfolio is active (e.g., 'Binance').
        :return: Instance of Portfolio.
        """
        portfolio_id = add_portfolio(
            event_manager_id=event_manager_id,
            risk_controller_id=risk_controller_id,
            portfolio_name=portfolio_name,
            currency=currency,
            initial_balance=initial_balance,
            managed_assets=managed_assets,
            exchange=exchange
        )
        logger.info(f"Created new portfolio with ID: {portfolio_id}")
        return Portfolio(portfolio_id)

    def handle_signal_event(self, event):
        """
        Handles a signal event from a strategy. If valid, creates a random spot order.

        :param event: Dictionary representing the signal event. Must contain 'event_type' and 'event_id'.
        """
        if event['event_type'] != 'SignalEvent':
            return

        direction = random.choice(['buy', 'sell'])
        quantity = random.uniform(1, 10)
        expected_price = random.uniform(100, 500)

        logger.info(f"Handling signal event in portfolio {self.portfolio_id}: direction={direction}, quantity={quantity:.2f}, price={expected_price:.2f}")

        OrderController().create_order(
            portfolio_id=self.portfolio_id,
            event_manager_id=self.event_manager_id,
            signal_id=event['event_id'],
            order_type='market',
            order_category='spot',
            order_side=direction,
            target_price=Decimal("40000"),
            order_status="pending",
            symbol="BTC/USDT",
            base_currency="BTC",
            quote_currency="USDT",
            initial_quantity=Decimal("0.0001")
        )

    def handle_order_filled_event(self, event):
        """
        Handles an order filled event. Logs the event details.

        :param event: Dictionary representing the order filled event. Must contain 'event_type' and 'payload' with 'order_id'.
        """
        if event['event_type'] != 'OrderFilledEvent':
            return

        order_id = event['payload'].get('order_id')
        logger.info(f"Portfolio {self.portfolio_id} received order filled event for order {order_id}")