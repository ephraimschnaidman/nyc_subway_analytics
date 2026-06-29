import os
import pandas as pd
from sqlalchemy import create_engine, Text, Float, Integer

# 1. Connection Configuration
# Adjust these environment variables or defaults to match your docker-compose.yml
DB_USER = os.getenv("POSTGRES_USER", "postgres")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD", "postgres")
DB_HOST = os.getenv("POSTGRES_HOST", "localhost")
DB_PORT = os.getenv("POSTGRES_PORT", "5432")
DB_NAME = os.getenv("POSTGRES_DB", "mta_static")

DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

def bootstrap_static_gtfs(data_directory: str):
    """
    Parses GTFS text files and seeds them into PostgreSQL.
    """
    print("🚀 Connecting to PostgreSQL...")
    engine = create_engine(DATABASE_URL)
    
    # Define files to process, target tables, and their specific SQLAlchemy types
    gtfs_files = {
        "stops.txt": {
            "table_name": "dim_stops",
            "dtype": {
                "stop_id": Text,
                "stop_name": Text,
                "stop_lat": Float,
                "stop_lon": Float,
                "location_type": Integer,
                "parent_station": Text
            }
        },
        "stop_times.txt": {
            "table_name": "fact_stop_times",
            "dtype": {
                "trip_id": Text,
                "arrival_time": Text,
                "departure_time": Text,
                "stop_id": Text,
                "stop_sequence": Integer
            }
        }
    }

    for file_name, config in gtfs_files.items():
        file_path = os.path.join(data_directory, file_name)
        
        if not os.path.exists(file_path):
            print(f"⚠️ Warning: {file_name} not found in {data_directory}. Skipping.")
            continue
            
        print(f"📖 Parsing {file_name}...")
        
        # Read CSV/TXT payload
        # GTFS files can sometimes have mixed types or empty strings; we force string for IDs
        df = pd.read_csv(file_path, dtype=str)
        
        # Clean up columns to match only what we explicitly defined in our schema config
        columns_to_keep = list(config["dtype"].keys())
        df = df[[col for col in columns_to_keep if col in df.columns]]

        print(f"📥 Seeding {len(df)} rows into table '{config['table_name']}'...")
        
        # Write to Postgres
        df.to_sql(
            name=config["table_name"],
            con=engine,
            if_exists="replace",  # Overwrites existing data on bootstrap rerun
            index=False,
            dtype=config["dtype"]
        )
        print(f"✅ Successfully seeded '{config['table_name']}'.")

    print("\n🎉 Database bootstrapping complete!")

if __name__ == "__main__":
    # Assumes your static files are unzipped inside a folder named 'gtfs_data'
    # Download latest NYC Subway GTFS from: http://web.mta.info/developers/developer-data-terms.html#data
    DATA_DIR = "./gtfs_data" 
    
    bootstrap_static_gtfs(DATA_DIR)