CREATE TABLE product_users (
    user_id TEXT PRIMARY KEY,
    signup_date TEXT NOT NULL,
    variant TEXT NOT NULL,
    acquisition_channel TEXT NOT NULL,
    device TEXT NOT NULL,
    connected_data INTEGER NOT NULL,
    created_dashboard INTEGER NOT NULL,
    activated_7d INTEGER NOT NULL,
    retained_14d INTEGER NOT NULL,
    support_ticket_7d INTEGER NOT NULL,
    time_to_value_hours REAL,
    revenue_30d REAL NOT NULL
);

CREATE TABLE product_events (
    event_id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    event_name TEXT NOT NULL,
    event_ts TEXT NOT NULL,
    event_value REAL,
    FOREIGN KEY (user_id) REFERENCES product_users(user_id)
);

CREATE INDEX idx_product_events_user ON product_events(user_id);
CREATE INDEX idx_product_events_name ON product_events(event_name);
