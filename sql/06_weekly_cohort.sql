SELECT
    strftime('%Y-W%W', signup_date) AS signup_week,
    variant,
    COUNT(*) AS signups,
    ROUND(100.0 * AVG(activated_7d), 2) AS activation_pct,
    ROUND(100.0 * AVG(retained_14d), 2) AS retention_14d_pct,
    ROUND(AVG(revenue_30d), 2) AS revenue_30d_per_signup
FROM product_users
GROUP BY signup_week, variant
ORDER BY signup_week, variant;
