import random
from decimal import Decimal

from src.config.logger_config import logger
from src.db.queries.portfolios import get_portfolio_by_id, add_portfolio
from src.order_processing.order_controller import OrderController
from src.risk_controller import RiskController, TradeDecision


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
        self.risk_controller = RiskController.create_risk_controller(
            self.risk_controller_id,
            self
        )

        logger.info(f"Initialized portfolio: {self.portfolio_id} - {self.portfolio_name}")

    @staticmethod
    def create_portfolio(event_manager_id, risk_controller_id, portfolio_name, managed_assets, currency,
                         initial_balance, exchange):
        """
        Creates a new portfolio in the database.

        :param event_manager_id: ID of the associated event manager.
        :param risk_controller_id: ID of the associated risk controller.
        :param portfolio_name: Name of the portfolio.
        :param managed_assets: Assets managed by the portfolio (e.g., dict of asset names).
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
        logger.info(f"Handling signal event in portfolio {self.portfolio_id}")

        decision: TradeDecision | None = self.risk_controller.evaluate(event)

        if decision is None:
            logger.info("Signal rejected by RiskController")
            return

        OrderController().create_order(
            portfolio_id=self.portfolio_id,
            event_manager_id=self.event_manager_id,
            signal_id=event['event_id'],
            order_type='market',
            order_category='spot',
            order_side=decision.direction,
            target_price=Decimal("0"), # fix
            order_status="pending",
            symbol=decision.trading_pair,
            base_currency=decision.trading_pair[:decision.trading_pair.index('/')],
            quote_currency=self.currency,
            initial_quantity=decision.quantity,
            stop_loss=decision.stop_loss,
            take_profit=decision.take_profit,
        )


def handle_order_filled_event(self, event):
    """
    Handles an order filled event. Logs the event details.

    :param event: Dictionary representing the order filled event. Must contain 'event_type' and 'payload' with 'order_id'.
    """
    order_id = event['payload']['order_id']
    logger.info(f"Portfolio {self.portfolio_id} received order filled event for order {order_id}")
