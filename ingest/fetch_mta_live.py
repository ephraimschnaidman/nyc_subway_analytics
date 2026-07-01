import os
import requests
import psycopg2
from google.transit import gtfs_realtime_pb2 # Assuming you are using the standard GTFS-rt protobuf library

def fetch_mta_data():
    # 1. Dictionary of the major MTA Real-Time Feed URLs covering the whole system
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

    # 2. Configure API Headers (using an environment variable or direct string)
    API_KEY = os.getenv("MTA_API_KEY", "YOUR_MTA_API_KEY_HERE")
    headers = {"x-api-key": API_KEY}

    # 3. Connect to your PostgreSQL database
    conn = psycopg2.connect(
        host="localhost",
        database="mta_static",
        user="postgres",       # Update if your username is different
        password="postgres"    # Update with your actual password
    )
    cursor = conn.cursor()

    records_inserted = 0

    # 4. Loop through every single feed URL
    for feed_name, url in MTA_FEEDS.items():
        print(f"Fetching live data for lines: {feed_name}...")
        try:
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                # Parse the protocol buffer feed
                feed = gtfs_realtime_pb2.FeedMessage()
                feed.ParseFromString(response.content)

                for entity in feed.entity:
                    # Ensure the entity has vehicle position data
                    if entity.HasField('vehicle'):
                        vehicle = entity.vehicle
                        trip_id = vehicle.trip.trip_id
                        route_id = vehicle.trip.route_id
                        lat = vehicle.position.latitude
                        lon = vehicle.position.longitude

                        # 5. Insert rows rounded to the nearest minute, ignoring conflicts
                        cursor.execute("""
                            INSERT INTO live_train_positions (trip_id, route_id, latitude, longitude, fetched_at)
                            VALUES (%s, %s, %s, %s, date_trunc('minute', CURRENT_TIMESTAMP))
                            ON CONFLICT (trip_id, fetched_at) DO NOTHING;
                        """, (trip_id, route_id, lat, lon))
                        
                        if cursor.rowcount > 0:
                            records_inserted += 1
            else:
                print(f"Failed to fetch {feed_name}: HTTP {response.status_code}")

        except Exception as e:
            print(f"Error processing feed {feed_name}: {e}")

    # 6. Commit changes and close the connection
    conn.commit()
    cursor.close()
    conn.close()

    print(f"\nDone! Inserted {records_inserted} new live train locations across all lines.")

if __name__ == "__main__":
    fetch_mta_data()