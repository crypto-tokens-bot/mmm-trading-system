CREATE TABLE IF NOT EXISTS strategy_subscriptions
(
    portfolio_id UUID NOT NULL,
    strategy_id UUID NOT NULL
) ENGINE = MergeTree()
ORDER BY (portfolio_id, strategy_id);