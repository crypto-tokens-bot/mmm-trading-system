import threading
from src.config.logger_config import logger
from queue import Queue

from src.db.queries.events import add_event
from src.db.queries.orders import get_order_by_id, get_executing_orders, update_order_status, update_order_exchange_id
from src.order_processing.order_executor import OrderExecutor


class LiveOrderExecutor(OrderExecutor):
    """
    LiveOrderExecutor executes orders on live exchanges.
    Implements a singleton pattern and uses a thread-safe queue to track executing orders.
    """

    _instance = None
    _instance_lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        with cls._instance_lock:
            if cls._instance is None:
                cls._instance = super(LiveOrderExecutor, cls).__new__(cls)
            return cls._instance

    def __init__(self, exchanges: dict):
        """
        Initialize the LiveOrderExecutor.

        :param exchanges: A dictionary mapping exchange names (str) to exchange objects.
        """
        if hasattr(self, "_initialized") and self._initialized:
            return

        self.exchanges = exchanges
        self._order_queue = Queue()

        executing_orders = get_executing_orders()
        for order in executing_orders:
            self._order_queue.put(order["order_id"])
        logger.info(f"Restored {len(executing_orders)} executing orders into queue.")

        self._monitor_thread = threading.Thread(target=self._monitor_executing_orders, daemon=True)
        self._monitor_thread.start()

        self._initialized = True
        logger.info("LiveOrderExecutor initialized and monitoring thread started.")

    def execute_order(self, order_id: str):
        """
        Executes an order by placing it on the exchange and adding it to the monitoring queue.

        :param order_id: Unique identifier of the order to execute.
        :raises ValueError: If the order is not found or the required exchange is unavailable.
        :raises Exception: For any failures during execution.
        """
        try:
            order = get_order_by_id(order_id)[0]
            if order is None:
                raise ValueError(f"Order {order_id} not found.")

            exchange = self.exchanges['bybit']

            if order['order_category'] == 'spot':
                self._order_queue.put(exchange.create_spot_order(order_id))
            logger.info(f"Order {order_id} is now executing.")
        except Exception as e:
            logger.exception("Error executing order %s: %s", order_id, e)
            raise

    def _monitor_executing_orders(self):
        """
        Background thread method that continuously monitors executing orders.
        """
        while True:
            try:
                order_id = self._order_queue.get()
                order = get_order_by_id(order_id)[0]
                if order is None:
                    logger.warning(f"Order {order_id} not found during monitoring.")
                    continue
                logger.debug(f"Order {order_id} status check...")

                # exchange_name = order.get("exchange")
                # if exchange_name not in self.exchanges:
                #     logger.error(f"Exchange '{exchange_name}' not found for order {order_id}.")
                #     continue

                exchange = self.exchanges['bybit']
                status = exchange.check_order_status(order['order_exchange_id'], order['symbol'])
                logger.debug(f"Order {order_id} status: {status}")
                if status == "executed":
                    update_order_status(order_id, "executed")
                    add_event(order['event_manager_id'], "OrderExecutedEvent", 2, {"order_id": order_id})
                    logger.info(f"Order {order_id} executed.")
                elif status == "cancelled":
                    update_order_status(order_id, "cancelled")
                    logger.warning(f"Order {order_id} cancelled.")
                else:
                    self._order_queue.put(order_id)
            except Exception as e:
                logger.exception(f"Error while monitoring order {order_id}: {e}")
                self._order_queue.put(order_id)  # Retry later
