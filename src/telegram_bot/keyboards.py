"""
Клавиатуры для сообщений.

"""

from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton

def menu_static():
    """
    Клавиатура со статичными кнопками внизу экрана.
    """
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    create_strategy_button = KeyboardButton(text="Strategy 📈")
    pnl_button = KeyboardButton(text="PnL 💲")
    keyboard.add(create_strategy_button, pnl_button)
    return keyboard


def strategy_actions():
    """
    Inline клавиатура с действиями над стратегиями.
    """
    create_strategy_button = InlineKeyboardButton(text="Create Strategy 🆕", callback_data='strategy_create_menu')
    all_strategies_button = InlineKeyboardButton(text="All Strategies 📋", callback_data='strategy_all')
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(create_strategy_button, all_strategies_button)
    return keyboard


def numbers(callback_prefix, count, custom_ids=None):
    """
    Создание кнопок с номерами.
    :param callback_prefix: Текст для callback.
    :param count: Количество кнопок.
    :return: List, содержащий 5 столбцов с кнопками.
    """
    columns = [[], [], [], [], []]
    ids = [str(i + 1) for i in range(count)]
    if custom_ids is not None:
        ids = custom_ids
    for i in range(count):
        button = InlineKeyboardButton(text=str(i + 1),
                                      callback_data=callback_prefix + ids[i])
        columns[i % 5].append(button)

    empty_button = InlineKeyboardButton(text=' ',
                                        callback_data='None')
    while count % 5 != 0:
        columns[count % 5].append(empty_button)
        count += 1

    return columns


def create_strategy():
    """
    Inline клавиатура для выбора типа стратегии.
    """
    try:
        keyboard = InlineKeyboardMarkup(row_width=5)
        back_button = InlineKeyboardButton(text='Back to Actions ⬅️',
                                           callback_data='strategy_back')
        keyboard.add(back_button)
        columns = numbers('strategy_create_type_', len(strategy.strategy_manager.strategies_types),
                          custom_ids=[str(key) for key in strategy.strategy_manager.strategies_types])

        for i in range(len(columns[0])):
            line = []
            for j in range(5):
                line.append(columns[j][i])
            keyboard.add(line[0], line[1], line[2], line[3], line[4])
        return keyboard
    except Exception as err:
        print(str(err))
        # admin.error(error_admin_text='Создание клавиатуры my_texts ' + str(err))
        return None

def create_strategy_type():
    """
    Inline клавиатура для возврата к видам стратегий.
    """
    try:
        keyboard = InlineKeyboardMarkup()
        back_button = InlineKeyboardButton(text='Back to strategy types ⬅️',
                                           callback_data='strategy_create_type_back')
        keyboard.add(back_button)
        return keyboard
    except Exception as err:
        print(str(err))
        # admin.error(error_admin_text='Создание клавиатуры my_texts ' + str(err))
        return None

def all_strategies(database):
    """
    Inline клавиатура для выбора созданной стратегии.
    """
    try:
        keyboard = InlineKeyboardMarkup(row_width=5)
        back_button = InlineKeyboardButton(text='Back to Actions ⬅️',
                                           callback_data='strategy_back')
        keyboard.add(back_button)

        query = f"""
                    SELECT strategyId
                    FROM strategies 
                    """
        data = database.execute_query(query)
        strategies = [el[0] for el in data]
        columns = numbers('strategy_entity_', len(data), strategies)
        for i in range(len(columns[0])):
            line = []
            for j in range(5):
                line.append(columns[j][i])
            keyboard.add(line[0], line[1], line[2], line[3], line[4])
        return keyboard
    except Exception as err:
        print(str(err))
        # admin.error(error_admin_text='Создание клавиатуры my_texts ' + str(err))
        return None


def strategy_info(strategy_id):
    """
    Информация о созданной стратегии.
    :param strategy_id: Id стратегии.
    """
    try:
        strategy_id = str(strategy_id)
        keyboard = InlineKeyboardMarkup()
        start = InlineKeyboardButton(text="START 📈",
                                     callback_data="strategy_start_" + strategy_id)
        stop = InlineKeyboardButton(text="STOP 🛑",
                                     callback_data="strategy_stop_" + strategy_id)
        update = InlineKeyboardButton(text="Update 🔄",
                                     callback_data="strategy_entity_" + strategy_id)
        delete = InlineKeyboardButton(text="Delete ❌️",
                                      callback_data="strategy_delete_" + strategy_id)
        back_button = InlineKeyboardButton(text='Back ⬅️',
                                           callback_data='strategy_all')
        keyboard.add(back_button)
        keyboard.add(start, stop)
        keyboard.add(update)
        keyboard.add(delete)
        return keyboard
    except Exception as err:
        str(err)
        # admin.error(error_admin_text='Не получилось создать клавиатуру ' + str(err))
        return None


def delete_strategy(strategy_id):
    """
    Подтверждение удаления стратегии.
    :param strategy_id: Id стратегии.
    """
    try:
        strategy_id = str(strategy_id)
        keyboard = InlineKeyboardMarkup()
        yes = InlineKeyboardButton(text="YES 👍",
                                     callback_data="strategy_delete_yes_" + strategy_id)
        no = InlineKeyboardButton(text="NO 👎",
                                     callback_data="strategy_entity_" + strategy_id)
        keyboard.add(no, yes)
        return keyboard
    except Exception as err:
        str(err)
        # admin.error(error_admin_text='Не получилось создать клавиатуру ' + str(err))
        return None