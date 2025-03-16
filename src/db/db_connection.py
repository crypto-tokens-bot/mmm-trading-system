import clickhouse_connect
from src.settings import CLICKHOUSE_CONFIG


def get_db_client():
    return clickhouse_connect.get_client(**CLICKHOUSE_CONFIG)


def execute_query(query, params=None):
    """
    Executes an SQL query and returns results as a list of dictionaries.

    :param query: SQL query string.
    :param params: Dictionary of query parameters (optional).
    :return: List of dictionaries where each row is {column_name: value}.
    """
    print(query, params)
    # Execute query
    result = get_db_client().query(query, parameters=params)
    # Get column names
    column_names = result.column_names

    # Convert result to a list of dictionaries
    rows = result.result_rows
    dict_result = [dict(zip(column_names, row)) for row in rows]
    return dict_result
