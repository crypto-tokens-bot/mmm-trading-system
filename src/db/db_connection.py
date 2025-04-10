import os

import clickhouse_connect
from dotenv import load_dotenv

load_dotenv()


def get_db_client():
    return clickhouse_connect.get_client(host=os.getenv("CLICKHOUSE_HOST", "localhost"),
                                         port=int(os.getenv("CLICKHOUSE_PORT", 8123)),
                                         user=os.getenv("CLICKHOUSE_USER", "user"),
                                         password=os.getenv("CLICKHOUSE_PASSWORD"))


def execute_query(query, params=None):
    """
    Executes an SQL query and returns results as a list of dictionaries.

    :param query: SQL query string.
    :param params: Dictionary of query parameters (optional).
    :return: List of dictionaries where each row is {column_name: value}.
    """
    # Execute query
    result = get_db_client().query(query, parameters=params)
    # Get column names
    column_names = result.column_names

    # Convert result to a list of dictionaries
    rows = result.result_rows
    dict_result = [dict(zip(column_names, row)) for row in rows]
    return dict_result
