{{ config(materialized='view') }}

with live_positions as (
    select * from {{ ref('stg_live_positions') }}
),

static_stops as (
    -- Pulling from the static tables created by bootstrap_gtfs.py
    select 
        stop_id, 
        stop_name, 
        stop_lat, 
        stop_lon 
    from {{ source('mta_static', 'stops') }}
),

calculated_distances as (
    select
        lp.snapshot_time,
        lp.trip_id,
        lp.subway_line,
        s.stop_name as closest_station_name,
        -- Simple Pythagorean distance formula for proximity
        ( (lp.latitude - s.stop_lat) * (lp.latitude - s.stop_lat) + 
          (lp.longitude - s.stop_lon) * (lp.longitude - s.stop_lon) ) as distance_squared,
        
        -- Number the stations from closest to furthest for each individual train
        row_number() over (
            partition by lp.trip_id, lp.snapshot_time 
            order by ( (lp.latitude - s.stop_lat) * (lp.latitude - s.stop_lat) + 
                       (lp.longitude - s.stop_lon) * (lp.longitude - s.stop_lon) ) asc
        ) as rank
    from live_positions lp
    cross join static_stops s
)

-- Only keep the single closest station for each train snapshot
select
    snapshot_time,
    trip_id,
    subway_line,
    closest_station_name
from calculated_distances
where rank = 1