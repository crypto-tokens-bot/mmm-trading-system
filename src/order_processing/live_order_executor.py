import asyncio
import threading
import time
import logging
from queue import Queue

from src.connectors.bybit_connector import BybitAsyncConnector
from src.db.queries.orders import get_order_by_id, get_executing_orders, update_order_status
from src.order_processing.order_executor import OrderExecutor

# Configure logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


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
        self._lock = threading.Lock()

        # Re-queue all currently executing orders
        executing_orders = get_executing_orders()
        for order in executing_orders:
            self._order_queue.put(order["order_id"])
        logger.info(f"Restored {len(executing_orders)} executing orders into queue.")

        # Start monitoring thread
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

            # Use the appropriate exchange connector (here hardcoded as Bybit for now)
            exchange = self.exchanges['bybit']

            if order['order_category'] == 'spot':
                result = asyncio.run(exchange.create_spot_order(order_id))
                if not result:
                    raise Exception(f"Order placement failed for order {order_id}.")
                update_order_status(order_id, "executing")
            # Add order to the queue
            self._order_queue.put(order_id)
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
                order_id = self._order_queue.get()  # Blocks until an order is available
                order = get_order_by_id(order_id)[0]
                if order is None:
                    logger.warning(f"Order {order_id} not found during monitoring.")
                    continue

                # exchange_name = order.get("exchange")
                # if exchange_name not in self.exchanges:
                #     logger.error(f"Exchange '{exchange_name}' not found for order {order_id}.")
                #     continue

                exchange = self.exchanges['bybit']
                # status = exchange.check_order_status(order)
                status = "executed"
                if status == "executed":
                    update_order_status(order_id, "executed")
                    # self.event_manager.publish_event("OrderExecuted", {
                    #     "order_id": order_id,
                    #     "order_status": "executed"
                    # })
                    logger.info(f"Order {order_id} executed.")
                else:
                    # Re-queue the order if still pending
                    self._order_queue.put(order_id)
            except Exception as e:
                logger.exception(f"Error while monitoring order {order_id}: {e}")
                self._order_queue.put(order_id)  # Retry later
