import React from "react";
import GoogleMapComponent from "./components/GooglemapComponent";
import DeliveryInfo from "./components/Deliveryinfo"; // <-- Update the import

function App() {
  return (
    <div className="App">
      <h1>📦 Logistics Delivery System</h1>
      <GoogleMapComponent />
      <DeliveryInfo />
    </div>
  );
}

export default App;