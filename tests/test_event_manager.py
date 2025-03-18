import threading
import time
from uuid import uuid4

from src.event_manager import EventManager
from src.db.queries.event_managers import add_event_manager, get_event_manager_by_id
from src.db.queries.events import get_next_event, add_event

def test_add_event_manager():
    """ Test the creation of an EventManager and validate its initial status. """
    event_manager = EventManager.create_new("test")

    # Check that the event manager is inactive before starting
    db_event_manager = get_event_manager_by_id(event_manager.event_manager_id)
    assert db_event_manager["status"] == "inactive"
    assert db_event_manager["event_manager_id"] == event_manager.event_manager_id

    event_manager.start()
    time.sleep(1)
    db_event_manager = get_event_manager_by_id(event_manager.event_manager_id)
    assert db_event_manager["status"] == "active"


    time.sleep(1)
    event_manager.stop()
    event_manager.join()
    db_event_manager = get_event_manager_by_id(event_manager.event_manager_id)
    assert db_event_manager["status"] == "inactive"


def test_event_processing_multiple_events():
    """ Test the processing of multiple events and ensure they are marked as processed. """
    event_manager = EventManager.create_new("test")
    event_manager.start()
    # Insert multiple test events
    for i in range(3):
        add_event(
            event_manager_id=event_manager.event_manager_id,
            event_type="ORDER_FILLED",
            priority=i,
            payload="{}"
        )

    time.sleep(8)

    for i in range(3):
        event = get_next_event(event_manager.event_manager_id)
        assert event is None, f"Event test-event-{i} was not processed!"

    event_manager.stop()
    event_manager.join()


def test_multiple_event_managers():
    """ Test running multiple EventManagers concurrently with different event sets. """
    event_managers = [EventManager.create_new("test1"), EventManager.create_new("test2")]

    # Assign events to different managers
    for manager in event_managers:
        for j in range(2):
            add_event(
                event_manager_id=manager.event_manager_id,
                event_type="ORDER_FILLED",
                priority=j,
                payload="{j}"
            )

    # Start all event managers
    for manager in event_managers:
        manager.start()

    time.sleep(6)  # Wait for events to be processed

    # Check that all events are processed
    for manager in event_managers:
        for j in range(2):
            event = get_next_event(manager.event_manager_id)
            assert event is None, f"Event {manager.event_manager_id}-{j} was not processed!"

    # Stop all event managers
    for manager in event_managers:
        manager.stop()
        manager.join()
