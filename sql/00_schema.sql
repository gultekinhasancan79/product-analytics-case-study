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
