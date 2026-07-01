"""
The bootstrap_gtfs.py file is a one-time setup script (often called a provisioning or bootstrapping script). 
Since it's a utility script used to initialize your database rather than something that runs continuously in your live ingestion pipeline, 
it belongs in your scripts/ folder right alongside your visualization tool.
Because subway tracks and station names don't change very often, 
you only need to re-run it if the MTA updates its official schedules 
(like adding a new station or permanently changing a train route), 
which usually only happens a few times a year.
"""

import os
import csv
import zipfile
import io
import requests
import psycopg2

def get_pg_connection():
    return psycopg2.connect(
        host=os.getenv("POSTGRES_HOST", "localhost"),
        port=os.getenv("POSTGRES_PORT", "5432"),
        database=os.getenv("POSTGRES_DB", "mta_static"),
        user=os.getenv("POSTGRES_USER", "postgres"),
        password=os.getenv("POSTGRES_PASSWORD", "postgres")
    )


def bootstrap_static_gtfs():
    # 1. Official MTA URL for Static Schedule Data (GTFS)
    GTFS_STATIC_URL = "http://web.mta.info/developers/data/nyct/subway/google_transit.zip"
    
    # 2. Connect to your existing PostgreSQL database
    print(f"Connecting to PostgreSQL database '{os.getenv('POSTGRES_DB', 'mta_static')}'...")
    conn = get_pg_connection()
    cursor = conn.cursor()

    # 3. Create the static reference tables if they don't exist
    print("Creating static reference tables...")
    cursor.execute("""
        DROP TABLE IF EXISTS stops CASCADE;
        CREATE TABLE stops (
            stop_id VARCHAR(255) PRIMARY KEY,
            stop_name VARCHAR(255),
            stop_lat DOUBLE PRECISION,
            stop_lon DOUBLE PRECISION
        );
        
        DROP TABLE IF EXISTS routes CASCADE;
        CREATE TABLE routes (
            route_id VARCHAR(255) PRIMARY KEY,
            route_long_name VARCHAR(255),
            route_type INT
        );
    """)
    conn.commit()

    # 4. Download the static zip file directly into memory
    print("Downloading official MTA static schedule dataset (this may take a moment)...")
    response = requests.get(GTFS_STATIC_URL)
    
    if response.status_code != 200:
        print(f"Failed to download MTA data. HTTP Status: {response.status_code}")
        return

    # 5. Extract and parse the files inside the ZIP archive
    with zipfile.ZipFile(io.BytesIO(response.content)) as z:
        
        # --- PARSE STOPS ---
        print("Processing and loading 'stops.txt'...")
        with z.open("stops.txt") as f:
            reader = csv.DictReader(io.TextIOWrapper(f, encoding="utf-8"))
            for row in reader:
                stop_id = row["stop_id"].strip()
                stop_name = row["stop_name"].strip()
                lat_raw = row["stop_lat"].strip()
                lon_raw = row["stop_lon"].strip()

                if not lat_raw or not lon_raw:
                    continue

                try:
                    stop_lat = float(lat_raw)
                    stop_lon = float(lon_raw)
                except ValueError:
                    continue

                cursor.execute("""
                    INSERT INTO stops (stop_id, stop_name, stop_lat, stop_lon)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (stop_id) DO NOTHING;
                """, (stop_id, stop_name, stop_lat, stop_lon))

        # --- PARSE ROUTES ---
        print("Processing and loading 'routes.txt'...")
        with z.open("routes.txt") as f:
            reader = csv.DictReader(io.TextIOWrapper(f, encoding="utf-8"))
            for row in reader:
                route_id = row["route_id"].strip()
                route_long_name = row["route_long_name"].strip()
                route_type = int(row["route_type"])

                cursor.execute("""
                    INSERT INTO routes (route_id, route_long_name, route_type)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (route_id) DO NOTHING;
                """, (route_id, route_long_name, route_type))

    # 6. Save everything and wrap up
    conn.commit()
    
    cursor.execute("SELECT COUNT(*) FROM stops;")
    total_stops = cursor.fetchone()[0]
    
    cursor.close()
    conn.close()
    
    print(f"\nSuccess! Bootstrapped {total_stops} static transit stations into Postgres.")

if __name__ == "__main__":
    bootstrap_static_gtfs()
