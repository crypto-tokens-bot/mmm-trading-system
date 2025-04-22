from datetime import datetime
from loguru import logger

from src.db.queries.events import add_event
from src.db.queries.orders import update_order_info, update_order_status, get_order_by_id
from src.order_processing.order_executor import OrderExecutor


class SimulatedOrderExecutor(OrderExecutor):
    """
    Simulates the execution of orders for backtesting purposes. Applies slippage,
    fees, and logs executed orders into the database with a backtest flag.

    :param market_data_provider: Object responsible for providing market data.
    :param db_connector: Object responsible for database operations.
    :param slippage_model: Model used to calculate slippage.
    :param fee_model: Model used to calculate transaction fees.
    :param event_manager: Object responsible for emitting execution events.
    """

    class SlippageModel:
        """
        Calculates price slippage based on a fixed percentage.

        :param slippage_percent: Percentage of price slippage to apply.
        """
        def __init__(self, slippage_percent=0.001):
            self.slippage_percent = slippage_percent

        def calculate(self, order, market_price):
            """
            Calculate the slippage-adjusted price.

            :param order: Order object with direction.
            :param market_price: Base market price.
            :return: Adjusted price including slippage.
            """
            direction_factor = 1 if order['order_side'] == 'BUY' else -1
            slippage = direction_factor * market_price * self.slippage_percent
            return slippage

    class FeeModel:
        """
        Calculates transaction fees.

        :param fixed_fee: Constant base fee.
        :param percentage_fee: Percentage of the trade value.
        """
        def __init__(self, fixed_fee=0.1, percentage_fee=0.0005):
            self.fixed_fee = fixed_fee
            self.percentage_fee = percentage_fee

        def calculate(self, order, execution_price):
            """
            Calculate the total fee for an order.

            :param order: Order object.
            :param execution_price: Final execution price.
            :return: Total fee amount.
            """
            fee = self.fixed_fee + (execution_price * float(order['initial_quantity']) * self.percentage_fee)
            return fee

    def __init__(self, slippage_model, fee_model, event_manager):
        self.slippage_model = slippage_model
        self.fee_model = fee_model
        self.event_manager = event_manager

    def execute_order(self, order_id, params={}):
        """
        Simulate the execution of an order with fees and slippage, store it in the database,
        and emit an execution event.

        :param order_id: Order id.
        :return: Executed order record.
        """
        try:
            order = get_order_by_id(order_id)[0]
            market_price = float(order['target_price'])
            slippage = self.slippage_model.calculate(order, market_price)
            execution_price = market_price + slippage
            fees = self.fee_model.calculate(order, execution_price)
            update_order_info(order_id, executed_quantity=order['initial_quantity'],
                              average_price=execution_price, total_fee=fees, execution_summary={})
            update_order_status(order_id, "executed", params['executed_time'])

            add_event(order['event_manager_id'], "OrderExecutedEvent", 2,
                      {"order_id": order_id, 'order_exchange_id': None,
                       "portfolio_id": str(order['portfolio_id']), 'symbol': order['symbol']})
            logger.success(f"Simulated order {order_id} executed at {execution_price}.")

        except Exception as e:
            logger.error(f"Failed to execute simulated order {order_id}: {e}")
            return None