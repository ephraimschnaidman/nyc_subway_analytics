{{ config(materialized='table') }}

with live_positions as (
    select * from {{ ref('stg_live_positions') }}
),

static_stops as (
    -- Pulling from the static tables created by bootstrap_gtfs.py
    select 
        stop_id, 
        stop_name
    from {{ source('mta_static', 'stops') }}
)

select
    lp.snapshot_time,
    lp.trip_id,
    lp.subway_line,
    lp.stop_id,
    s.stop_name as current_station_name
from live_positions lp
left join static_stops s
    on lp.stop_id = s.stop_id
