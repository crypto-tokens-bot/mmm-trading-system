from src.db.db_connection import execute_query

def add_strategy_subscription(portfolio_id, strategy_id):
    """
    Inserts a new subscription into the strategy_subscriptions table.

    :param portfolio_id: UUID of the portfolio subscribing to the strategy.
    :param strategy_id: UUID of the strategy being subscribed to.
    """
    query = """
    INSERT INTO strategy_subscriptions (portfolio_id, strategy_id)
    VALUES (%(portfolio_id)s, %(strategy_id)s)
    """
    execute_query(query, locals())

def get_subscriptions_by_portfolio(portfolio_id):
    """
    Retrieves all strategies subscribed by a given portfolio.

    :param portfolio_id: UUID of the portfolio.
    :return: List of subscribed strategies.
    """
    query = "SELECT * FROM strategy_subscriptions WHERE portfolio_id = %(portfolio_id)s"
    return execute_query(query, {"portfolio_id": portfolio_id})
