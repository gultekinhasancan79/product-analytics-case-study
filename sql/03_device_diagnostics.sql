SELECT
    device,
    variant,
    COUNT(*) AS users,
    ROUND(100.0 * AVG(activated_7d), 2) AS activation_7d_pct,
    ROUND(100.0 * AVG(retained_14d), 2) AS retention_14d_pct
FROM product_users
GROUP BY device, variant
ORDER BY device, variant;
