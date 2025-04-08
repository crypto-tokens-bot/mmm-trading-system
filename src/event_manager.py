import json
import time
import threading
from logger_config import logger

from src.connectors.bybit_connector import BybitConnector
from src.db.queries.events import get_next_event, mark_event_as_processed
from src.db.queries.event_managers import add_event_manager, update_event_manager_status
from src.db.queries.strategy_subscriptions import add_strategy_subscription
from src.order_processing.live_order_executor import LiveOrderExecutor
from src.order_processing.order_controller import OrderController

class EventManager(threading.Thread):
    """
    Manages events by fetching them from the database,
    handling them, and marking them as processed.
    Runs in a separate thread.
    """

    def __init__(self, event_manager_id):
        """
        Initializes the EventManager with a unique ID.
        The status remains inactive until the EventManager is started.

        :param event_manager_id: Unique identifier for this event manager.
        """
        super().__init__()
        self.event_manager_id = event_manager_id
        self._order_controller = OrderController()
        bybit_exchange = BybitConnector(testnet=True)
        self._order_executor = LiveOrderExecutor(exchanges={'bybit': bybit_exchange})
        self.running = False
        self._strategy_subscriptions = {}

        logger.info(f"EventManager {self.event_manager_id} initialized.")

    def _get_next_event(self):
        """
        Retrieves the highest priority unprocessed event from the database.
        If multiple events have the same priority, the earliest one is selected.

        :return: Event data dictionary or None if no events are available.
        """
        try:
            event = get_next_event(self.event_manager_id)
            if event:
                logger.info(
                    f"EventManager {self.event_manager_id}: Fetched event {event['event_id']} with priority {event['priority']}")
            else:
                logger.info(f"EventManager {self.event_manager_id}: No unprocessed events found.")
            return event
        except Exception as e:
            logger.error(f"Error fetching next event for EventManager {self.event_manager_id}: {e}")
            return None

    def subscribe_portfolio_to_strategy(self, portfolio, strategy_id):
        """
        Subscribes a portfolio to a strategy: updates in-memory structure and database table.

        :param portfolio:
        :param strategy_id: ID of the strategy.
        """
        if strategy_id not in self._strategy_subscriptions:
            self._strategy_subscriptions[strategy_id] = []

        if portfolio.portfolio_id not in self._strategy_subscriptions[strategy_id]:
            self._strategy_subscriptions[strategy_id].append(portfolio)
            add_strategy_subscription(portfolio.portfolio_id, strategy_id)
            logger.info(f"Portfolio {portfolio.portfolio_id} subscribed to strategy {strategy_id}")
        else:
            logger.warning(f"Portfolio {portfolio.portfolio_id} is already subscribed to strategy {strategy_id}")

    def _handle_event(self, event):
        """
        Processes the given event and updates its status in the database.

        :param event: Dictionary containing event data.
        """
        if not event:
            return

        try:
            logger.info(
                f"EventManager {self.event_manager_id}: Handling event {event['event_id']} of type {event['event_type']}")
            if event['event_type'] == "OrderPlacementEvent":
                self._order_executor.execute_order(json.loads(event['payload'])['order_id'])
            elif event['event_type'] == "order":
                pass
            elif event['event_type'] == "SignalEvent":
                strategy_id = json.loads(event['payload'])['strategy_id']
                if not strategy_id:
                    logger.warning("SignalEvent missing strategy_id in payload")
                    return

                subscribed_portfolios = self._strategy_subscriptions[strategy_id]
                for portfolio in subscribed_portfolios:
                    try:
                        portfolio.handle_signal_event(event)
                    except Exception as e:
                        logger.error(f"Failed to notify portfolio {portfolio.portfolio_id}: {e}")
            elif event['event_type'] == "error":
                pass
            else:
                pass

            time.sleep(1)  # Simulate event processing

            # Mark the event as processed in the database
            mark_event_as_processed(event['event_id'])
            logger.info(f"EventManager {self.event_manager_id}: Event {event['event_id']} marked as processed.")
        except Exception as e:
            logger.error(f"Error processing event {event['event_id']} for EventManager {self.event_manager_id}: {e}")

    def start(self):
        """
        Starts the event manager by setting its status to active and running it in a separate thread.
        """
        try:
            update_event_manager_status(self.event_manager_id, "active")
            logger.info(f"EventManager {self.event_manager_id} is now active.")
            super().start()
        except Exception as e:
            logger.error(f"Error starting EventManager {self.event_manager_id}: {e}")

    def run(self):
        """
        Processes events in a loop until no more unprocessed events remain.
        """
        try:
            self.running = True
            logger.info(f"EventManager {self.event_manager_id} started processing events.")

            while self.running:
                event = self._get_next_event()
                if not event:
                    logger.info(f"EventManager {self.event_manager_id}: No more events to process. Waiting...")
                    time.sleep(3)
                else:
                    self._handle_event(event)

            update_event_manager_status(self.event_manager_id, "inactive")
            logger.info(f"EventManager {self.event_manager_id} stopped.")
        except Exception as e:
            logger.error(f"Error in run loop of EventManager {self.event_manager_id}: {e}")

    def stop(self):
        """
        Stops the event manager gracefully and updates its status in the database.
        """
        try:
            self.running = False

            logger.info(f"EventManager {self.event_manager_id} is shutting down.")
        except Exception as e:
            logger.error(f"Error stopping EventManager {self.event_manager_id}: {e}")


    @staticmethod
    def create_new(mode):
        """
        Creates a new EventManager instance in the database and returns the corresponding object.

        :param mode: The mode of operation for the EventManager (e.g., "live" or "simulated").
        :return: Instance of EventManager.
        """
        try:
            event_manager_id = add_event_manager(mode, "inactive")
            return EventManager(event_manager_id)
        except Exception as e:
            logger.error(f"Error creating new EventManager: {e}")
            return None