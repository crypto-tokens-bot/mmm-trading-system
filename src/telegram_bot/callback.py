import re

from telebot.types import InputMediaPhoto

from src.tools.grafana import get_panel_png, DEFAULT_TEMPLATE_VARS
from src.config.logger_config import logger
from src.connectors.token_connector import get_balance, get_price
from src.db.queries.portfolios import get_all_portfolios, get_portfolio_by_id
from src.telegram_bot import keyboards, texts
from src.telegram_bot.keyboards import get_main_keyboard
from src.telegram_bot.texts import invalid_address, investment_info, choose_option


class TelegramBotCallback:
    def __init__(self, bot):
        self._bot = bot
        self.user_states = {}

    def process_data(self, call):
        if re.match(r'^my_investments', call.data):
            self._ask_wallet(call)
        elif re.match(r'^view_portfolios', call.data):
            self._get_portfolios(call)
        elif re.match(r'^select_portfolio_', call.data):
            portfolio_id = re.split(r'^select_portfolio_', call.data, maxsplit=1)[1]
            self._get_portfolio_info(call, portfolio_id)
        elif re.match(r'^back', call.data):
            self._process_back(call)

    def process_message(self, message):
        user_id = str(message.chat.id)
        if self.user_states[user_id] == "awaiting_wallet":
            self.user_states[user_id] = None
            self._get_wallet_info(user_id, message.text)

    def _ask_wallet(self, call):
        user_id = str(call.from_user.id)
        self.user_states[user_id] = "awaiting_wallet"
        self._bot.send_message(call.message.chat.id, text=texts.get_wallet_address())

    def _get_wallet_info(self, user_id, user_address):
        user_id = str(user_id)
        try:
            balance = get_balance(user_address)
            try:
                price = get_price()
            except Exception as e:
                logger.warning(f"No price value: {e}")
                price = 0
            self._bot.send_message(user_id, text=investment_info(user_address, balance, price),  parse_mode='Markdown',)
            self._bot.send_message(
                chat_id=user_id,
                text=texts.choose_option(),
                parse_mode='html',
                reply_markup=keyboards.get_main_keyboard(user_id)
            )
        except Exception:
            self._bot.send_message(user_id, text=invalid_address())
            self.user_states[user_id] = "awaiting_wallet"

    def cancel_action(self, id):
        self.user_states[str(id)] = None

    def _get_portfolios(self, call):
        user_id = str(call.from_user.id)
        portfolios = get_all_portfolios()
        self._bot.send_message(
            chat_id=user_id,
            text=texts.choose_option(),
            parse_mode='html',
            reply_markup=keyboards.get_portfolios(portfolios)
        )

    def _get_portfolio_info(self, call, portfolio_id):
        user_id = call.from_user.id
        chat_id = call.message.chat.id
        portfolio_info = get_portfolio_by_id(portfolio_id)
        try:
            media_group = []
            for panel_id in range(2, 5):
                png_data = get_panel_png(
                    panel_id=panel_id,
                    template_vars={
                        **DEFAULT_TEMPLATE_VARS,
                        "var-Portfolio": portfolio_info['portfolio_name']
                    }
                )

                if panel_id == 2:
                    media_group.append(InputMediaPhoto(
                        png_data,
                        caption=texts.get_portfolio_info(portfolio_info),
                        parse_mode="Markdown"
                    ))
                else:
                    media_group.append(InputMediaPhoto(png_data))

            self._bot.send_media_group(chat_id, media_group)

            # Показываем клавиатуру обратно после отправки
            self._get_portfolios(call)

        except RuntimeError as e:
            self._bot.send_message(chat_id, f"❌ Failed to load chart for {portfolio_info['portfolio_name']}.\n\n{e}")

    def _process_back(self, call):
        back_func = re.split(r'^back_', call.data, maxsplit=1)[1]
        user_id = str(call.from_user.id)
        if back_func == "menu":
            self._bot.edit_message_text(
                chat_id=user_id,
                message_id=call.message.message_id,
                text=choose_option(),
                reply_markup=get_main_keyboard(user_id)
            )


