import json
import uuid

from src.db.db_connection import execute_query


def add_risk_controller(risk_model, stop_loss_coefficient, take_profit_coefficient,
                        max_asset_share):
    """
    Inserts a new risk controller into the risk_controllers table.

    :param risk_model: Type of risk model.
    :param stop_loss_coefficient: Stop-loss coefficient.
    :param take_profit_coefficient: Take-profit coefficient.
    :param max_asset_share: Maximum allowed share of an asset in the portfolio.
    """

    risk_controller_id = uuid.uuid4()
    query = """
    INSERT INTO risk_controllers (risk_controller_id, risk_model, stop_loss_coefficient, take_profit_coefficient, max_asset_share)
    VALUES (%(risk_controller_id)s, %(risk_model)s, %(stop_loss_coefficient)s, %(take_profit_coefficient)s, %(max_asset_share)s)
    """
    execute_query(query, locals())
    return str(risk_controller_id)


def get_risk_controller_by_id(risk_controller_id):
    """
    Retrieves a risk controller from the database by risk_controller_id.

    :param risk_controller_id: UUID of the risk controller.
    :return: Risk controller details as a tuple.
    """
    query = "SELECT * FROM risk_controllers WHERE risk_controller_id = %(risk_controller_id)s"
    return execute_query(query, {"risk_controller_id": risk_controller_id})
