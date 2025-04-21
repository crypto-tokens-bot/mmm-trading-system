CREATE TABLE ohlcv_data (
    symbol String,
    timeframe String,
    time DateTime,
    open Float64,
    high Float64,
    low Float64,
    close Float64,
    volume Float64,
    updated_at DateTime DEFAULT now()
)
ENGINE = ReplacingMergeTree(updated_at)
ORDER BY (symbol, timeframe, time)
TTL time + INTERVAL 30 DAY;