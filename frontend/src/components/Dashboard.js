import React, { useEffect, useState } from "react";
import { fetchDeliveries, retrainModel } from "./api";

const Dashboard = () => {
  const [deliveries, setDeliveries] = useState([]);
  const [message, setMessage] = useState("");

  useEffect(() => {
    // Fetch deliveries when the component loads
    const fetchData = async () => {
      try {
        const data = await fetchDeliveries();
        setDeliveries(data);
      } catch (error) {
        console.error(error);
      }
    };
    fetchData();
  }, []);

  const handleRetrainModel = async () => {
    try {
      const response = await retrainModel();
      setMessage(response);
    } catch (error) {
      console.error(error);
    }
  };

    return (
    <div>
        <h1>Dashboard</h1>
        <button onClick={handleRetrainModel}>Retrain Model</button>
      {message && <p>{message}</p>}
      <table style={{ width: '100%', borderCollapse: 'collapse', marginTop: '20px' }}>
                <thead>
                    <tr style={{ borderBottom: '1px solid #ddd', fontWeight: 'bold' }}>
                        <th style={{ padding: '10px', textAlign: 'left' }}>Order ID</th>
                    <th style={{ padding: '10px', textAlign: 'left' }}>Customer Location</th>
                    <th style={{ padding: '10px', textAlign: 'left' }}>Priority</th>
                    </tr>
                </thead>
                <tbody>
                {deliveries.map((delivery, index) => (
                     <tr key={index} style={{ borderBottom: '1px solid #eee' }}>
                    <td style={{ padding: '10px', textAlign: 'left' }}>{delivery.order_id}</td>
                      <td style={{ padding: '10px', textAlign: 'left' }}>{delivery.customer_location}</td>
                      <td style={{ padding: '10px', textAlign: 'left' }}>{delivery.order_priority}</td>
                    </tr>
                ))}
                </tbody>
        </table>
    </div>
  );
};

export default Dashboard;