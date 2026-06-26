import urllib.request
import urllib.parse
import json
import argparse
import sys
import time

def geocode(query):
    # Nominatim requires a custom user-agent
    url = f"https://nominatim.openstreetmap.org/search?q={urllib.parse.quote(query)}&format=json&limit=1"
    req = urllib.request.Request(url, headers={'User-Agent': 'TaiwanTourPlannerSkill/1.0'})
    try:
        time.sleep(1) # Respect Nominatim rate limits (max 1 request per second)
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode('utf-8'))
            if not data:
                return None
            return float(data[0]['lat']), float(data[0]['lon'])
    except Exception as e:
        print(f"Error geocoding {query}: {e}", file=sys.stderr)
        return None

def route(lat1, lon1, lat2, lon2, mode="driving"):
    # public OSRM supports driving, walking, cycling
    if mode not in ["driving", "walking", "cycling"]:
        mode = "driving"
        
    url = f"http://router.project-osrm.org/route/v1/{mode}/{lon1},{lat1};{lon2},{lat2}?overview=false"
    try:
        with urllib.request.urlopen(url) as response:
            data = json.loads(response.read().decode('utf-8'))
            if data.get('code') != 'Ok':
                return None
            route_data = data['routes'][0]
            return {
                'distance_meters': route_data['distance'],
                'duration_seconds': route_data['duration']
            }
    except Exception as e:
        print(f"Error routing: {e}", file=sys.stderr)
        return None

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Calculate distance and duration using OSM and OSRM")
    parser.add_argument("--origin", required=True, help="Origin place name")
    parser.add_argument("--destination", required=True, help="Destination place name")
    parser.add_argument("--mode", default="driving", choices=["driving", "walking", "cycling"], help="Travel mode")
    
    args = parser.parse_args()
    
    orig_coords = geocode(args.origin)
    if not orig_coords:
        print(json.dumps({"error": f"Could not find coordinates for {args.origin}"}))
        sys.exit(1)
        
    dest_coords = geocode(args.destination)
    if not dest_coords:
        print(json.dumps({"error": f"Could not find coordinates for {args.destination}"}))
        sys.exit(1)
        
    route_info = route(orig_coords[0], orig_coords[1], dest_coords[0], dest_coords[1], args.mode)
    
    if route_info:
        result = {
            "origin": args.origin,
            "origin_coords": orig_coords,
            "destination": args.destination,
            "destination_coords": dest_coords,
            "mode": args.mode,
            "distance_km": round(route_info['distance_meters'] / 1000.0, 2),
            "duration_mins": round(route_info['duration_seconds'] / 60.0, 1),
            "google_maps_link": f"https://www.google.com/maps/dir/?api=1&origin={orig_coords[0]},{orig_coords[1]}&destination={dest_coords[0]},{dest_coords[1]}&travelmode={'walking' if args.mode == 'walking' else 'driving'}"
        }
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(json.dumps({"error": "Could not calculate route"}))
        sys.exit(1)
