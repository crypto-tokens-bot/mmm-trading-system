CREATE TABLE IF NOT EXISTS strategies
(
    strategy_id UUID,
    event_manager_id UUID NOT NULL,
    trading_pair String NOT NULL,
    strategy_name String NOT NULL,
    strategy_type String NOT NULL,
    parameters String NOT NULL,
    PRIMARY KEY (strategy_id)
) ENGINE = MergeTree();
