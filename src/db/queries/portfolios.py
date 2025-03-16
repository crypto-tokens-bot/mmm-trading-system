from src.db.db_connection import execute_query

def add_portfolio(portfolio_id, event_manager_id, risk_controller_id, portfolio_name, currency, initial_balance, exchange):
    """
    Inserts a new portfolio into the portfolios table.

    :param portfolio_id: UUID of the portfolio.
    :param event_manager_id: UUID of the associated event manager.
    :param risk_controller_id: UUID of the risk controller linked to this portfolio.
    :param portfolio_name: Name of the portfolio.
    :param currency: Currency in which the portfolio operates.
    :param initial_balance: Initial balance of the portfolio.
    :param exchange: Exchange where this portfolio operates.
    """
    query = """
    INSERT INTO portfolios (portfolio_id, event_manager_id, risk_controller_id, portfolio_name, currency, initial_balance, exchange)
    VALUES (%(portfolio_id)s, %(event_manager_id)s, %(risk_controller_id)s, %(portfolio_name)s, %(currency)s, %(initial_balance)s, %(exchange)s)
    """
    execute_query(query, locals())

def get_portfolio_by_id(portfolio_id):
    """
    Retrieves a portfolio by its portfolio_id.

    :param portfolio_id: UUID of the portfolio.
    :return: Portfolio details as a tuple.
    """
    query = "SELECT * FROM portfolios WHERE portfolio_id = %(portfolio_id)s"
    return execute_query(query, {"portfolio_id": portfolio_id})
