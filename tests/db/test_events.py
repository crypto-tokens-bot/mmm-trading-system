import pytest
from src.db.queries.events import add_event, get_event_by_id
from uuid import uuid4

# Generate test UUIDs
TEST_EVENT_ID = uuid4()
TEST_EVENT_MANAGER_ID = uuid4()


def test_add_and_get_event():
    """Test inserting and retrieving an event from the database."""

    add_event(
        event_id=TEST_EVENT_ID,
        event_manager_id=TEST_EVENT_MANAGER_ID,
        event_type="trade_signal",
        priority=1,
        payload="{}"
    )

    event = get_event_by_id(TEST_EVENT_ID)

    # Validate event data
    assert event, "Event not found!"
    event = event[0]
    assert event["event_id"] == TEST_EVENT_ID, "Event ID does not match!"
    assert event["event_type"] == "trade_signal", "Event type does not match!"
    assert event["payload"] == "{}", "Event payload does not match!"
