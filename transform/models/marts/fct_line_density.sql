{{ config(materialized='table') }}

with staging_data as (
    -- Pulling directly from your clean staging model
    select * from {{ ref('stg_live_positions') }}
),

aggregated as (
    select
        snapshot_time,
        subway_line,
        -- Count the unique trip IDs to see how many individual trains are on the line
        count(distinct trip_id) as active_train_count
    from staging_data
    group by snapshot_time, subway_line
)

select * from aggregated
order by snapshot_time desc, active_train_count desc