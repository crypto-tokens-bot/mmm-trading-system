import threading
import time
import pytest
from src.event import Event, EventType, Priority
from src.event_manager import EventManager
import random


def test_event_manager_run_and_stop():
    """
    Test that EventManager can start and stop cleanly
    in a separate thread without errors.
    """
    manager = EventManager()
    manager.start()
    time.sleep(0.1)
    manager.stop()
    assert True


def test_event_manager_priority_order():
    """
    Test that higher priority events are fetched and handled
    before lower priority ones.
    """
    processed_events = []

    class TestEventManager(EventManager):
        def _handle_event(self, event: Event):
            processed_events.append(event.get_priority().name)
            super()._handle_event(event)

    manager = TestEventManager()
    manager.start()

    manager.add_event(Event(EventType.MARKET, Priority.LOW))
    manager.add_event(Event(EventType.SIGNAL, Priority.MEDIUM))
    manager.add_event(Event(EventType.ORDER, Priority.HIGH))
    manager.add_event(Event(EventType.SIGNAL, Priority.MEDIUM))

    time.sleep(0.5)
    manager.stop()

    assert processed_events == ["HIGH", "MEDIUM", "MEDIUM", "LOW"], (
        f"Unexpected order of priorities: {processed_events}"
    )


@pytest.mark.parametrize("num_events", [10, 50, 100])
def test_event_manager_multiple_events(num_events):
    """
    Test handling multiple events to ensure stability with
    different volumes of events.
    """
    processed_events = []

    class TestEventManager(EventManager):
        def _handle_event(self, event: Event):
            processed_events.append(event.get_priority().name)
            super()._handle_event(event)

    manager = TestEventManager()
    manager.start()

    for i in range(num_events):
        if i % 3 == 0:
            priority = Priority.HIGH
        elif i % 3 == 1:
            priority = Priority.MEDIUM
        else:
            priority = Priority.LOW
        manager.add_event(Event(EventType.MARKET, priority))

    time.sleep(1.0)
    manager.stop()

    assert len(processed_events) == num_events, (
        f"Expected {num_events} processed events, got {len(processed_events)}"
    )


def test_multiple_managers_parallel():
    """
    Test running multiple EventManagers in parallel threads.
    Each manager processes its own queue of events independently.
    """

    class TestEventManager(EventManager):
        def __init__(self):
            super().__init__()
            self._processed_events = []

        def _handle_event(self, event: Event):
            self._processed_events.append(event.get_event_id())
            super()._handle_event(event)

    manager1 = TestEventManager()
    manager2 = TestEventManager()

    manager1.start()
    manager2.start()

    def worker(total_events: int):
        for i in range(total_events):
            priority = random.choice([Priority.HIGH, Priority.MEDIUM, Priority.LOW])
            event = Event(EventType.ORDER, priority)

            if random.random() < 0.5:
                manager1.add_event(event)
            else:
                manager2.add_event(event)

            time.sleep(random.uniform(0.0, 0.01))

    num_workers = 3
    events_per_worker = 10
    total_expected_events = num_workers * events_per_worker
    threads = []
    for _ in range(num_workers):
        t = threading.Thread(target=worker, args=(events_per_worker,))
        t.start()
        threads.append(t)

    for t in threads:
        t.join()

    time.sleep(1)

    manager1.stop()
    manager2.stop()

    total_processed = len(manager1._processed_events) + len(manager2._processed_events)

    assert total_processed == total_expected_events, (
        f"Expected {total_expected_events} total events processed, got {total_processed}"
    )