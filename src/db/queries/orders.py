import uuid

from src.db.db_connection import execute_query


def add_order(portfolio_id, event_manager_id, signal_id, order_type, order_category, order_side,
              order_status, symbol, base_currency, quote_currency, initial_quantity, target_price,
              parent_order_id=None):
    """
    Inserts a new order into the orders table.

    :param portfolio_id: UUID of the associated portfolio.
    :param event_manager_id: UUID of the event manager handling this order.
    :param signal_id: UUID of the signal that triggered this order.
    :param order_type: Type of order (limit, market, etc.).
    :param order_category: Order category (spot, futures, options).
    :param order_side: Buy or sell side.
    :param target_price: Target execution price.
    :param order_status: Status of the order (pending, executed, canceled).
    :param symbol Trading symbol (e.g., 'BTCUSD').
    :param base_currency: Base currency of the order.
    :param quote_currency: Quote currency of the order.
    :param initial_quantity: Initial quantity of the order.
    :param parent_order_id: UUID of the parent order.
    """

    order_id = uuid.uuid4()
    query = """
    INSERT INTO orders (order_id, portfolio_id, event_manager_id, parent_order_id, signal_id, order_type, order_category, order_side, 
                        target_price, order_status, symbol, base_currency, quote_currency, initial_quantity, created_at)
    VALUES (%(order_id)s, %(portfolio_id)s, %(event_manager_id)s, %(parent_order_id)s, %(signal_id)s, %(order_type)s, %(order_category)s,
            %(order_side)s, %(target_price)s, %(order_status)s, %(symbol)s, %(base_currency)s, %(quote_currency)s, %(initial_quantity)s, now())
    """
    execute_query(query, locals())
    return str(order_id)


def get_order_by_id(order_id):
    """
    Retrieves an order from the database by order_id.

    :param order_id: UUID of the order to fetch.
    :return: Order details as a tuple.
    """
    order_id = str(order_id)
    query = "SELECT * FROM orders WHERE order_id = %(order_id)s"
    return execute_query(query, {"order_id": order_id})


def update_order_status(order_id, status):
    """
        Updates the status and timestamps of an order.

        :param order_id: UUID of the order to update.
        :param status: New status of the order.
    """
    query = """
    ALTER TABLE orders 
    UPDATE 
        order_status = %(status)s,
        updated_at = now()
    WHERE order_id = %(order_id)s
    """
    execute_query(query, {"order_id": order_id, "status": status})


def get_executing_orders():
    query = """
    SELECT order_id 
    FROM orders 
    WHERE order_status = 'executing'
    """
    return execute_query(query)
