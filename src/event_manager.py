import json
import time
import threading
from src.config.logger_config import logger

from src.connectors.bybit_connector import BybitConnector
from src.db.queries.events import get_next_event, mark_event_as_processed
from src.db.queries.event_managers import add_event_manager, update_event_manager_status, get_event_manager_by_id
from src.db.queries.portfolios import get_portfolio_by_id
from src.db.queries.strategy_subscriptions import add_strategy_subscription
from src.order_processing.live_order_executor import LiveOrderExecutor
from src.order_processing.order_controller import OrderController
from src.order_processing.simulated_order_executor import SimulatedOrderExecutor
from src.portfolio import Portfolio


class EventManager(threading.Thread):
    """
    Manages events by fetching them from the database,
    handling them, and marking them as processed.
    Runs in a separate thread.
    """

    def __init__(self, event_manager_id, mode):
        """
        Initializes the EventManager with a unique ID.
        The status remains inactive until the EventManager is started.

        :param event_manager_id: Unique identifier for this event manager.
        """
        super().__init__()
        self.event_manager_id = event_manager_id
        self._order_controller = OrderController()
        self._mode = mode
        bybit_exchange = BybitConnector(testnet=True)
        self.running = False
        self._strategy_subscriptions = {}
        self._order_executor = LiveOrderExecutor(exchanges={'bybit': bybit_exchange}) if mode == "live" else SimulatedOrderExecutor(slippage_model=SimulatedOrderExecutor.SlippageModel(), fee_model=SimulatedOrderExecutor.FeeModel(), event_manager=self)

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
                self._order_executor.execute_order(event['payload']['order_id'], event['payload'])
            elif event['event_type'] == "OrderExecutedEvent":
                portfolio = Portfolio.load_by_id(str(event['payload']['portfolio_id']))
                portfolio.handle_order_executed_event(event)
            elif event['event_type'] == "SignalEvent":
                strategy_id = event['payload']['strategy_id']
                if not strategy_id:
                    logger.warning("SignalEvent missing strategy_id in payload")
                    return
                subscribed_portfolios = self._strategy_subscriptions.get(strategy_id, [])
                for portfolio in subscribed_portfolios:
                    try:
                        portfolio_info = get_portfolio_by_id(portfolio.portfolio_id)
                        if not portfolio_info['has_executing_order']:
                            portfolio.handle_signal_event(event)
                        else:
                            logger.info(f"Signal ignored for portfolio {portfolio.portfolio_id}.")
                    except Exception as e:
                        logger.error(f"Failed to notify portfolio {portfolio.portfolio_id}: {e}")
            else:
                pass

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

            while True:
                event = self._get_next_event()
                if not event:
                    if not self.running:
                        break
                    # logger.info(f"EventManager {self.event_manager_id}: No more events to process. Waiting...")
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
    def from_id(event_manager_id: str):
        try:
            # Retrieve the persisted row; expected to expose `id` and `mode` fields
            event_manager = get_event_manager_by_id(event_manager_id)

            if event_manager is None:
                logger.error(f"EventManager with id {event_manager_id} not found")
                return None

            return EventManager(event_manager_id=event_manager['event_manager_id'], mode=event_manager['mode'])
        except Exception as exc:
            logger.exception(f"Failed to initialise EventManager for id {event_manager_id}: {exc}")
            return None