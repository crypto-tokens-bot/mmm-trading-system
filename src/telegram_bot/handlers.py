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
            logger.info(f"Got start command {message.text} from {message.chat.id}")
            if message.chat.type == "private" and message.text == '/start':
                self._bot.send_message(
                    chat_id=message.chat.id,
                    text=texts.greeting(),
                    parse_mode='html',
                    reply_markup=keyboards.get_reply_keyboard()
                )
                self._bot.send_message(
                    chat_id=message.chat.id,
                    text=texts.choose_option(),
                    parse_mode='html',
                    reply_markup=keyboards.get_main_keyboard(message.chat.id)
                )
                logger.info("Sent greeting to %s", message.chat.id)

        @self._bot.message_handler(func=lambda msg: msg.text == "📋 Menu" or msg.text == "/cancel")
        def show_main_menu(message):
            self.callback.cancel_action(message.chat.id)
            self._bot.send_message(
                chat_id=message.chat.id,
                text=texts.choose_option(),
                parse_mode='html',
                reply_markup=keyboards.get_main_keyboard(message.chat.id)
            )

        @self._bot.message_handler(content_types=["text"])
        def continue_chat(message):
            logger.info(f"Got text {message.text} from {message.chat.id}")
            if message.chat.type == "private":
                user_id = str(message.chat.id)
                if user_id in self.callback.user_states and self.callback.user_states[user_id] is not None:
                    self.callback.process_message(message)
                else:
                    self._bot.send_message(
                        chat_id=message.chat.id,
                        text=texts.choose_option(),
                        parse_mode='html',
                        reply_markup=keyboards.get_main_keyboard(message.chat.id)
                    )

        @self._bot.callback_query_handler(func=lambda call: True)
        def callback_text(call):
            logger.info(f"Got callback {call.data} from {call.from_user.id}")
            self.callback.process_data(call)


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
