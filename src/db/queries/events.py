from src.db.db_connection import execute_query

def add_event(event_id, event_manager_id, event_type, priority, payload):
    """
    Inserts a new event into the events table.

    :param event_id: UUID of the event.
    :param event_manager_id: UUID of the event manager handling this event.
    :param event_type: Type of event.
    :param priority: Priority of the event (integer).
    :param payload: JSON string containing event details.
    """
    query = """
    INSERT INTO events (event_id, event_manager_id, event_type, priority, payload, created_at)
    VALUES (%(event_id)s, %(event_manager_id)s, %(event_type)s, %(priority)s, %(payload)s, now())
    """
    execute_query(query, locals())

def get_event_by_id(event_id):
    """
    Retrieves an event from the database by event_id.

    :param event_id: UUID of the event.
    :return: Event details as a tuple.
    """
    query = "SELECT * FROM events WHERE event_id = %(event_id)s"
    return execute_query(query, {"event_id": event_id})
