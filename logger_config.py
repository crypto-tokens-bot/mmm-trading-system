import sys

from loki_logger_handler.loki_logger_handler import LokiLoggerHandler
from loki_logger_handler.formatters.loguru_formatter import LoguruFormatter
from loguru import logger
import os
from dotenv import load_dotenv

load_dotenv()

def setup_logger():
    # Создаем обработчик для Loki
    loki_handler = LokiLoggerHandler(
        url=os.getenv('LOKI_URL'),
        labels={"application": "MyApp", "env": "production"},
        label_keys={},
        timeout=10,
        default_formatter=LoguruFormatter(),
    )

    logger.configure(
        handlers=[
            {"sink": loki_handler, "serialize": True},
            {"sink": "app.log", "rotation": "10 MB"},
            {"sink": sys.stdout, "level": "DEBUG"},
        ]
    )

    return logger


logger = setup_logger()