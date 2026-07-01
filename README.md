# NYC Subway Analytics

Data engineering project for collecting NYC subway realtime vehicle positions, modeling them with dbt, and serving analytics through Streamlit.

## Architecture

```text
MTA realtime + static GTFS data
        |
        v
Postgres raw source database: mta_static
        |
        v
dbt-duckdb transformation project
        |
        v
DuckDB analytics database: data/mta_analytics.db
        |
        v
Streamlit dashboard
```

## Project Structure

```text
nyc_subway_analytics/
├── dashboard/
│   └── app.py
├── data/
│   └── mta_analytics.db
├── ingest/
│   └── fetch_mta_live.py
├── scripts/
│   ├── bootstrap_gtfs.py
│   └── view_activity_chart.py
├── transform/
│   ├── dbt_project.yml
│   ├── profiles.yml
│   └── models/
│       ├── staging/
│       └── marts/
├── docker-compose.yml
└── requirements.txt
```

## Run The Pipeline

1. Start Postgres.

```bash
docker compose up -d
```

2. Install Python dependencies.

```bash
pip install -r requirements.txt
```

3. Load static subway station and route data into Postgres.

```bash
python scripts/bootstrap_gtfs.py
```

4. Fetch a realtime snapshot into Postgres.

```bash
python ingest/fetch_mta_live.py
```

5. Build dbt models into DuckDB.

```bash
cd transform
dbt run --profiles-dir .
```

6. Open the dashboard from the project root.

```bash
streamlit run dashboard/app.py
```

## Main Tables

- `stops`: static GTFS stop reference data in Postgres.
- `routes`: static GTFS route reference data in Postgres.
- `live_train_positions`: raw realtime vehicle positions in Postgres.
- `stg_live_positions`: cleaned live position records in DuckDB.
- `stg_live_with_stations`: live positions matched to nearest station names.
- `fct_trip_activity`: active trip counts by snapshot time.
- `fct_line_density`: active train counts by subway line and snapshot time.
