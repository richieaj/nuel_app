from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
import os
from typing import List, Tuple

from models import predict_delivery_time, train_model, load_model
from route_optimization import optimize_routes

app = FastAPI()

# ✅ Add CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ Request Models
class PredictRequest(BaseModel):
    order_priority: str
    customer_location: str  # Include customer_location

class OptimizationRequest(BaseModel):
    num_vehicles: int = 2

@app.get("/")
def root():
    """ Health Check Endpoint """
    return {"message": "Backend Running Successfully!"}

@app.post("/optimize")
def optimize_route(data: OptimizationRequest):
    """
    Calls the OR-Tools optimizer to generate the best routes.
    """
    try:
        # Pass num_vehicles to optimize_routes
        routes = optimize_routes(num_vehicles=data.num_vehicles)
        #After Optimization let's trigger training
        train_model()
        return {"optimized_routes": routes}
    except Exception as e:
        return {"error": str(e)}

@app.post("/predict")
def predict_delivery(req: PredictRequest):
    """
    Predict delivery time using the trained model.
    """
    try:
        # Pass order_priority and customer_location
        pred_time = predict_delivery_time(req.order_priority, req.customer_location)
        return {"predicted_delivery_time": pred_time}
    except Exception as e:
        return {"error": str(e)}

@app.post("/train_model")
def train():
    """
    Train the ML model using the latest data from SQLite database.
    """
    try:
        train_model()
        return {"message": "Model retrained and saved."}
    except Exception as e:
        return {"error": str(e)}

@app.get("/deliveries")
def get_deliveries():
    """
    Fetch all deliveries stored in the SQLite database.
    """
    try:
        # Connect to DB and fetch all deliveries
        from database import get_db_connection  # Import directly here
        conn = get_db_connection()
        conn.row_factory = lambda cursor, row: {col[0]: row[idx] for idx, col in enumerate(cursor.description)}
        cur = conn.cursor()
        cur.execute("SELECT * FROM deliveries")
        rows = cur.fetchall()
        conn.close()
        return rows
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    print("[INFO] Running Backend...")
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)