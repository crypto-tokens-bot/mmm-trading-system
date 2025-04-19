# src/risk_management/risk_controller.py
from dataclasses import dataclass
from decimal import Decimal
from typing import Dict, Optional

from src.db.queries.risk_controllers import get_risk_controller_by_id


@dataclass
class TradeDecision:
    """Result of a risk‑check for a single strategy signal."""
    direction: str                # "buy" | "sell"
    trading_pair: str               # e.g. "BTC/USDT"
    quantity: Decimal        # units to trade
    target_price: Decimal
    stop_loss: Optional[Decimal] = None
    take_profit: Optional[Decimal] = None


class RiskController:
    """
    Portfolio‑level risk manager.

    It is initialised from the **RiskControllers** table and stays attached
    to a single `Portfolio` instance.  `evaluate()` turns a raw *SignalEvent*
    dictionary into a `TradeDecision` or returns *None* when the signal is
    rejected by risk rules.
    """

    def __init__(
        self,
        risk_controller_id: str,
        risk_model: str,
        stop_loss_coefficient: Decimal,
        take_profit_coefficient: Decimal,
        max_asset_share: Dict[str, Decimal],
        portfolio,
    ):
        self.id = risk_controller_id
        self.risk_model = risk_model
        self.stop_loss_coef = stop_loss_coefficient
        self.take_profit_coef = take_profit_coefficient
        self.max_asset_share = max_asset_share
        self.portfolio = portfolio

    @staticmethod
    def create_risk_controller(risk_controller_id: str, portfolio):
        rc_row = get_risk_controller_by_id(risk_controller_id)
        if not rc_row:
            raise ValueError(f"RiskController '{risk_controller_id}' not found")

        rc = rc_row[0]
        return RiskController(
            risk_controller_id=rc["risk_controller_id"],
            risk_model=rc["risk_model"],
            stop_loss_coefficient=rc["stop_loss_coefficient"],
            take_profit_coefficient=rc["take_profit_coefficient"],
            max_asset_share=rc["max_asset_share"],
            portfolio=portfolio,
        )

    def evaluate(self, signal_event: dict) -> Optional[TradeDecision]:
        """
        Validate a *SignalEvent* and return a `TradeDecision`.

        Required payload keys
        ---------------------
        - ``payload['trading_pair']`` – BTC/USDT
        - ``payload['direction']``  – "buy" | "sell"

        """
        payload = signal_event["payload"]
        trading_pair = payload["trading_pair"]
        direction = payload["direction"]
        target_price = payload["target_price"]
        current_qty = self.portfolio.managed_assets.get(trading_pair, Decimal("0"))

        if direction == "sell":
            return None if current_qty == 0 else TradeDecision(direction=direction, target_price=target_price, trading_pair=trading_pair, quantity=current_qty)

        total_qty = sum(self.portfolio.managed_assets.values()) or Decimal("1")
        current_share = current_qty / total_qty
        if current_share >= self.max_asset_share.get(trading_pair, Decimal("1")):
            return None

        buy_qty = Decimal("0.0001") # fix
        return TradeDecision(direction=direction, trading_pair=trading_pair, quantity=buy_qty, target_price=target_price, stop_loss=None, take_profit=None)
