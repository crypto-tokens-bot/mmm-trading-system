"""
Клавиатуры для сообщений.

"""
import os

from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup


def is_admin(user_id: int) -> bool:
    admins = os.getenv("ADMINS", "")
    admin_ids = [int(uid.strip()) for uid in admins.split(",") if uid.strip().isdigit()]
    return user_id in admin_ids


def get_main_keyboard(user_id):
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        InlineKeyboardButton("💼 My Investments", callback_data="my_investments"),
    )

    if is_admin(user_id):
        keyboard.add(
            InlineKeyboardButton("📁 Portfolios Info", callback_data="view_portfolios")
        )

    return keyboard

def get_reply_keyboard():
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(KeyboardButton("📋 Menu"))
    return keyboard


def get_portfolios(portfolios):
    keyboard = InlineKeyboardMarkup(row_width=1)
    for p in portfolios:
        keyboard.add(
            InlineKeyboardButton(
                text=p['portfolio_name'],
                callback_data=f"select_portfolio_{p['portfolio_id']}"
            )
        )

    keyboard.add(InlineKeyboardButton("🔙 Back", callback_data="back_menu"))
    return keyboard