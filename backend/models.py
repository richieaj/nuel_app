import pickle
import os
import pandas as pd
import sqlite3
import requests
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split

# File paths
MODEL_FILE = "delivery_time_model.pkl"
DB_FILE = "mini.db"  # Ensure this matches your SQLite database filename

# API Keys
OPENWEATHER_API_KEY = "YOUR_OPENWEATHER_API_KEY" # Replace with your OpenWeather API KEY here


def get_db_connection():
    """Returns a connection to the SQLite database."""
    return sqlite3.connect(DB_FILE)

def fetch_training_data():
    """
    Fetch delivery training data from SQLite database.
    Uses:
      - Order Priority (Categorical)
      - Optimized Distance (from Route Optimization)
      - External Data (Weather API)
    """
    conn = get_db_connection()
    df = pd.read_sql("""
        SELECT d.customer_location, d.order_priority, d.delivery_time, o.optimized_distance_km 
        FROM deliveries d
        LEFT JOIN optimized_routes o
        ON d.start_location = o.start_location AND d.customer_location = o.customer_location
    """, conn)
    conn.close()

    if df.empty:
        raise ValueError("[ERROR] No training data found in DB!")

    # Convert 'order_priority' (High/Medium/Low) into numerical values
    priority_mapping = {"High": 3, "Medium": 2, "Low": 1}
    df["order_priority"] = df["order_priority"].map(priority_mapping)

    # Fill missing distances with an average fallback (200 km)
    df["optimized_distance_km"].fillna(200, inplace=True)

    # Fetch weather data
    df["weather_factor"] = df["customer_location"].apply(get_weather_factor)

    # Drop rows with missing values to avoid NaN errors
    df.dropna(inplace=True)

    # Features & target
    X = df[["order_priority", "optimized_distance_km", "weather_factor"]]
    y = df["delivery_time"]

    return X, y

def get_weather_factor(customer_location):
    """
    Uses OpenWeatherMap API to get weather conditions using latitude & longitude.
    """
    # Fetch coordinates from DB
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT customer_latitude, customer_longitude 
        FROM deliveries 
        WHERE customer_location = ?
    """, (customer_location,))
    result = cur.fetchone()
    conn.close()

    if not result:
        print(f"[WARNING] No coordinates found for {customer_location}. Using default weather factor.")
        return 1.0  # Default (no impact)

    lat, lng = result

    url = f"http://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lng}&appid={OPENWEATHER_API_KEY}"

    try:
        response = requests.get(url, timeout=10)
        data = response.json()

        if data and "weather" in data:
            condition = data["weather"][0]["main"]
            if condition in ["Rain", "Storm", "Snow"]:
                return 1.5  # Heavy impact
            elif condition in ["Clouds", "Mist"]:
                return 1.2  # Moderate impact
            else:
                return 1.0  # No impact
        else:
             print(f"[WARNING] Weather API returned no valid weather data, using default for: {customer_location}")
             return 1.0
    except Exception as e:
        print(f"[WARNING] Weather fetch failed for {customer_location} ({lat}, {lng}): {e}. Using default.")
        return 1.0  # Default (no impact)


def train_model():
    """
    Train a machine learning model using real data from SQLite.
    Saves the trained model for future predictions.
    """
    print("[INFO] Training new ML model...")
    
    try:
        X, y = fetch_training_data()

        # Train/Test split
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

        # Train model
        model = LinearRegression()
        model.fit(X_train, y_train)

        score = model.score(X_test, y_test)
        print(f"[INFO] Model trained with R^2 score: {score:.3f}")

        # Save model
        with open(MODEL_FILE, "wb") as f:
            pickle.dump(model, f)

        print(f"[INFO] Model saved to '{MODEL_FILE}'")
    
    except Exception as e:
        print(f"[ERROR] Failed to train model: {e}")

def load_model():
    """
    Load the trained model from disk.
    """
    if not os.path.exists(MODEL_FILE):
        print("[INFO] No model found, training a new one...")
        train_model()

    with open(MODEL_FILE, "rb") as f:
        model = pickle.load(f)
    return model

def predict_delivery_time(order_priority, customer_location):
    """
    Uses trained model to predict delivery time based on:
    - Order Priority
    - Distance (from optimized route)
    - Weather
    """
    model = load_model()

    # Convert order priority to numerical
    priority_mapping = {"High": 3, "Medium": 2, "Low": 1}
    order_priority = priority_mapping.get(order_priority, 2)  # Default to Medium

    # Fetch optimized distance from DB
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT optimized_distance_km 
        FROM optimized_routes 
        WHERE customer_location = ?
    """, (customer_location,))
    result = cur.fetchone()
    conn.close()

    # Default to 200 km if not found
    distance_km = result[0] if result else 200

    # Fetch weather factor
    weather_factor = get_weather_factor(customer_location)

    # Convert input to Pandas DataFrame
    X_input = pd.DataFrame([[order_priority, distance_km, weather_factor]], columns=["order_priority", "optimized_distance_km", "weather_factor"])

    pred = model.predict(X_input)[0]
    return pred

if __name__ == "__main__":
    # Train the model when this script is executed
    train_model()
    test_pred = predict_delivery_time("Medium", "Mumbai CST, India")
    print(f"[INFO] Predicted delivery time: {test_pred:.2f} minutes")