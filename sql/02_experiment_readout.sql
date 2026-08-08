SELECT
    variant,
    COUNT(*) AS users,
    ROUND(100.0 * AVG(activated_7d), 2) AS activation_7d_pct,
    ROUND(100.0 * AVG(retained_14d), 2) AS retention_14d_pct,
    ROUND(100.0 * AVG(support_ticket_7d), 2) AS support_ticket_7d_pct,
    ROUND(AVG(revenue_30d), 2) AS avg_revenue_30d,
    ROUND(AVG(CASE WHEN activated_7d = 1 THEN time_to_value_hours END), 2) AS avg_ttv_hours_activated
FROM product_users
GROUP BY variant
ORDER BY variant;
