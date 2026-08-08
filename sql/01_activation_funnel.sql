SELECT
    variant,
    COUNT(*) AS signups,
    SUM(connected_data) AS connected_users,
    ROUND(100.0 * AVG(connected_data), 2) AS connect_rate_pct,
    SUM(created_dashboard) AS dashboard_users,
    ROUND(100.0 * AVG(created_dashboard), 2) AS dashboard_rate_pct,
    SUM(activated_7d) AS activated_users,
    ROUND(100.0 * AVG(activated_7d), 2) AS activation_rate_pct
FROM product_users
GROUP BY variant
ORDER BY variant;
