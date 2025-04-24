"""
Тексты для сообщений.

"""
from datetime import datetime
import json
import texttable as table


def greeting():
    """
    Текст-приветствие.
    :return: Str.
    """
    text = 'Welcome to the <b>MMM Trading System</b>!'
    return text


def pnl(database, monitoring):
    """
    Информация об общем PnL.
    :param database: Клиент базы данных.
    :param monitoring: Экземпляр мониторинга.
    :return: Str.
    """
    try:
        query = f"""
                            SELECT strategyId, name, symbol
                            FROM strategies 
                            """
        data = database.execute_query(query)
        strategies = [(el[0], el[1], el[2]) for el in data]

        text = "<b>💵 Profit and Loss 💵</b>\n\n"
        pnl_table = table.Texttable()
        pnl_table.set_deco(table.Texttable.HEADER)
        pnl_table.set_cols_align(["l", "c", "c", "c", "c"])
        pnl_table.set_cols_valign(["m", "m", "m", "m", "m"])
        pnl_table.set_cols_dtype(['i', 't', "t", 'f', 'f'])
        pnl_table.add_row([" \n", "Name\n", "Symbol", "Assets\n", "P&L"])
        for i in range(len(strategies)):
            strategy_id, strategy_name, strategy_symbol = strategies[i]
            strategy_info = monitoring.calculate_pnl_by_strategy(strategy_id)
            pnl_table.add_row([i + 1, strategy_name, strategy_symbol, strategy_info['total_qty'], strategy_info['pnl']])
        text += '<code>' + pnl_table.draw() + '</code>'
        return text
    except Exception as err:
        print(err)
        return None


def choose_option():
    text = "Please choose an option from the menu below 👇"
    return text

def get_wallet_address():
    text = "📥 Please enter your wallet address:"
    return text

def invalid_address():
    text = (
        "🔴 Invalid address format.\n"
        "Please enter a valid wallet address.\n"
        "If you want to cancel this action, type /cancel."
    )
    return text

def investment_info(user_address, balance, price):
    text = (
        f"📊 *Your Investment Info*\n\n"
        f"👛 *Wallet:* `{user_address}`\n"
        f"💰 *Token Balance:* {balance:.4f} MMM\n"
        f"💵 *Current Price:* 1 MMM = {price:.4f} USDT\n\n"
        f"🧮 *Estimated Value:* ~ {balance * price:.2f} USDT"
    )
    return text


def choose_portfolio():
    text = "📁 Please select a portfolio:"
    return text


def get_portfolio_info(portfolio_info):
    text = f"📈 Portfolio: *{portfolio_info['portfolio_name']}*"
    return text