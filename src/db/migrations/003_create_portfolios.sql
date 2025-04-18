CREATE TABLE IF NOT EXISTS portfolios
(
    portfolio_id UUID,
    event_manager_id UUID NOT NULL,
    risk_controller_id UUID NOT NULL,
    portfolio_name String NOT NULL,
    managed_assets Map(String, Decimal(10, 4)) NOT NULL,
    currency String,
    initial_balance Decimal(18, 8),
    exchange String NOT NULL,
    PRIMARY KEY (portfolio_id)
) ENGINE = MergeTree();
