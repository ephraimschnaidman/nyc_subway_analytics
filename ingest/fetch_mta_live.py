import requests
from google.transit import gtfs_realtime_pb2
import psycopg2

# 1. Connect to your local Windows PostgreSQL database
try:
    conn = psycopg2.connect(
        dbname="mta_static",
        user="postgres",
        password="postgres",
        host="localhost",
        port="5432"
    )
    cursor = conn.cursor()
    print("Successfully connected to PostgreSQL database!")
except Exception as e:
    print(f"Database connection failed: {e}")
    exit()

# 2. Create a table to hold live train positions if it doesn't exist
cursor.execute("""
    CREATE TABLE IF NOT EXISTS live_train_positions (
        id SERIAL PRIMARY KEY,
        trip_id VARCHAR(100),
        route_id VARCHAR(10),
        latitude FLOAT,
        longitude FLOAT,
        fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
""")
conn.commit()

# 3. Fetch the Live Real-time Feed from the MTA
# This URL handles the ACE subway lines
mta_url = "https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs-ace"

print("Fetching live data from the MTA...")
response = requests.get(mta_url)

if response.status_code == 200:
    # 4. Parse the Protocol Buffer data
    feed = gtfs_realtime_pb2.FeedMessage()
    feed.ParseFromString(response.content)
    
    print(f"Successfully downloaded feed. Parsing entries...")
    records_inserted = 0
    
    # Loop through all live transit updates inside the feed
    for entity in feed.entity:
        if entity.HasField('vehicle'):
            vehicle = entity.vehicle
            trip_id = vehicle.trip.trip_id
            route_id = vehicle.trip.route_id
            lat = vehicle.position.latitude
            lon = vehicle.position.longitude
            
            # Insert the live train snapshot into Postgres
            cursor.execute("""
                INSERT INTO live_train_positions (trip_id, route_id, latitude, longitude)
                VALUES (%s, %s, %s, %s);
            """, (trip_id, route_id, lat, lon))
            records_inserted += 1

    conn.commit()
    print(f" Done! Inserted {records_inserted} live train locations into 'live_train_positions'.")
else:
    print(f"Failed to fetch data from MTA. Status Code: {response.status_code}")

# Close connections
cursor.close()
conn.close()