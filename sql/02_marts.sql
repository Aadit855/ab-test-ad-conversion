-- 02_marts.sql
-- Experiment summary by variant. Statistics are computed in Python (src/analysis.py).

CREATE OR REPLACE TABLE mart_variant_summary AS
SELECT
    variant,
    COUNT(*)                AS users,
    SUM(converted)          AS conversions,
    AVG(converted)          AS conversion_rate,
    AVG(ads_seen)           AS avg_ads_seen
FROM stg_users
GROUP BY variant;
