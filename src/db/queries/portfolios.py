import uuid

from src.db.db_connection import execute_query, to_map_literal


def add_portfolio(event_manager_id, risk_controller_id, portfolio_name, managed_assets, currency, initial_balance, exchange):
    """
    Inserts a new portfolio into the portfolios table.

    :param event_manager_id: UUID of the associated event manager.
    :param risk_controller_id: UUID of the risk controller linked to this portfolio.
    :param portfolio_name: Name of the portfolio.
    :param managed_assets: Dict of managed assets.
    :param currency: Currency in which the portfolio operates.
    :param initial_balance: Initial balance of the portfolio.
    :param exchange: Exchange where this portfolio operates.
    """

    portfolio_id = uuid.uuid4()
    query = """
    INSERT INTO portfolios (portfolio_id, event_manager_id, risk_controller_id, portfolio_name, managed_assets, currency, initial_balance, exchange)
    VALUES (%(portfolio_id)s, %(event_manager_id)s, %(risk_controller_id)s, %(portfolio_name)s, %(managed_assets)s, %(currency)s, %(initial_balance)s, %(exchange)s)
    """
    params = locals()
    params['managed_assets'] = to_map_literal(managed_assets)
    execute_query(query, params)
    return str(portfolio_id)


def get_portfolio_by_id(portfolio_id):
    """
    Retrieves a portfolio by its portfolio_id.

    :param portfolio_id: UUID of the portfolio.
    :return: Portfolio details as a tuple.
    """
    query = "SELECT * FROM portfolios WHERE portfolio_id = %(portfolio_id)s"
    result = execute_query(query,{"portfolio_id": portfolio_id})
    if result is None:
        return None
    return result[0]

def get_portfolios_by_event_manager_id(event_manager_id):
    """
    Fetch all portfolios that belong to the specified event manager.

    :param event_manager_id: UUID of the event manager.
    :return: List of portfolio rows (each row is usually a dict) or an empty list.
    """
    query = """
        SELECT *
        FROM portfolios
        WHERE event_manager_id = %(event_manager_id)s
    """
    return execute_query(query, {"event_manager_id": event_manager_id}) or []


def get_all_portfolios_ids():
    """
    Retrieves portfolios ids.
    :return: List of portfolios ids.
    """
    query = "SELECT portfolio_id FROM portfolios"
    return execute_query(query)


def get_all_portfolios():
    """
    Retrieves portfolios.
    :return: List of portfolios.
    """
    query = "SELECT * FROM portfolios"
    return execute_query(query)


def delete_portfolio(portfolio_id):
    """
    Deletes a portfolio from the portfolios table.

    :param portfolio_id: UUID of the portfolio to delete.
    """
    query = """
    DELETE FROM portfolios
    WHERE portfolio_id = %(portfolio_id)s
    """
    execute_query(query, {'portfolio_id': portfolio_id})


def update_portfolio_status(portfolio_id, has_executing_order):
    """
        Updates the status and timestamps of an order.

        :param portfolio_id:  UUID of the portfolio.
        :param has_executing_order: New status of the portfolio.
    """
    query = """
        ALTER TABLE portfolios 
        UPDATE 
            has_executing_order = %(has_executing_order)s
        WHERE portfolio_id = %(portfolio_id)s
        """

    execute_query(query, {"portfolio_id": portfolio_id, "has_executing_order": has_executing_order})


def update_managed_assets(portfolio_id, managed_assets):
    """
    Updates the managed_assets of a portfolio.

    :param portfolio_id: UUID of the portfolio.
    :param managed_assets: Dictionary of updated managed assets.
    """
    managed_assets = to_map_literal(managed_assets, update_request=True)
    query = f"""
        ALTER TABLE portfolios 
        UPDATE 
            managed_assets = {managed_assets}
        WHERE portfolio_id = %(portfolio_id)s
    """
    execute_query(query, {"portfolio_id": portfolio_id})

def update_portfolio_prices(portfolio_id, current_prices):
    """
    Updates the current_prices of a portfolio.

    :param portfolio_id: UUID of the portfolio.
    :param current_prices: Dictionary of updated current prices.
    """
    current_prices = to_map_literal(current_prices, update_request=True)
    query = f"""
        ALTER TABLE portfolios 
        UPDATE 
            current_prices = {current_prices}
        WHERE portfolio_id = %(portfolio_id)s
    """
    execute_query(query, {"portfolio_id": portfolio_id})