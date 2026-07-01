{{ config(materialized='table') }}

with staging_data as (
    select * from {{ ref('stg_live_positions') }}
),

total_activity as (
    select
        snapshot_time,
        -- Count every single unique trip across the entire system at this minute
        count(distinct trip_id) as total_active_trips
    from staging_data
    group by snapshot_time
)

select * from total_activity
order by snapshot_time desc