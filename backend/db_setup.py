import sqlite3
import requests
import random
import math
import os

DB_FILE = "mini.db"  # SQLite Database File
MAPBOX_API_KEY = "sk.eyJ1IjoiYWpyaWNoaWUiLCJhIjoiY202bWQ3bGU2MGhxajJ3czc4Z240aWN3aiJ9.JNHZL6Tu1ArHImFazJPVBg"


def get_db_connection():    
    """Returns a connection to the SQLite database."""
    return sqlite3.connect(DB_FILE)

def geocode_address(address):
    """Fetches latitude & longitude for a given address using Mapbox Geocoding API."""
    url = f"https://api.mapbox.com/geocoding/v5/mapbox.places/{address}.json"
    response = requests.get(url, params={"access_token": MAPBOX_API_KEY})
    data = response.json()

    if "features" in data and len(data["features"]) > 0:
        location = data["features"][0]["geometry"]["coordinates"]
        return location[1], location[0]  # Mapbox returns [longitude, latitude]
    else:
        raise ValueError(f"Failed to geocode address: {address}, Status: {data.get('message', 'Unknown Error')}")

def calculate_euclidean_distance(lat1, lon1, lat2, lon2):
    """Calculates Euclidean distance between two geographic points."""
    return math.sqrt((lat2 - lat1) ** 2 + (lon2 - lon1) ** 2) * 111  # Approx conversion to km

def init_db():
    """Creates required tables in SQLite database."""
    conn = get_db_connection()
    cur = conn.cursor()

    # Updated Table Schema
    cur.execute("""
        CREATE TABLE IF NOT EXISTS deliveries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id TEXT,
            start_location TEXT,
            customer_location TEXT,
            start_latitude REAL,
            start_longitude REAL,
            customer_latitude REAL,
            customer_longitude REAL,
            euclidean_distance_km REAL,  -- NEW COLUMN
            order_priority TEXT,
            delivery_time REAL,
            vehicle_id TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    conn.commit()
    conn.close()
    print("[INFO] SQLite tables created (or already exist).")

def seed_deliveries_data():
    """Seeds sample delivery data with dynamically fetched lat/lng from Mapbox API."""
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) FROM deliveries;")
    if cur.fetchone()[0] > 0:
        print("[INFO] Sample data already exists. Skipping seeding.")
        conn.close()
        return

    # **Source location remains fixed**
    source_location = "Secunderabad Junction, India"

    # **20 Destination Railway Stations in India**
    destination_locations = [
        "Chennai Central, India", "Howrah Junction, India", "Mumbai CST, India",
        "New Delhi Railway Station, India", "Bangalore City Junction, India",
        "Pune Junction, India", "Jaipur Junction, India", "Lucknow Charbagh, India",
        "Ahmedabad Junction, India", "Bhubaneswar Railway Station, India",
        "Patna Junction, India", "Ranchi Junction, India", "Kolkata Sealdah, India",
        "Coimbatore Junction, India", "Madurai Junction, India",
        "Visakhapatnam Railway Station, India", "Varanasi Junction, India",
        "Amritsar Junction, India", "Nagpur Junction, India", "Agra Cantonment, India"
    ]

    # Generate random data for order priorities and delivery times
    priorities = ["High", "Medium", "Low"]
    delivery_times = [random.uniform(30.0, 120.0) for _ in range(len(destination_locations))]

    enriched_data = []
    for i, destination in enumerate(destination_locations):
        order_id = f"ORD{str(i+1).zfill(3)}"
        priority = random.choice(priorities)
        delivery_time = delivery_times[i]
        vehicle_id = f"VEH{random.randint(1, 10)}"
        try:
            # Fetch coordinates
            source_lat, source_lng = geocode_address(source_location)
            dest_lat, dest_lng = geocode_address(destination)

            # Calculate Euclidean distance
            euclidean_distance = calculate_euclidean_distance(source_lat, source_lng, dest_lat, dest_lng)

            # Save data
            enriched_data.append((order_id, source_location, destination, source_lat, source_lng, dest_lat, dest_lng, euclidean_distance, priority, delivery_time, vehicle_id))
        
        except ValueError as e:
            print(f"[ERROR] Geocoding failed for {source_location} or {destination}: {e}")
            continue

    cur.executemany("""
        INSERT INTO deliveries (order_id, start_location, customer_location, start_latitude, start_longitude, customer_latitude, customer_longitude, euclidean_distance_km, order_priority, delivery_time, vehicle_id)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, enriched_data)

    conn.commit()
    conn.close()
    print("[INFO] Deliveries seeded with geocoded locations.")

if __name__ == "__main__":
    init_db()
    seed_deliveries_data()