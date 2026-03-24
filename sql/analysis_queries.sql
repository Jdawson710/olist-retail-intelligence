-- =========================================
-- 1. Shipping Delay Audit (by state)
-- =========================================
SELECT 
    c.customer_state,
    ROUND(AVG(DATEDIFF(o.order_delivered_customer_date, o.order_estimated_delivery_date)), 2) AS avg_delay_days
FROM orders o
JOIN customers c ON o.customer_id = c.customer_id
WHERE o.order_status = 'delivered'
GROUP BY c.customer_state
ORDER BY avg_delay_days DESC
LIMIT 3;


-- =========================================
-- 2. Top Sellers by Category (DENSE_RANK)
-- =========================================
SELECT *
FROM (
    SELECT 
        p.product_category_name,
        s.seller_id,
        ROUND(SUM(oi.price), 2) AS revenue,
        DENSE_RANK() OVER (
            PARTITION BY p.product_category_name 
            ORDER BY SUM(oi.price) DESC
        ) AS rank_in_category
    FROM order_items oi
    JOIN products p ON oi.product_id = p.product_id
    JOIN sellers s ON oi.seller_id = s.seller_id
    GROUP BY p.product_category_name, s.seller_id
) ranked
WHERE rank_in_category <= 5;


-- =========================================
-- 3. Payment Preferences (CASE)
-- =========================================
SELECT 
    CASE 
        WHEN op.payment_type = 'credit_card' THEN 'Credit Card'
        WHEN op.payment_type = 'boleto' THEN 'Boleto'
        ELSE 'Other'
    END AS payment_category,
    ROUND(AVG(op.payment_value), 2) AS avg_order_value
FROM order_payments op
GROUP BY payment_category;


-- =========================================
-- 4. Customer Lifetime Value (CTE)
-- =========================================
WITH customer_totals AS (
    SELECT 
        o.customer_id,
        COUNT(DISTINCT o.order_id) AS total_orders,
        SUM(op.payment_value) AS total_spent
    FROM orders o
    JOIN order_payments op ON o.order_id = op.order_id
    GROUP BY o.customer_id
)

SELECT *
FROM customer_totals
WHERE total_spent > (
    SELECT AVG(total_spent) FROM customer_totals
)
AND total_orders > 2;