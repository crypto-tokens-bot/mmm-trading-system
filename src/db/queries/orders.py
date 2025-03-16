from src.db.db_connection import execute_query


def add_order(order_id, portfolio_id, event_manager_id, signal_id, order_type, order_category, order_side,
              order_status, base_currency, quote_currency, initial_quantity, target_price):
    """
    Inserts a new order into the orders table.

    :param order_id: UUID of the order.
    :param portfolio_id: UUID of the associated portfolio.
    :param event_manager_id: UUID of the event manager handling this order.
    :param signal_id: UUID of the signal that triggered this order.
    :param order_type: Type of order (limit, market, etc.).
    :param order_category: Order category (spot, futures, options).
    :param order_side: Buy or sell side.
    :param order_status: Status of the order (pending, executed, canceled).
    :param base_currency: Base currency of the order.
    :param quote_currency: Quote currency of the order.
    :param initial_quantity: Initial quantity of the order.
    :param target_price: Target execution price.
    """
    query = """
    INSERT INTO orders (order_id, portfolio_id, event_manager_id, signal_id, order_type, order_category, order_side, 
                        order_status, base_currency, quote_currency, initial_quantity, target_price, created_at)
    VALUES (%(order_id)s, %(portfolio_id)s, %(event_manager_id)s, %(signal_id)s, %(order_type)s, %(order_category)s,
            %(order_side)s, %(order_status)s, %(base_currency)s, %(quote_currency)s, %(initial_quantity)s, %(target_price)s, now())
    """
    execute_query(query, locals())


def get_order_by_id(order_id):
    """
    Retrieves an order from the database by order_id.

    :param order_id: UUID of the order to fetch.
    :return: Order details as a tuple.
    """
    query = "SELECT * FROM orders WHERE order_id = %(order_id)s"
    return execute_query(query, {"order_id": order_id})
