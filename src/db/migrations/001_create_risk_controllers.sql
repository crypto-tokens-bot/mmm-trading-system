CREATE TABLE IF NOT EXISTS risk_controllers
(
    risk_controller_id UUID,
    risk_model String NOT NULL,
    stop_loss_coefficient Decimal(10, 4) NOT NULL,
    take_profit_coefficient Decimal(10, 4) NOT NULL,
    max_asset_share Map(String, Decimal(10, 4)) NOT NULL,
    PRIMARY KEY (risk_controller_id)
) ENGINE = MergeTree();
