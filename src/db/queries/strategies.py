import uuid

from src.db.db_connection import execute_query

def add_strategy(event_manager_id, trading_pair, strategy_name, parameters):
    """
    Inserts a new strategy into the strategies table.

    :param event_manager_id: UUID of the event manager responsible for this strategy.
    :param trading_pair: Trading pair the strategy operates on (e.g., BTC/USDT).
    :param strategy_name: Name of the strategy.
    :param parameters: JSON string containing strategy parameters.
    """

    strategy_id = uuid.uuid4()
    query = """
    INSERT INTO strategies (strategy_id, event_manager_id, trading_pair, strategy_name, parameters, started_at)
    VALUES (%(strategy_id)s, %(event_manager_id)s, %(trading_pair)s, %(strategy_name)s, %(parameters)s, now())
    """
    execute_query(query, locals())
    return str(strategy_id)


def get_strategy_by_id(strategy_id):
    """
    Retrieves a strategy from the database by strategy_id.

    :param strategy_id: UUID of the strategy.
    :return: Strategy details as a tuple.
    """
    query = "SELECT * FROM strategies WHERE strategy_id = %(strategy_id)s"
    return execute_query(query, {"strategy_id": strategy_id})


def update_strategy_status(strategy_id, status):
    """
    Updates the status of the strategy in the database.

    :param strategy_id: UUID of the strategy.
    :param status: New status ("active" or "inactive").
    """
    query = """
    ALTER TABLE strategies 
    UPDATE status = %(status)s
    WHERE strategy_id = %(strategy_id)s
    """
    execute_query(query, {"strategy_id": strategy_id, "status": status})