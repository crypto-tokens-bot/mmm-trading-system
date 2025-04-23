import threading
from datetime import datetime, timedelta

from src.config.logger_config import logger
from queue import Queue

from src.db.queries.events import add_event
from src.db.queries.orders import get_order_by_id, get_executing_orders, update_order_status, update_order_exchange_id, \
    update_order_info
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
        self._is_running = False
        self._initialized = True
        logger.info("LiveOrderExecutor initialized and monitoring thread started.")

    def execute_order(self, order_id: str, params={}):
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
            elif order['order_category'] == 'stop_loss' or order['order_category'] == 'take_profit':
                self._order_queue.put(exchange.create_conditional_order(order_id))
            logger.info(f"Order {order_id} is now executing.")
        except Exception as e:
            logger.exception("Error executing order %s: %s", order_id, e)
            raise

    def _monitor_executing_orders(self):
        """
        Background thread method that continuously monitors executing orders.
        """
        self._is_running = True
        while self._is_running:
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
                order_info = exchange.get_order_info(order['order_exchange_id'], order['symbol'])
                if order_info is None:
                    logger.error(f"Order {order_id} not found during monitoring.")
                    return


                update_order_info(order_id, executed_quantity=order_info['filled'], execution_summary={}, average_price=order_info['average'], total_fee=order_info['fee']['cost'])
                status = order_info['status']
                logger.debug(f"Order {order_id} status: {status}")
                logger.debug(order_info)
                timestamp_ms = order_info['lastUpdateTimestamp']
                executed_time = datetime.fromtimestamp(timestamp_ms / 1000) - timedelta(hours=3)
                if status == "closed":
                    update_order_status(order_id, "executed", executed_time)
                    add_event(order['event_manager_id'], "OrderExecutedEvent", 2, {"order_id": str(order_id), 'order_exchange_id': str(order['order_exchange_id']), "portfolio_id": str(order['portfolio_id']), 'symbol': order['symbol']})
                    logger.info(f"Order {order_id} executed.")
                elif status == "canceled" or status == "expired" or status == "rejected":
                    update_order_status(order_id, status, executed_time)
                    logger.warning(f"Order {order_id} {status}.")
                else:
                    self._order_queue.put(order_id)
            except Exception as e:
                logger.exception(f"Error while monitoring order: {e}")


    def stop(self):
        try:
            logger.info(f"LiveOrderExecutor is shutting down.")
            self._is_running = False
            self._order_queue.shutdown()
            self._monitor_thread.join()
            logger.info(f"LiveOrderExecutor stopped.")
        except Exception as e:
            logger.error(f"Error stopping LiveOrderExecutor: {e}")
