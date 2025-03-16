import threading
import time
import logging
from order_executor import OrderExecutor

# Configure logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class LiveOrderExecutor(OrderExecutor):
    """
    LiveOrderExecutor executes orders on live exchanges.
    """

    _instance = None
    _instance_lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        with cls._instance_lock:
            if cls._instance is None:
                cls._instance = super(LiveOrderExecutor, cls).__new__(cls)
            return cls._instance

    def __init__(self, exchanges: dict, event_manager):
        """
        Initialize the LiveOrderExecutor.

        :param exchanges: A dictionary mapping exchange names (str) to exchange objects.
        :param event_manager: An instance of the EventManager used for event publishing.
        """
        # Prevent re-initialization in a singleton
        if hasattr(self, "_initialized") and self._initialized:
            return
        self.exchanges = exchanges
        self.event_manager = event_manager
        self._lock = threading.Lock()
        # Dictionary mapping order_id to order data for orders currently executing.
        self._executing_orders = {}
        # Start the background monitoring thread.
        self._monitor_thread = threading.Thread(target=self._monitor_executing_orders, daemon=True)
        self._monitor_thread.start()
        self._initialized = True
        logger.info("LiveOrderExecutor initialized and monitoring thread started.")

    def execute_order(self, order_id: str):
        """
        Thread-safely executes an order.

        :param order_id: Unique identifier of the order to execute.
        :raises ValueError: If the order is not found or the required exchange is unavailable.
        :raises Exception: For any failures during the execution process.
        """
        with self._lock:
            try:
                # Retrieve the order details from the database.
                order = self._get_order_by_id(order_id)
                if order is None:
                    raise ValueError(f"Order {order_id} not found.")

                exchange_name = order.get("exchange")
                if exchange_name not in self.exchanges:
                    raise ValueError(f"Exchange '{exchange_name}' not available for order {order_id}.")

                exchange = self.exchanges[exchange_name]
                # Place the order on the exchange.
                if not exchange.place_order(order):
                    raise Exception(f"Order placement failed on exchange {exchange_name} for order {order_id}.")

                # Update the order status to 'executing' in the database.
                self._update_order_status(order_id, "executing")
                order["order_status"] = "executing"
                # Add the order to the monitoring list.
                self._executing_orders[order_id] = order

                # Publish an event that order execution has started.
                self.event_manager.publish_event("OrderExecuting", {"order_id": order_id, "order_status": "executing"})
                logger.info(f"Order {order_id} is now executing on exchange {exchange_name}.")
            except Exception as e:
                logger.exception("Error executing order %s: %s", order_id, e)
                raise

    def _monitor_executing_orders(self):
        """
        Background thread method that continuously monitors orders with the 'executing' status.
        """
        while True:
            time.sleep(1)  # Polling interval
            with self._lock:
                executed_orders = []
                for order_id, order in list(self._executing_orders.items()):
                    exchange_name = order.get("exchange")
                    if exchange_name not in self.exchanges:
                        logger.error(f"Exchange '{exchange_name}' not found during monitoring of order {order_id}.")
                        continue
                    exchange = self.exchanges[exchange_name]
                    try:
                        current_status = exchange.check_order_status(order)
                        if current_status == "executed":
                            # Update the order status in the database.
                            self._update_order_status(order_id, "executed")
                            order["order_status"] = "executed"
                            self.event_manager.publish_event("OrderExecuted",
                                                             {"order_id": order_id, "order_status": "executed"})
                            logger.info(f"Order {order_id} executed on exchange {exchange_name}.")
                            executed_orders.append(order_id)
                    except Exception as e:
                        logger.exception("Error while monitoring order %s: %s", order_id, e)
                # Remove executed orders from the monitoring list.
                for order_id in executed_orders:
                    self._executing_orders.pop(order_id, None)