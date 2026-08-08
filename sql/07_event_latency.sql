WITH signup AS (
    SELECT user_id, event_ts AS signup_ts
    FROM product_events
    WHERE event_name = 'signup'
),
dashboard AS (
    SELECT user_id, event_ts AS dashboard_ts
    FROM product_events
    WHERE event_name = 'dashboard_created'
)
SELECT
    u.variant,
    u.device,
    COUNT(*) AS activated_users,
    ROUND(
        AVG((julianday(d.dashboard_ts) - julianday(s.signup_ts)) * 24.0),
        2
    ) AS mean_hours_signup_to_dashboard
FROM product_users u
JOIN signup s ON s.user_id = u.user_id
JOIN dashboard d ON d.user_id = u.user_id
GROUP BY u.variant, u.device
ORDER BY u.variant, u.device;
