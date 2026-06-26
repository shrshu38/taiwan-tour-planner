import sqlite3
import urllib.request
import json
import argparse
import sys
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "tra_schedule.db")

def update_db():
    print("Downloading TRA Schedule from Open Data (data.gov.tw)...", file=sys.stderr)
    url = "https://tdx.transportdata.tw/data-service/Opendata/File/Rail/TRA/DailyTrainTimetable/Today.json"
    
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'TaiwanTourPlannerSkill/1.0'})
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode('utf-8'))
    except Exception as e:
        print(f"Failed to download open data: {e}", file=sys.stderr)
        print("Creating an empty SQLite schema instead. Please manually place a valid JSON if needed.", file=sys.stderr)
        data = {"TrainTimetables": []}

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DROP TABLE IF EXISTS timetables")
    cursor.execute("""
        CREATE TABLE timetables (
            train_no TEXT,
            direction TEXT,
            train_type TEXT,
            stop_sequence INTEGER,
            station_id TEXT,
            station_name TEXT,
            arrival_time TEXT,
            departure_time TEXT
        )
    """)
    
    records = []
    if "TrainTimetables" in data:
        for train in data["TrainTimetables"]:
            train_no = train["TrainInfo"]["TrainNo"]
            direction = str(train["TrainInfo"]["Direction"])
            train_type = train["TrainInfo"]["TrainTypeName"]["Zh_tw"]
            
            for stop in train["StopTimes"]:
                records.append((
                    train_no,
                    direction,
                    train_type,
                    stop["StopSequence"],
                    stop["StationID"],
                    stop["StationName"]["Zh_tw"],
                    stop.get("ArrivalTime", ""),
                    stop.get("DepartureTime", "")
                ))
    
    cursor.executemany("INSERT INTO timetables VALUES (?, ?, ?, ?, ?, ?, ?, ?)", records)
    conn.commit()
    
    cursor.execute("CREATE INDEX idx_station ON timetables(station_name)")
    cursor.execute("CREATE INDEX idx_train ON timetables(train_no)")
    conn.commit()
    conn.close()
    
    print(f"Successfully updated TRA SQLite database at {DB_PATH}", file=sys.stderr)

def query_db(origin, destination):
    if not os.path.exists(DB_PATH):
        print(json.dumps({"error": "Database not found. Please run with --update first to initialize the cache."}))
        sys.exit(1)
        
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    query = """
    SELECT 
        o.train_no, 
        o.train_type,
        o.departure_time as origin_dep, 
        d.arrival_time as dest_arr
    FROM timetables o
    JOIN timetables d ON o.train_no = d.train_no
    WHERE o.station_name LIKE ? 
      AND d.station_name LIKE ?
      AND o.stop_sequence < d.stop_sequence
    ORDER BY o.departure_time ASC
    LIMIT 5
    """
    
    cursor.execute(query, (f"%{origin}%", f"%{destination}%"))
    rows = cursor.fetchall()
    
    results = []
    for row in rows:
        results.append({
            "train_no": row["train_no"],
            "train_type": row["train_type"],
            "departure": row["origin_dep"],
            "arrival": row["dest_arr"]
        })
        
    conn.close()
    
    if not results:
        print(json.dumps({"error": f"No trains found from {origin} to {destination} in local cache."}))
    else:
        print(json.dumps({"origin": origin, "destination": destination, "trains": results}, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Manage and query local TRA SQLite database")
    parser.add_argument("--update", action="store_true", help="Download latest Open Data and build SQLite DB")
    parser.add_argument("--query", action="store_true", help="Query the database")
    parser.add_argument("--origin", help="Origin station name")
    parser.add_argument("--destination", help="Destination station name")
    
    args = parser.parse_args()
    
    if args.update:
        update_db()
    elif args.query:
        if not args.origin or not args.destination:
            print(json.dumps({"error": "Must provide --origin and --destination for querying"}))
            sys.exit(1)
        query_db(args.origin, args.destination)
    else:
        parser.print_help()
