import pytest
from src.db.queries.event_managers import add_event_manager, get_event_manager_by_id
from uuid import uuid4

# Generate test UUID
TEST_EVENT_MANAGER_ID = uuid4()

def test_add_and_get_event_manager():
    """Test inserting and retrieving an event manager from the database."""

    add_event_manager(
        event_manager_id=TEST_EVENT_MANAGER_ID,
        mode="live",
        status="active"
    )

    event_manager = get_event_manager_by_id(TEST_EVENT_MANAGER_ID)

    # Validate event manager data
    assert event_manager, "Event manager not found!"
    assert event_manager["event_manager_id"] == TEST_EVENT_MANAGER_ID, "Event manager ID does not match!"
    assert event_manager["mode"] == "live", "Mode does not match!"
    assert event_manager["status"] == "active", "Status does not match!"
