import uuid
import logging
from decimal import Decimal
from typing import List, Optional, Any

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class OrderController:
    """
    A controller that handles creating main, stop-loss, and take-profit orders.

    This class is implemented as a Singleton. Use `OrderController()` to get the
    single instance. It interacts with an event manager to publish events after
    creating orders in a simulated database.
    """

    _instance = None

    def __new__(cls, *args, **kwargs) -> "OrderController":
        """
        Ensures only one instance of OrderController is created (Singleton pattern).

        :return: The singleton instance of this class.
        :rtype: OrderController
        """
        if cls._instance is None:
            cls._instance = super(OrderController, cls).__new__(cls)
        return cls._instance

    def create_order(
        self,
        portfolio_id: int,
        event_manager_id: str,
        signal_id: str,
        order_type: str,
        order_category: str,
        order_side: str,
        target_price: Decimal,
        order_status: str,
        symbol: str,
        exchange: str,
        base_currency: str,
        quote_currency: str,
        initial_quantity: Decimal,
        event_manager: Any,
        stop_loss: Optional[Decimal] = None,
        take_profit: Optional[Decimal] = None
    ) -> List[str]:
        """
        Creates a main order and optionally stop-loss / take-profit orders.

        :param portfolio_id: Identifier of the portfolio creating the order.
        :type portfolio_id: int
        :param event_manager_id: Identifier of the event manager.
        :type event_manager_id: str
        :param signal_id: Identifier of the trading signal.
        :type signal_id: str
        :param order_type: The type of the order (e.g., 'spot', 'stop_loss').
        :type order_type: str
        :param order_category: The category of the order (e.g., 'limit', 'market').
        :type order_category: str
        :param order_side: The side of the order, either 'buy' or 'sell'.
        :type order_side: str
        :param target_price: The target price for the main order.
        :type target_price: Decimal
        :param order_status: The initial status of the order (e.g., 'pending_execution').
        :type order_status: str
        :param symbol: Trading symbol (e.g., 'BTCUSD').
        :type symbol: str
        :param exchange: The name of the exchange (e.g., 'Binance').
        :type exchange: str
        :param base_currency: The base currency (e.g., 'BTC').
        :type base_currency: str
        :param quote_currency: The quote currency (e.g., 'USD').
        :type quote_currency: str
        :param initial_quantity: The initial quantity for the order.
        :type initial_quantity: Decimal
        :param event_manager: An instance of EventManager used to publish events.
        :type event_manager: Any
        :param stop_loss: The price for the stop-loss order (optional).
        :type stop_loss: Optional[Decimal]
        :param take_profit: The price for the take-profit order (optional).
        :type take_profit: Optional[Decimal]
        :return: A list of created order IDs (as strings).
        :rtype: List[str]
        :raises ValueError: If any mandatory parameter is invalid.
        :raises Exception: For any failure during order creation.
        """
        try:
            # Basic validation
            if portfolio_id is None:
                raise ValueError("portfolio_id cannot be None.")
            if not event_manager_id:
                raise ValueError("event_manager_id must be provided.")
            if not symbol:
                raise ValueError("symbol must be provided.")
            if not exchange:
                raise ValueError("exchange must be provided.")
            if order_side not in ["buy", "sell"]:
                raise ValueError("order_side must be 'buy' or 'sell'.")
            if target_price <= Decimal("0"):
                raise ValueError("target_price must be greater than 0.")
            if initial_quantity <= Decimal("0"):
                raise ValueError("initial_quantity must be greater than 0.")
            if stop_loss is not None and stop_loss <= Decimal("0"):
                raise ValueError("stop_loss must be greater than 0 if provided.")
            if take_profit is not None and take_profit <= Decimal("0"):
                raise ValueError("take_profit must be greater than 0 if provided.")

            created_order_ids: List[str] = []

            # Main order data in the exact column order (excluding DB-managed fields):
            main_order_data = {
                "portfolio_id": portfolio_id,
                "event_manager_id": event_manager_id,
                "signal_id": signal_id,
                "order_type": order_type,
                "order_category": order_category,
                "order_side": order_side,
                "target_price": target_price,
                "order_status": order_status,
                "symbol": symbol,
                "exchange": exchange,
                "base_currency": base_currency,
                "quote_currency": quote_currency,
                "initial_quantity": initial_quantity,
                "executed_quantity": Decimal("0.0"),
                "extra_summary": None,
                "total_fee": Decimal("0.0"),
                # created_at, updated_at, executed_at handled by DB
            }

            main_order_id = self._insert_order_into_db(main_order_data)
            created_order_ids.append(main_order_id)
            event_manager.publish_event(
                "OrderAwaitingExecution",
                {"order_id": main_order_id, "order_status": order_status}
            )
            logger.info("Main order created with ID: %s", main_order_id)

            # Create stop-loss order if specified
            if stop_loss is not None:
                stop_loss_order_id = self._create_stop_loss_order(
                    parent_order_id=main_order_id,
                    parent_order_data=main_order_data,
                    stop_loss_price=stop_loss,
                    event_manager=event_manager
                )
                created_order_ids.append(stop_loss_order_id)
                logger.info("Stop-loss order created with ID: %s", stop_loss_order_id)

            # Create take-profit order if specified
            if take_profit is not None:
                take_profit_order_id = self._create_take_profit_order(
                    parent_order_id=main_order_id,
                    parent_order_data=main_order_data,
                    take_profit_price=take_profit,
                    event_manager=event_manager
                )
                created_order_ids.append(take_profit_order_id)
                logger.info("Take-profit order created with ID: %s", take_profit_order_id)

            return created_order_ids

        except Exception as e:
            logger.exception("Failed to create order: %s", e)
            raise

    def _create_stop_loss_order(
        self,
        parent_order_id: str,
        parent_order_data: dict,
        stop_loss_price: Decimal,
        event_manager: Any
    ) -> str:
        """
        Creates a stop-loss order linked to a parent order.

        The stop-loss order inherits most fields from the parent order,
        but uses 'stop_loss' as its order_type and inverts the side if needed.

        :param parent_order_id: The ID of the main (parent) order.
        :type parent_order_id: str
        :param parent_order_data: The main order's data dictionary.
        :type parent_order_data: dict
        :param stop_loss_price: The price at which the stop-loss triggers.
        :type stop_loss_price: Decimal
        :param event_manager: An instance of EventManager used to publish events.
        :type event_manager: Any
        :return: The ID of the created stop-loss order.
        :rtype: str
        :raises Exception: If the stop-loss order creation fails.
        """
        try:
            # Invert the order side for stop-loss
            stop_order_side = "sell" if parent_order_data["order_side"] == "buy" else "buy"

            stop_loss_order_data = {
                "portfolio_id": parent_order_data["portfolio_id"],
                "event_manager_id": parent_order_data["event_manager_id"],
                "signal_id": parent_order_data["signal_id"],
                "order_type": "stop_loss",
                "order_category": parent_order_data["order_category"],
                "order_side": stop_order_side,
                "target_price": stop_loss_price,
                "order_status": parent_order_data["order_status"],
                "symbol": parent_order_data["symbol"],
                "exchange": parent_order_data["exchange"],
                "base_currency": parent_order_data["base_currency"],
                "quote_currency": parent_order_data["quote_currency"],
                "initial_quantity": parent_order_data["initial_quantity"],
                "executed_quantity": Decimal("0.0"),
                "extra_summary": None,
                "total_fee": Decimal("0.0"),
                "parent_order_id": parent_order_id,  # extra link (not in original DB schema)
            }

            stop_loss_order_id = self._insert_order_into_db(stop_loss_order_data)
            event_manager.publish_event(
                "OrderAwaitingExecution",
                {"order_id": stop_loss_order_id, "order_status": parent_order_data["order_status"]}
            )
            return stop_loss_order_id

        except Exception as e:
            logger.exception("Failed to create stop-loss order: %s", e)
            raise

    def _create_take_profit_order(
        self,
        parent_order_id: str,
        parent_order_data: dict,
        take_profit_price: Decimal,
        event_manager: Any
    ) -> str:
        """
        Creates a take-profit order linked to a parent order.

        The take-profit order inherits most fields from the parent order,
        but uses 'take_profit' as its order_type and inverts the side if needed.

        :param parent_order_id: The ID of the main (parent) order.
        :type parent_order_id: str
        :param parent_order_data: The main order's data dictionary.
        :type parent_order_data: dict
        :param take_profit_price: The price at which the take-profit triggers.
        :type take_profit_price: Decimal
        :param event_manager: An instance of EventManager used to publish events.
        :type event_manager: Any
        :return: The ID of the created take-profit order.
        :rtype: str
        :raises Exception: If the take-profit order creation fails.
        """
        try:
            # Invert the order side for take-profit
            take_order_side = "sell" if parent_order_data["order_side"] == "buy" else "buy"

            take_profit_order_data = {
                "portfolio_id": parent_order_data["portfolio_id"],
                "event_manager_id": parent_order_data["event_manager_id"],
                "signal_id": parent_order_data["signal_id"],
                "order_type": "take_profit",
                "order_category": parent_order_data["order_category"],
                "order_side": take_order_side,
                "target_price": take_profit_price,
                "order_status": parent_order_data["order_status"],
                "symbol": parent_order_data["symbol"],
                "exchange": parent_order_data["exchange"],
                "base_currency": parent_order_data["base_currency"],
                "quote_currency": parent_order_data["quote_currency"],
                "initial_quantity": parent_order_data["initial_quantity"],
                "executed_quantity": Decimal("0.0"),
                "extra_summary": None,
                "total_fee": Decimal("0.0"),
                "parent_order_id": parent_order_id,  # extra link (not in original DB schema)
            }

            take_profit_order_id = self._insert_order_into_db(take_profit_order_data)
            event_manager.publish_event(
                "OrderAwaitingExecution",
                {"order_id": take_profit_order_id, "order_status": parent_order_data["order_status"]}
            )
            return take_profit_order_id

        except Exception as e:
            logger.exception("Failed to create take-profit order: %s", e)
            raise