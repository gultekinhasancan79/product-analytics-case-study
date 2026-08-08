SELECT
    acquisition_channel,
    variant,
    COUNT(*) AS users,
    ROUND(100.0 * AVG(activated_7d), 2) AS activation_7d_pct,
    ROUND(AVG(revenue_30d), 2) AS avg_revenue_30d
FROM product_users
GROUP BY acquisition_channel, variant
ORDER BY acquisition_channel, variant;
