import pytest
from src.db.queries.events import add_event, get_event_by_id
from uuid import uuid4

# Generate test UUID
TEST_EVENT_MANAGER_ID = uuid4()


def test_add_and_get_event():
    """Test inserting and retrieving an event from the database."""

    event_id = add_event(
        event_manager_id=TEST_EVENT_MANAGER_ID,
        event_type="trade_signal",
        priority=1,
        payload="{}"
    )

    event = get_event_by_id(event_id)

    # Validate event data
    assert event, "Event not found!"
    event = event[0]
    assert event["event_id"] == event_id, "Event ID does not match!"
    assert event["event_type"] == "trade_signal", "Event type does not match!"
    assert event["payload"] == "{}", "Event payload does not match!"