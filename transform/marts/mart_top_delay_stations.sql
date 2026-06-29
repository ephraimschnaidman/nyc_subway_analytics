{{ config(materialized='table') }}

WITH raw_delays AS (
    -- Reads directly from the native DuckDB table your worker is writing to
    SELECT stop_id, delay_seconds 
    FROM main.live_delay_logs 
    WHERE delay_seconds > 120
),

stations AS (
    -- Reads from the Postgres database attached via the profile plugin
    SELECT stop_id, stop_name, parent_station 
    FROM pg_static.dim_stops
)

SELECT 
    s.parent_station,
    s.stop_name,
    COUNT(*) AS total_delays
FROM raw_delays d
JOIN stations s ON d.stop_id = s.stop_id
GROUP BY s.parent_station, s.stop_name
ORDER BY total_delays DESC