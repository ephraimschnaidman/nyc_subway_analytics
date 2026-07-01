import os
import requests
import psycopg2
from google.transit import gtfs_realtime_pb2 # Assuming you are using the standard GTFS-rt protobuf library

MTA_FEEDS = {
    "ACE": "https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs-ace",
    "BDFM": "https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs-bdfm",
    "G": "https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs-g",
    "JZ": "https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs-jz",
    "NQRW": "https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs-nqrw",
    "L": "https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs-l",
    "1234567": "https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs",
    "SIR": "https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs-si"
}


def get_pg_connection():
    return psycopg2.connect(
        host=os.getenv("POSTGRES_HOST", "localhost"),
        port=os.getenv("POSTGRES_PORT", "5432"),
        database=os.getenv("POSTGRES_DB", "mta_static"),
        user=os.getenv("POSTGRES_USER", "postgres"),
        password=os.getenv("POSTGRES_PASSWORD", "postgres")
    )


def ensure_live_table(cursor):
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS live_train_positions (
            id BIGSERIAL PRIMARY KEY,
            trip_id TEXT NOT NULL,
            route_id TEXT,
            latitude DOUBLE PRECISION,
            longitude DOUBLE PRECISION,
            stop_id TEXT,
            fetched_at TIMESTAMPTZ NOT NULL,
            UNIQUE (trip_id, fetched_at)
        );
    """)


def collect_trip_stop_ids(feed):
    trip_stop_ids = {}
    for entity in feed.entity:
        if not entity.HasField("trip_update"):
            continue

        trip_id = entity.trip_update.trip.trip_id
        if not trip_id:
            continue

        for stop_time_update in entity.trip_update.stop_time_update:
            if stop_time_update.stop_id:
                trip_stop_ids[trip_id] = stop_time_update.stop_id
                break

    return trip_stop_ids


def get_vehicle_position(vehicle):
    if not vehicle.HasField("position"):
        return None, None

    latitude = vehicle.position.latitude
    longitude = vehicle.position.longitude

    if latitude == 0 and longitude == 0:
        return None, None

    return latitude, longitude


def fetch_mta_data():
    api_key = os.getenv("MTA_API_KEY")
    headers = {"x-api-key": api_key} if api_key else {}

    conn = get_pg_connection()
    cursor = conn.cursor()
    ensure_live_table(cursor)

    records_inserted = 0

    for feed_name, url in MTA_FEEDS.items():
        print(f"Fetching live data for lines: {feed_name}...")
        try:
            response = requests.get(url, headers=headers, timeout=30)
            if response.status_code == 200:
                feed = gtfs_realtime_pb2.FeedMessage()
                feed.ParseFromString(response.content)
                trip_stop_ids = collect_trip_stop_ids(feed)

                for entity in feed.entity:
                    if entity.HasField('vehicle'):
                        vehicle = entity.vehicle
                        trip_id = vehicle.trip.trip_id
                        route_id = vehicle.trip.route_id
                        lat, lon = get_vehicle_position(vehicle)
                        stop_id = vehicle.stop_id or trip_stop_ids.get(trip_id)

                        cursor.execute("""
                            INSERT INTO live_train_positions (trip_id, route_id, latitude, longitude, stop_id, fetched_at)
                            VALUES (%s, %s, %s, %s, %s, date_trunc('minute', CURRENT_TIMESTAMP))
                            ON CONFLICT (trip_id, fetched_at) DO NOTHING;
                        """, (trip_id, route_id, lat, lon, stop_id))
                        
                        if cursor.rowcount > 0:
                            records_inserted += 1
            else:
                print(f"Failed to fetch {feed_name}: HTTP {response.status_code}")

        except Exception as e:
            print(f"Error processing feed {feed_name}: {e}")

    conn.commit()
    cursor.close()
    conn.close()

    print(f"\nDone! Inserted {records_inserted} new live train locations across all lines.")

if __name__ == "__main__":
    fetch_mta_data()
