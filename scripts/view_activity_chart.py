import duckdb
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DB_PATH = PROJECT_ROOT / "data" / "mta_analytics.db"

def generate_terminal_chart():
    conn = duckdb.connect(str(DB_PATH))
    
    # 2. Grab the latest 15 snapshots from your activity tracker mart
    query = """
        SELECT snapshot_time, total_active_trips 
        FROM main.fct_trip_activity 
        ORDER BY snapshot_time DESC 
        LIMIT 15;
    """
    
    try:
        rows = conn.execute(query).fetchall()
        
        if not rows:
            print("No data found in fct_trip_activity. Make sure to run your pipeline first!")
            return
            
        print("\n=== NYC SUBWAY SYSTEM ACTIVE TRIPS OVER TIME ===")
        print(f"{'Snapshot Time':<22} | {'Total Active Trips':<20} | Visual Graph")
        print("-" * 75)
        
        # 3. Loop through rows and print a clean text bar chart
        # We reverse it so chronological order reads top-to-bottom
        for row in reversed(rows):
            time_str = str(row[0])[:19] # Truncate milliseconds for clean printing
            trip_count = row[1]
            
            # Scale the bar so it fits nicely in the terminal (1 block per 10 trains)
            bar_length = int(trip_count / 10)
            bar = "█" * bar_length
            
            print(f"{time_str:<22} | {trip_count:<20} | {bar}")
            
        print("-" * 75)
        
    except Exception as e:
        print(f"Error reading from analytics database: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    generate_terminal_chart()
