CREATE TABLE IF NOT EXISTS orders
(
    order_id UUID,
    portfolio_id UUID NOT NULL,
    event_manager_id UUID NOT NULL,
    signal_id UUID DEFAULT NULL,
    order_type String NOT NULL,
    order_category String NOT NULL,
    order_side String NOT NULL,
    order_status String NOT NULL,
    base_currency String NOT NULL,
    quote_currency String NOT NULL,
    initial_quantity Decimal(18, 8) NOT NULL,
    executed_quantity Decimal(18, 8) DEFAULT 0,
    target_price Decimal(18, 8) NOT NULL,
    execution_summary Map(String, Decimal(18, 8)),
    total_fee Decimal(18, 8) DEFAULT 0,
    created_at DateTime DEFAULT now(),
    updated_at DateTime DEFAULT now(),
    executed_at DateTime DEFAULT NULL,
    PRIMARY KEY (order_id)
) ENGINE = MergeTree();
