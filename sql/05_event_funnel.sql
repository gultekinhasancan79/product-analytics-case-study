WITH event_users AS (
    SELECT
        u.variant,
        e.event_name,
        COUNT(DISTINCT e.user_id) AS users
    FROM product_users u
    JOIN product_events e ON e.user_id = u.user_id
    WHERE e.event_name IN ('signup', 'data_connected', 'dashboard_created')
    GROUP BY u.variant, e.event_name
),
pivoted AS (
    SELECT
        variant,
        MAX(CASE WHEN event_name = 'signup' THEN users END) AS signups,
        MAX(CASE WHEN event_name = 'data_connected' THEN users END) AS connected,
        MAX(CASE WHEN event_name = 'dashboard_created' THEN users END) AS dashboards
    FROM event_users
    GROUP BY variant
)
SELECT
    variant,
    signups,
    connected,
    ROUND(100.0 * connected / signups, 2) AS signup_to_connect_pct,
    dashboards,
    ROUND(100.0 * dashboards / signups, 2) AS signup_to_dashboard_pct,
    ROUND(100.0 * dashboards / connected, 2) AS connect_to_dashboard_pct
FROM pivoted
ORDER BY variant;
