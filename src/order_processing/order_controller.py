import uuid
from loguru import logger
from decimal import Decimal
from typing import List, Optional, Any

from src.db.queries.events import add_event
from src.db.queries.orders import add_order

logger.add("../../logs/order_controller.log", rotation="10 MB", level="INFO", format="{time} - {level} - {message}")

class OrderController:
    """
    A controller that handles creating main, stop-loss, and take-profit orders.
    This class is implemented as a Singleton. Use `OrderController()` to get the
    single instance. It interacts with an event manager to publish events after
    creating orders in a simulated database.
    """

    _instance = None

    def __new__(cls, *args, **kwargs):
        """
        Ensures only one instance of OrderController is created (Singleton pattern).
        """
        if cls._instance is None:
            cls._instance = super(OrderController, cls).__new__(cls)
        return cls._instance

    def create_order(
        self,
        portfolio_id: str,
        event_manager_id: str,
        signal_id: str,
        order_type: str,
        order_category: str,
        order_side: str,
        target_price: Decimal,
        order_status: str,
        symbol: str,
        base_currency: str,
        quote_currency: str,
        initial_quantity: Decimal,
        event_manager: Any,
        stop_loss: Optional[Decimal] = None,
        take_profit: Optional[Decimal] = None
    ) -> List[str]:
        """
        Creates a main order and optionally stop-loss / take-profit orders within a trading system.

        :param portfolio_id: Identifier of the portfolio creating the order.
        :param event_manager_id: Identifier of the event manager responsible for order events.
        :param signal_id: Identifier of the trading signal that initiated the order.
        :param order_type: Type of the order, such as 'limit', 'market', etc.
        :param order_category: Category of the order, such as 'spot', 'futures', etc.
        :param order_side: Side of the order, 'buy' or 'sell'.
        :param target_price: Target price at which the main order should execute.
        :param order_status: Initial status of the order, typically 'pending'.
        :param symbol: Trading symbol, e.g., 'BTCUSD'.
        :param base_currency: Base currency of the trade, e.g., 'BTC'.
        :param quote_currency: Quote currency of the trade, e.g., 'USD'.
        :param initial_quantity: Amount of the asset to be traded.
        :param event_manager: An instance of EventManager used to handle events related to the order.
        :param stop_loss: Optional. Price at which a stop-loss order should trigger to limit loss.
        :param take_profit: Optional. Price at which a take-profit order should trigger to secure profits.

        :return: A list of UUIDs representing the IDs of the created orders, including the main order and any associated stop-loss or take-profit orders.
        """
        try:
            main_order_id = add_order(portfolio_id, event_manager_id, signal_id, order_type, order_category, order_side, order_status, symbol, base_currency, quote_currency, initial_quantity, target_price)
            created_order_ids = [main_order_id]
            add_event(event_manager_id, "OrderPlacementEvent", 1, {"order_id": main_order_id})

            if stop_loss is not None:
                stop_loss_order_id = self._create_stop_loss_order(main_order_id, portfolio_id, event_manager_id, signal_id, order_category, order_status, symbol, base_currency, quote_currency, initial_quantity, stop_loss, event_manager, order_side)
                created_order_ids.append(stop_loss_order_id)

            if take_profit is not None:
                take_profit_order_id = self._create_take_profit_order(main_order_id, portfolio_id, event_manager_id, signal_id, order_category, order_status, symbol, base_currency, quote_currency, initial_quantity, take_profit, event_manager, order_side)
                created_order_ids.append(take_profit_order_id)

            return created_order_ids

        except Exception as e:
            logger.exception("Failed to create order: %s", e)
            raise

    def _create_stop_loss_order(self, parent_order_id, portfolio_id, event_manager_id, signal_id, order_category, order_status, symbol, base_currency, quote_currency, initial_quantity, stop_loss_price, event_manager, order_side):
        """
        Creates a stop-loss order linked to a parent order. The stop-loss order will have the opposite side of the main order.

        :param parent_order_id (str): UUID of the parent order.

        :return: UUID of the created stop-loss order.
        """
        stop_loss_order_side = "sell" if order_side == "buy" else "buy"
        stop_loss_order_id = add_order(portfolio_id, event_manager_id, signal_id, "stop_loss", order_category, stop_loss_order_side, order_status, symbol, base_currency, quote_currency, initial_quantity, stop_loss_price, parent_order_id=parent_order_id)
        add_event(event_manager_id, "OrderPlacementEvent", 1, {"order_id": stop_loss_order_id})
        return stop_loss_order_id

    def _create_take_profit_order(self, parent_order_id, portfolio_id, event_manager_id, signal_id, order_category, order_status, symbol, base_currency, quote_currency, initial_quantity, take_profit_price, event_manager, order_side):
        """
        Creates a take-profit order linked to a parent order. The take-profit order will have the opposite side of the main order.

        :param parent_order_id (str): UUID of the parent order.

        :return: str: UUID of the created take-profit order.
        """
        take_profit_order_side = "sell" if order_side == "buy" else "buy"
        take_profit_order_id = add_order(portfolio_id, event_manager_id, signal_id, "take_profit", order_category, take_profit_order_side, order_status, symbol, base_currency, quote_currency, initial_quantity, take_profit_price, parent_order_id=parent_order_id)
        add_event(event_manager_id, "OrderPlacementEvent", 1, {"order_id": take_profit_order_id})
        return take_profit_order_id
