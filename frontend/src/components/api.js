import axios from "axios";

// Base URL for the backend API
const BASE_URL = "http://127.0.0.1:8000";


// Function to handle API responses with error info
const handleApiResponse = async (request) => {
  try {
      const response = await request();
    return response.data;
  } catch (error) {
    console.error("API Error:", error);
      if(error.response && error.response.data){
           // Pass the error detail for the catch block
          throw new Error(`${error.message}: ${JSON.stringify(error.response.data)}`)
    }
       throw new Error(`API Error: Unable to complete request`)
  }
}


// ✅ Fix: Ensure Predict API sends `customer_location`
export const predictDeliveryTime = async (orderPriority, customerLocation) => {
    return await handleApiResponse(() => axios.post(`${BASE_URL}/predict`, {
        order_priority: orderPriority,
        customer_location: customerLocation
    }));
};


// ✅ Fix: Ensure Optimize API works properly
export const fetchOptimizedRoutes = async (numVehicles) => {
      return await handleApiResponse(() => axios.post(`${BASE_URL}/optimize`, {
      num_vehicles: numVehicles
        }));
};


// Fetch deliveries
export const fetchDeliveries = async () => {
    return await handleApiResponse(() => axios.get(`${BASE_URL}/deliveries`));
};


// Retrain Model
export const retrainModel = async () => {
      return await handleApiResponse(() => axios.post(`${BASE_URL}/train_model`));
};