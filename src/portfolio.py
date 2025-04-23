import random
from decimal import Decimal
from math import lgamma

from src.config.logger_config import logger
from src.connectors.exchange_connector import ExchangeConnector
from src.db.queries.orders import get_order_by_id, update_order_status
from src.db.queries.portfolios import get_portfolio_by_id, add_portfolio, update_portfolio_status, update_managed_assets
from src.order_processing.order_controller import OrderController
from src.risk_controller import RiskController, TradeDecision


class Portfolio:
    _cache: dict = {}

    @classmethod
    def load_by_id(cls, portfolio_id: int):
        if portfolio_id not in cls._cache:
            cls._cache[portfolio_id] = cls(portfolio_id)
        return cls._cache[portfolio_id]

    def __init__(self, portfolio_id):
        """
        Initializes a Portfolio object by loading its data from the database.

        :param portfolio_id: Unique identifier of the portfolio.
        :raises ValueError: If the portfolio is not found in the database.
        """
        data = get_portfolio_by_id(portfolio_id)
        if not data:
            raise ValueError(f"Portfolio with id {portfolio_id} not found")

        self.portfolio_id = str(data['portfolio_id'])
        self.risk_controller_id = str(data['risk_controller_id'])
        self.event_manager_id = str(data['event_manager_id'])
        self.portfolio_name = data['portfolio_name']
        self.managed_assets = data['managed_assets']
        self.currency = data['currency']
        self.initial_balance = data['initial_balance']
        self.exchange = ExchangeConnector.get_exchange_connector(data['exchange'])
        self.risk_controller = RiskController.create_risk_controller(
            self.risk_controller_id,
            self
        )
        self.has_executing_order = data['has_executing_order']

        logger.info(f"Initialized portfolio: {self.portfolio_id} - {self.portfolio_name}")

    @classmethod
    def from_id(cls, portfolio_id: str) -> "Portfolio | None":
        """
        Load a portfolio from the database and return the object.

        :param portfolio_id: Primary-key of the portfolio row.
        :return: Portfolio object or ``None`` when the row is missing or an error occurs.
        """
        try:
            if portfolio_id in cls._cache:
                return cls._cache[portfolio_id]

            row = get_portfolio_by_id(portfolio_id)
            if row is None:
                logger.error(f"Portfolio with id {portfolio_id} not found")
                return None

            portfolio = cls(portfolio_id=row["portfolio_id"])
            cls._cache[portfolio_id] = portfolio
            return portfolio

        except Exception as exc:
            logger.exception(f"Failed to build portfolio for id {portfolio_id}: {exc}")
            return None


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
        self.has_executing_order = True
        update_portfolio_status(self.portfolio_id, self.has_executing_order)
        executed_time = event['payload']['executed_time'] if 'executed_time' in event['payload'] else None
        OrderController().create_order(
            portfolio_id=self.portfolio_id,
            event_manager_id=self.event_manager_id,
            signal_id=event['event_id'],
            order_type='market',
            order_category='spot',
            order_side=decision.direction,
            target_price=decision.target_price,
            order_status="pending",
            symbol=decision.trading_pair,
            base_currency=decision.trading_pair[:decision.trading_pair.index('/')],
            quote_currency=self.currency,
            initial_quantity=decision.quantity,
            stop_loss=decision.stop_loss,
            take_profit=decision.take_profit,
            executed_time=executed_time
        )


    def handle_order_executed_event(self, event):
        """
        Handles an order filled event. Logs the event details.

        :param event: Dictionary representing the order filled event. Must contain 'event_type' and 'payload' with 'order_id'.
        """
        order_id = event['payload']['order_id']
        order_exchange_id = event['payload']['order_exchange_id']
        symbol = event['payload']['symbol']
        base_asset, quote_asset = symbol.split('/')
        order_side = None
        if order_exchange_id is None:
            order_info = get_order_by_id(order_id)[0]
            logger.debug(order_info)
            order_side = order_info['order_side']
            filled_quantity = Decimal(order_info['executed_quantity'])
            cost = Decimal(order_info['average_price'])
            fee_cost = Decimal(order_info['total_fee'])
            fee_currency = quote_asset
        else:
            order_info = self.exchange.get_order_info(order_exchange_id, symbol)
            logger.debug(order_info)
            order_side = order_info['side']
            filled_quantity = Decimal(order_info['filled'])
            cost = Decimal(order_info['cost'])
            fee_cost = Decimal(order_info['fee'].get('cost', 0))
            fee_currency = order_info['fee'].get('currency')
        if order_side == 'buy':
            self.managed_assets[base_asset] = self.managed_assets.get(base_asset, Decimal(0)) + filled_quantity
            self.managed_assets[quote_asset] = self.managed_assets.get(quote_asset, Decimal(0)) - cost
        else:
            self.managed_assets[base_asset] = self.managed_assets.get(base_asset, Decimal(0)) - filled_quantity
            self.managed_assets[quote_asset] = self.managed_assets.get(quote_asset, Decimal(0)) + cost

        self.managed_assets[fee_currency] -= fee_cost
        self.managed_assets[base_asset] = max(self.managed_assets[base_asset], 0)
        self.managed_assets[quote_asset] = max(self.managed_assets[quote_asset], 0)


        logger.debug(self.managed_assets)
        update_managed_assets(self.portfolio_id, self.managed_assets)
        self.has_executing_order = False
        update_portfolio_status(self.portfolio_id, self.has_executing_order)
        logger.info(f"Portfolio {self.portfolio_id} received order filled event for order {order_id}")
