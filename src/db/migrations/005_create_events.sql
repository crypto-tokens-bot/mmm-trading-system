CREATE TABLE IF NOT EXISTS events
(
    event_id UUID,
    event_manager_id UUID NOT NULL,
    event_type String NOT NULL,
    priority Int32 NOT NULL,
    payload String NOT NULL,
    created_at DateTime DEFAULT now(),
    executed_at DateTime DEFAULT NULL,
    INDEX idx_unexecuted executed_at TYPE minmax GRANULARITY 32,
    PRIMARY KEY (event_id)
) ENGINE = MergeTree();
