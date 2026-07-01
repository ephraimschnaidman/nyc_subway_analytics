{{ config(materialized='table') }}

with station_positions as (
    select *
    from {{ ref('stg_live_with_stations') }}
    where current_station_name is not null
),

aggregated as (
    select
        snapshot_time,
        subway_line,
        current_station_name,
        count(distinct trip_id) as active_train_count
    from station_positions
    group by snapshot_time, subway_line, current_station_name
)

select *
from aggregated
order by snapshot_time desc, active_train_count desc