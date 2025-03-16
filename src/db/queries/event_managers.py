from src.db.db_connection import execute_query

def add_event_manager(event_manager_id, mode, status):
    """
    Inserts a new event manager into the eventmanager table.

    :param event_manager_id: UUID of the event manager.
    :param mode: Operation mode (live/simulated).
    :param status: Current status of the event manager.
    """
    query = """
    INSERT INTO event_managers (event_manager_id, mode, status)
    VALUES (%(event_manager_id)s, %(mode)s, %(status)s)
    """
    execute_query(query, locals())

def get_event_manager_by_id(event_manager_id):
    """
    Retrieves an event manager from the database by event_manager_id.

    :param event_manager_id: UUID of the event manager.
    :return: Event manager details as a tuple.
    """
    query = "SELECT * FROM event_managers WHERE event_manager_id = %(event_manager_id)s"
    return execute_query(query, {"event_manager_id": event_manager_id})[0]


def update_event_manager_status(event_manager_id, status):
    """
    Updates the status of the event manager in the database.

    :param event_manager_id: UUID of the event manager.
    :param status: New status ("active" or "inactive").
    """
    query = """
    ALTER TABLE event_managers 
    UPDATE status = %(status)s
    WHERE event_manager_id = %(event_manager_id)s
    """
    execute_query(query, {"event_manager_id": event_manager_id, "status": status})
