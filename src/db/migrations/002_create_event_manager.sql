CREATE TABLE IF NOT EXISTS event_manager
(
    event_manager_id UUID,
    mode String NOT NULL,
    status String NOT NULL,
    PRIMARY KEY (event_manager_id)
) ENGINE = MergeTree();
