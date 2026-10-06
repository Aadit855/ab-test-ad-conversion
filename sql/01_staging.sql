-- 01_staging.sql
-- One row per user. Source: raw_ab (loaded from the gzipped CSV, unchanged).
-- Variant labels are normalized to 'ad' (treatment) and 'psa' (control).

CREATE OR REPLACE TABLE stg_users AS
SELECT
    user_id,
    CASE test_group WHEN 'ad' THEN 'ad' WHEN 'psa' THEN 'psa' END AS variant,
    converted::INT    AS converted,
    total_ads         AS ads_seen,
    most_ads_day      AS peak_ad_day,
    most_ads_hour     AS peak_ad_hour
FROM raw_ab
WHERE test_group IN ('ad', 'psa');
