import React, { useState, useEffect } from "react";
import { predictDeliveryTime, fetchDeliveries } from "./api";

const DeliveryInfo = ({onSelectChange}) => {
    const [orderPriority, setOrderPriority] = useState("Medium");
  const [predictedTime, setPredictedTime] = useState("");
   const [customerLocation, setCustomerLocation] = useState("");
    const [allDeliveries, setAllDeliveries] = useState([]);

  useEffect(() => {
      const fetchData = async () => {
        try {
            const data = await fetchDeliveries();
           setAllDeliveries(data);
         if (data && data.length > 0) {
           setCustomerLocation(data[0].customer_location);
            }
          } catch (error) {
          console.error("Error fetching deliveries:", error);
         }
       };
      fetchData();
 }, []);

 const handlePredictTime = async () => {
     try {
       const response = await predictDeliveryTime(orderPriority, customerLocation);
       setPredictedTime(response);
        } catch (error) {
           console.error("Prediction failed :", error.message);
           setPredictedTime(`Error: ${error.message}`);
        }
  };

   const handleLocationChange = (e) => {
        const value = e.target.value
      setCustomerLocation(value);
       onSelectChange(value)
    }
  return (
   <div>
        <h1>Predict Delivery Time</h1>
          <label>
           Order Priority:
             <select value={orderPriority} onChange={(e) => setOrderPriority(e.target.value)}>
               <option value="High">High</option>
                <option value="Medium">Medium</option>
                  <option value="Low">Low</option>
           </select>
           </label>
            <label>
           Customer Location:
            <select value={customerLocation} onChange={handleLocationChange}>
             {allDeliveries.map((delivery, index) => (
              <option value={delivery.customer_location} key={index}>
                 {delivery.customer_location}
                 </option>
                ))}
               </select>
         </label>
       <button onClick={handlePredictTime}>Predict Time</button>
             {predictedTime && <p>Estimated Delivery Time: {predictedTime} minutes</p>}
    </div>
   );
};

export default DeliveryInfo;