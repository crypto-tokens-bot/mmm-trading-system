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


def strategy_actions():
    """
    Действия со стратегиями.
    :return: Str.
    """
    text = '<b>Choose an action:</b>\n'
    return text


def create_strategy():
    """
    Создание стратегии.
    :return: Str.
    """
    text = '<b>Select a strategy type from the following:</b>\n'
    num = 1
    text += '<code>'
    for type in strategy.strategy_manager.strategies_types:
        text += str(num) + ". " + type + '\n'
        num += 1
    text += '</code>'

    return text


def create_strategy_type(type):
    """
    Вывод сообщения для создания определённой стратегии.
    :param type Тип создаваемой стратегии.
    :return: Str.
    """
    text = '<b>To create a strategy, send the following message with modified parameters:</b>\n'
    text += '<pre>'
    text += f"#CREATE_STRATEGY\n"
    text += json.dumps(strategy.strategy_manager.strategies_types[type], indent=4)
    text += '</pre>'
    return text


def all_strategies(database):
    """
    Вывод всех созданных стратегий.
    :return: Str.
    """
    try:
        text = '<b>Select a strategy from the following:</b>\n'
        query = f"""
                SELECT 
                    name, type
                FROM strategies 
                """
        data = database.execute_query(query)
        strategies_table = table.Texttable()
        strategies_table.set_deco(table.Texttable.HEADER)
        strategies_table.set_cols_align(["l", "c", "c"])
        strategies_table.set_cols_valign(["m", "m", "m"])
        strategies_table.set_cols_dtype(['i', 't', 't'])
        strategies_table.add_row([" \n", "Name\n", "Type\n"])
        for i in range(len(data)):
            strategies_table.add_row([i + 1, data[i][0], data[i][1]])
        text += '<code>' + strategies_table.draw() + '</code>'
        return text
    except Exception as err:
        print(str(err))
        return None


def strategy_info(database, monitoring, strategy_id):
    """
    Информация о созданной стратегии.
    :param database: Клиент базы данных.
    :param monitoring: Экземпляр мониторинга.
    :param strategy_id: Id стратегии.
    :return: Str.
    """
    try:
        query = f"""
                SELECT 
                    *
                FROM strategies 
                WHERE strategyId == '{strategy_id}'
                """
        data = database.execute_query(query, columns=True)
        text = ""
        if data is None:
            text = 'Sorry, something went wrong.'
            return text
        strategy_data = data[0]
        text = '<b>🔹 Strategy Details 🔹</b>\n\n'
        text += '<b>Title:</b> <i>' + strategy_data['name'] + '</i>\n'
        text += '<b>Type:</b> <i>' + strategy_data['type'] + '</i>\n'
        text += '<b>Exchange:</b> <i>' + strategy_data['exchange'] + '</i>\n'
        text += '<b>Symbol:</b> <i>' + strategy_data['symbol'] + '</i>\n'
        text += '<b>Balance:</b> <i>' + str(round(strategy_data['balance'], 5)) + '</i>\n'
        text += '<b>Assets Number:</b> <i>' + str(round(strategy_data['assetsNumber'], 5)) + '</i>\n'
        text += '<b>Status:</b> <i>' + ('launched' if strategy_data['status'] else 'stopped') + '</i>\n'
        text += '<b>Created:</b> <i>' + str(strategy_data['createdTime']) + '</i>\n'
        text += '<b>PnL:</b> <i>' + str(monitoring.calculate_pnl_by_strategy(strategy_id)['pnl']) + '</i>\n'
        text += '\n<i>Current time:</i> <i>' + str(datetime.now().strftime("%Y-%m-%d %H:%M:%S")) + '</i>\n'
        return text
    except Exception as err:
        print(err)
        # admin.error(error_admin_text='Не получилось содздать описание текста' + str(err))
        return None


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


def delete_strategy():
    """
       Запрос на подтверждение удаления стратегии.
       :return: Str.
       """
    try:
        text = '<b>Confirm delete</b>\n'
        return text
    except Exception as err:
        print(str(err))
        return None
