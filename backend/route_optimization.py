import math
import requests
import sqlite3
from ortools.constraint_solver import pywrapcp
from ortools.constraint_solver import routing_enums_pb2
import time

DB_FILE = "mini.db"  # SQLite Database File
MAPBOX_API_KEY = "sk.eyJ1IjoiYWpyaWNoaWUiLCJhIjoiY202bWQ3bGU2MGhxajJ3czc4Z240aWN3aiJ9.JNHZL6Tu1ArHImFazJPVBg"


def get_db_connection():
    """Returns a connection to the SQLite database."""
    return sqlite3.connect(DB_FILE)

def init_optimized_routes_table():
    """Creates the optimized_routes table if not exists."""
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS optimized_routes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            start_location TEXT,
            customer_location TEXT,
            optimized_distance_km REAL,
            UNIQUE(start_location, customer_location)
        );
    """)
    conn.commit()
    conn.close()
    print("[INFO] Optimized routes table initialized.")

def fetch_locations_from_db():
    """Fetches start and customer locations from the database."""
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT start_location, customer_location, start_latitude, start_longitude, customer_latitude, customer_longitude
        FROM deliveries
    """)
    rows = cur.fetchall()
    conn.close()
    return rows

def fetch_distance_matrix(locations):
    """Fetches a real-world distance matrix using Mapbox Directions Matrix API."""
    base_url = "https://api.mapbox.com/directions-matrix/v1/mapbox/driving"
    unique_locations = list(set([(lat, lng) for (_, _, lat, lng, _, _) in locations] +
                                 [(lat, lng) for (_, _, _, _, lat, lng) in locations]))
    if len(unique_locations) > 25:
        raise Exception(f"Too many locations ({len(unique_locations)}) for Mapbox API limit (max 25). Reduce the dataset.")
    coordinates = ";".join(["{},{}".format(lng, lat) for lat, lng in unique_locations])
    url = f"{base_url}/{coordinates}"
    params = {"access_token": MAPBOX_API_KEY, "annotations": "distance"}
    response = requests.get(url, params=params)
    data = response.json()
    if "distances" in data:
        return data["distances"]
    else:
        raise Exception(f"Mapbox API Error: {data}")

def create_data_model(locations, num_vehicles=2, depot_index=0):
    """Prepares the data model required for the OR-Tools VRP Solver."""
    data = {
        "locations": locations,
        "num_locations": len(locations),
        "num_vehicles": num_vehicles,
        "depot": depot_index,
        "distance_matrix": fetch_distance_matrix(locations)
    }
    return data

def solve_vrp(data):
    """Solves the Vehicle Routing Problem (VRP) using OR-Tools."""
    manager = pywrapcp.RoutingIndexManager(
        data["num_locations"], data["num_vehicles"], data["depot"]
    )
    routing = pywrapcp.RoutingModel(manager)
    def distance_callback(from_index, to_index):
        from_node = manager.IndexToNode(from_index)
        to_node = manager.IndexToNode(to_index)
        return int(data["distance_matrix"][from_node][to_node] if data["distance_matrix"][from_node][to_node] is not None else 200000)
    transit_callback_index = routing.RegisterTransitCallback(distance_callback)
    routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)
    search_parameters = pywrapcp.DefaultRoutingSearchParameters()
    search_parameters.first_solution_strategy = routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
    solution = routing.SolveWithParameters(search_parameters)
    if not solution:
        return None
    routes = []
    for vehicle_id in range(data["num_vehicles"]):
        index = routing.Start(vehicle_id)
        route = []
        while not routing.IsEnd(index):
            route.append(manager.IndexToNode(index))
            index = solution.Value(routing.NextVar(index))
        route.append(manager.IndexToNode(index))
        routes.append(route)
    return routes

def optimize_routes(num_vehicles=2, depot_index=0):
    """Main function to optimize routes using locations from the database and save to DB."""
    print("[INFO] Fetching locations from DB...")
    locations = fetch_locations_from_db()
    if not locations:
        print("[ERROR] No delivery locations found in the database.")
        return
    print(f"[INFO] Locations fetched successfully! Total: {len(locations)}")
    data = create_data_model(locations=locations, num_vehicles=num_vehicles, depot_index=depot_index)
    routes = solve_vrp(data)
    if not routes:
        print("[ERROR] No optimized routes found.")
        return
    print("[INFO] Saving optimized distances in DB...")
    conn = get_db_connection()
    cur = conn.cursor()
    for route in routes:
        for i in range(len(route) - 1):
            from_idx, to_idx = route[i], route[i + 1]
            if from_idx >= len(locations) or to_idx >= len(locations):
                continue
            start_location, customer_location, start_lat, start_lng, cust_lat, cust_lng = locations[from_idx]
            optimized_distance_m = data["distance_matrix"][from_idx][to_idx]
            optimized_distance_km = (optimized_distance_m / 1000) if optimized_distance_m else 200
            cur.execute("""
                INSERT INTO optimized_routes (start_location, customer_location, optimized_distance_km)
                VALUES (?, ?, ?)
                ON CONFLICT(start_location, customer_location) DO UPDATE SET optimized_distance_km = excluded.optimized_distance_km;
            """, (start_location, customer_location, optimized_distance_km))
    conn.commit()
    conn.close()
    print("[INFO] Optimized distances saved successfully!")

    return routes # Let's return the route

if __name__ == "__main__":
    try:
        start_time = time.time()
        init_optimized_routes_table()
        optimize_routes(num_vehicles=2)
        print(f"[INFO] Route optimization completed in {time.time() - start_time:.2f} seconds!")
    except Exception as e:
        print(f"[ERROR] {e}")