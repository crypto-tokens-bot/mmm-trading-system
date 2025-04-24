import re
import os
import time
from threading import Thread

import telebot
from dotenv import load_dotenv

from src.config.logger_config import logger
from src.telegram_bot import keyboards, texts
from src.telegram_bot.callback import TelegramBotCallback

load_dotenv()

class TelegramBotHandlers(Thread):
    def __init__(self):
        super().__init__(daemon=True)
        logger.info("Initializing TelegramBotHandlers")
        self._bot = telebot.TeleBot(os.getenv('TELEGRAM_TOKEN'))
        self.callback = TelegramBotCallback(self._bot)

        @self._bot.message_handler(commands=["start", "help"])
        def start_chat(message):
            logger.info("Got command %r from %s", message.text, message.chat.id)
            if message.chat.type == "private" and message.text == '/start':
                self._bot.send_message(
                    chat_id=message.chat.id,
                    text=texts.greeting(),
                    parse_mode='html',
                    reply_markup=keyboards.menu_static()
                )
                logger.info("Sent greeting to %s", message.chat.id)

        @self._bot.message_handler(content_types=["text"])
        def continue_chat(message):
            logger.info("Got text %r from %s", message.text, message.chat.id)
            if message.chat.type == "private" and message.text == 'PnL 💲':

                self._bot.send_message(
                    chat_id=message.chat.id,
                    text=texts.pnl(),
                    parse_mode='html'
                )
                logger.info("Sent PnL info to %s", message.chat.id)

        @self._bot.callback_query_handler(func=lambda call: True)
        def callback_text(call):
            logger.info("Got callback %r from %s", call.data, call.from_user.id)
            if re.match(r'^strategy', call.data):
                logger.info("Handling strategy callback %r", call.data)
                # ... your logic ...

    def run(self):
        logger.info("Starting polling loop")
        self._bot.polling(non_stop=True)

    def stop(self):
        logger.info("Stopping bot")
        try:
            self._bot.stop_bot()
            logger.info("Called stop bot")
        except AttributeError:
            logger.warning("stop_bot() unavailable in this version")
