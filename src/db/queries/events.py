import uuid

from src.db.db_connection import execute_query

def add_event(event_manager_id, event_type, priority, payload, event_id=uuid.uuid4()):
    """
    Inserts a new event into the events table.

    :param event_manager_id: UUID of the event manager handling this event.
    :param event_type: Type of event.
    :param priority: Priority of the event (integer).
    :param payload: JSON string containing event details.
    :param event_id: UUID of the event.

    :return: event_id.
    """

    event_id = uuid.uuid4()
    query = """
    INSERT INTO events (event_id, event_manager_id, event_type, priority, payload, created_at)
    VALUES (%(event_id)s, %(event_manager_id)s, %(event_type)s, %(priority)s, %(payload)s, now())
    """
    execute_query(query, locals())
    return str(event_id)

def get_event_by_id(event_id):
    """
    Retrieves an event from the database by event_id.

    :param event_id: UUID of the event.

    """
    query = "SELECT * FROM events WHERE event_id = %(event_id)s"
    return execute_query(query, {"event_id": event_id})


def get_next_event(event_manager_id):
    """
    Fetches the highest priority unprocessed event from the database.
    If multiple events have the same priority, returns the earliest one.

    :return: Dictionary containing event details or None if no events found.
    """
    query = """
    SELECT event_id, event_manager_id, event_type, priority, payload, created_at
    FROM events
    WHERE event_manager_id = %(event_manager_id)s AND executed_at IS NULL
    ORDER BY priority DESC, created_at ASC
    LIMIT 1
    """
    result = execute_query(query, {"event_manager_id": event_manager_id})
    return result[0] if result else None


def mark_event_as_processed(event_id):
    """
    Marks an event as processed by updating the executed_at timestamp.

    :param event_id: UUID of the processed event.
    """
    query = """
    ALTER TABLE events 
    UPDATE executed_at = now()
    WHERE event_id = %(event_id)s
    """
    execute_query(query, {"event_id": event_id})