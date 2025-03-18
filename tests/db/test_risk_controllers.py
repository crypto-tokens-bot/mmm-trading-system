import json

import pytest
from src.db.queries.risk_controllers import add_risk_controller, get_risk_controller_by_id
from uuid import uuid4
from decimal import Decimal


def test_add_and_get_risk_controller():
    """Test inserting and retrieving a risk controller from the database."""

    risk_controller_id = add_risk_controller(
        risk_model="default",
        stop_loss_coefficient=0.05,
        take_profit_coefficient=0.10,
        max_asset_share=(['BTC', 'USDT'], [0.25, 0.75])
    )

    risk_controller = get_risk_controller_by_id(risk_controller_id)

    # Validate risk controller data
    assert risk_controller, "Risk controller not found!"
    risk_controller = risk_controller[0]
    assert risk_controller["risk_controller_id"] == risk_controller_id, "Risk controller ID does not match!"
    assert risk_controller["risk_model"] == "default", "Risk model does not match!"
    assert risk_controller["stop_loss_coefficient"] == Decimal("0.0500"), "Stop loss coefficient does not match!"
    assert risk_controller["take_profit_coefficient"] == Decimal("0.1000"), "Take profit coefficient does not match!"
    assert risk_controller["max_asset_share"] == {"BTC": Decimal("0.2500"), "USDT": Decimal("0.7500")}, "Max asset share does not match!"
