import clickhouse_connect
from src.settings import CLICKHOUSE_CONFIG

def get_db_client():
    return clickhouse_connect.get_client(**CLICKHOUSE_CONFIG)

def execute_query(query, params=None):
    client = get_db_client()
    result = client.query(query, parameters=params)
    return result.result_rows

def execute_write_query(query, params=None):
    client = get_db_client()
    client.command(query, parameters=params)
