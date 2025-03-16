import threading
import time
from queue import Queue, Empty
from loguru import logger
from src.event import Event, EventType, Priority


class EventManager:
    """
    Manages events in separate queues by priority
    and processes them in a separate thread after start() is called.
    """

    # Common counter for all EventManager instances.
    _global_id_counter = 1

    def __init__(self):
        """
        Create a manager with queues for each priority level.
        """
        self._manager_id = f"EventManager-{EventManager._global_id_counter}"
        EventManager._global_id_counter += 1
        self._queues = {
            Priority.HIGH: Queue(),
            Priority.MEDIUM: Queue(),
            Priority.LOW: Queue()
        }
        self._stop_flag = threading.Event()
        self._thread = None

    def start(self):
        """
        Start the manager in a separate thread.

        :return: None
        """
        logger.info(f"[{self._manager_id}] Starting EventManager...")
        self._stop_flag.clear()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self):
        """
        Signal the manager to stop and wait for the thread to finish.

        :return: None
        """
        logger.info(f"[{self._manager_id}] Stopping EventManager...")
        self._stop_flag.set()
        if self._thread is not None:
            self._thread.join()
            logger.info(f"[{self._manager_id}] EventManager stopped.")

    def _run(self):
        """
        Main loop: continuously fetch and handle events until stopped.

        :return: None
        """
        logger.debug(f"[{self._manager_id}] EventManager main loop started.")
        while not self._stop_flag.is_set():
            event = self._get_next_event()
            if event:
                self._handle_event(event)
            else:
                time.sleep(0.01)
        logger.debug(f"[{self._manager_id}] EventManager main loop exited.")

    def _get_next_event(self) -> Event | None:
        """
        Get the first available event from the highest-priority non-empty queue.
        Return None if all queues are empty.

        :return: The next available event or None.
        :rtype: Event | None
        """
        for priority in [Priority.HIGH, Priority.MEDIUM, Priority.LOW]:
            try:
                event = self._queues[priority].get_nowait()
                logger.debug(
                    f"[{self._manager_id}] Fetched event '{event.get_event_id()}' "
                    f"from {priority.name} queue."
                )
                return event
            except Empty:
                pass
        return None

    def add_event(self, event: Event):
        """
        Add an event to the corresponding priority queue.

        :param event: The event to be added.
        :type event: Event
        :return: None
        """
        logger.debug(
            f"[{self._manager_id}] Adding event '{event.get_event_id()}' "
            f"to {event.get_priority().name} queue."
        )
        self._queues[event.get_priority()].put(event)

    def _handle_event(self, event: Event):
        """
        Handle the event based on its type.

        :param event: The event to handle.
        :type event: Event
        :return: None
        """
        logger.info(
            f"[{self._manager_id}] Handling event '{event.get_event_id()}' "
            f"(type={event.get_event_type().name}, priority={event.get_priority().name})"
        )

        if event.get_event_type() == EventType.MARKET:
            pass
        elif event.get_event_type() == EventType.ORDER:
            pass
        elif event.get_event_type() == EventType.SIGNAL:
            pass
        elif event.get_event_type() == EventType.ERROR:
            pass
        else:
            pass
