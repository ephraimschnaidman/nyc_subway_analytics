# nyc_subway_analytics
Checks and Analyzes NYC Subway station delays

nyc_subway_analytics/
│
├── docker-compose.yml
├── requirements.txt            # <-- Add 'dbt-duckdb' here
├── data/
│   ├── gtfs_raw/
│   └── mta_analytics.db
│
├── scripts/                    # Back to basics: just raw ingestion
│   ├── bootstrap_gtfs.py
│   └── live_ingestion_worker.py
│
├── transform/                  # 🚀 NEW: Your complete dbt project folder
│   ├── dbt_project.yml         # Main dbt configuration file
│   ├── profiles.yml            # Tells dbt how to connect to your DuckDB file
│   └── models/
│       ├── staging/            # Cleans up raw logs and reads Postgres dimensions
│       │   ├── stg_live_delays.sql
│       │   └── stg_station_dimensions.sql
│       └── marts/              # Final aggregate tables for your Streamlit dashboard
│           └── mart_top_delay_stations.sql
│
└── dashboard/
    └── app.py                  # Now reads from clean dbt tables instead of raw logs!
