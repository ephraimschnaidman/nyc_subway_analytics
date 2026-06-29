with source_data as (
    -- This pulls directly from the Postgres database we attached in profiles.yml
    select * from {{ source('mta_static', 'live_train_positions') }}
),

renamed as (
    select
        id as position_id,
        trip_id,
        route_id as subway_line,
        latitude,
        longitude,
        fetched_at as snapshot_time
    from source_data
)

select * from renamed