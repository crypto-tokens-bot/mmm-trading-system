import asyncio
import json
import re

from src.telegram_bot import keyboards, texts


class TelegramBotCallback:
    def __init__(self, bot):
        self._bot = bot

