import os
from dotenv import load_dotenv

load_dotenv()

CLICKHOUSE_CONFIG = {
    "host": os.getenv("CLICKHOUSE_HOST", "localhost"),
    "port": int(os.getenv("CLICKHOUSE_PORT", 8123)),
    "user": os.getenv("CLICKHOUSE_USER", "user"),
    "password": os.getenv("CLICKHOUSE_PASSWORD"),
}