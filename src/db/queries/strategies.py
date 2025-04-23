import uuid

from src.db.db_connection import execute_query

def add_strategy(event_manager_id, trading_pair, strategy_name, strategy_type, parameters):
    """
    Inserts a new strategy into the strategies table.

    :param event_manager_id: UUID of the event manager responsible for this strategy.
    :param trading_pair: Trading pair the strategy operates on (e.g., BTC/USDT).
    :param strategy_name: Name of the strategy.
    :param parameters: JSON string containing strategy parameters.
    """

    strategy_id = uuid.uuid4()
    query = """
    INSERT INTO strategies (strategy_id, event_manager_id, trading_pair, strategy_name, strategy_type, parameters)
    VALUES (%(strategy_id)s, %(event_manager_id)s, %(trading_pair)s, %(strategy_name)s, %(strategy_type)s, %(parameters)s)
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
    result = execute_query(query, locals())
    if result is None:
        return None
    return result[0]


def get_strategies_by_event_manager_id(event_manager_id):
    """
    Fetch all strategies that belong to the specified event manager.

    :param event_manager_id: UUID of the event manager.
    :return: List of strategy rows (each row is typically a dict) or an empty list.
    """
    query = """
        SELECT *
        FROM strategies
        WHERE event_manager_id = %(event_manager_id)s
    """
    return execute_query(query, {"event_manager_id": event_manager_id}) or []


def get_all_strategies():
    query = "SELECT * FROM strategies"
    return execute_query(query)


def delete_strategy(strategy_id):
    """
    Deletes a strategy from the strategies table.

    :param strategy_id: UUID of the strategy to delete.
    """
    query = """
    DELETE FROM strategies
    WHERE strategy_id = %(strategy_id)s
    """
    execute_query(query, {'strategy_id': strategy_id})