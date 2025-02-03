import React, { useEffect, useRef, useState } from "react";
import mapboxgl from "mapbox-gl";
import { fetchOptimizedRoutes, fetchDeliveries } from "./api";
import "mapbox-gl/dist/mapbox-gl.css";
import DeliveryInfo from "./Deliveryinfo"; // We now need the import for `<DeliveryInfo/>`

mapboxgl.accessToken = "pk.eyJ1IjoiYWpyaWNoaWUiLCJhIjoiY202bWN4aHNqMGc3djJrcGJmOWVtODU3MCJ9.6bguq83MhOWy_12lk_cJUg";

const GooglemapComponent = () => {
    const mapContainerRef = useRef(null);
    const [map, setMap] = useState(null);
    const [allDeliveries, setAllDeliveries] = useState([])
    const [loading, setLoading] = useState(false);
    const [selectedCustomerLocation, setSelectedCustomerLocation] = useState(null);


  useEffect(() => {
      const fetchData = async () => {
       try {
         const data = await fetchDeliveries();
         setAllDeliveries(data);
       } catch (error) {
             console.error("Error fetching deliveries from backend: ", error);
         }
    }
        fetchData();
     }, []);

  useEffect(() => {
    const mapInstance = new mapboxgl.Map({
        container: mapContainerRef.current,
            style: "mapbox://styles/mapbox/streets-v11",
           center: [78.486671, 17.385044],
         zoom: 5,
     });
    setMap(mapInstance);
         return () => mapInstance.remove();
 }, []);

    const handleFetchRoutes = async () => {
        setLoading(true);
      try {
            if (!selectedCustomerLocation){
              alert ("No customer's location has been selected")
                 return
                }
           const optimizedRoutes = await fetchOptimizedRoutes(2);
           if (!map) return;
            for(let i = 0; i < allDeliveries.length; i++){
               if (map.getLayer(`route-${i}`)) {
                     map.removeLayer(`route-${i}`);
                }
          }
              const markers = document.querySelectorAll('.mapboxgl-marker');
              markers.forEach(marker => marker.remove());


            for(let routeIndex = 0; routeIndex < optimizedRoutes.length; routeIndex ++){
              let route = optimizedRoutes[routeIndex];
                const coordinates = route.map((locationIndex) => {
                    const delivery  = allDeliveries[locationIndex]

                     if (!delivery){
                         return null
                   }
                  if(delivery.customer_location !== selectedCustomerLocation) {
                    return null
                  }
                    return [delivery.customer_longitude, delivery.customer_latitude]
                  });
                  const filteredCoordinates = coordinates.filter(coord => coord !== null);


            const geoJson = {
                  type: "Feature",
                  geometry: {
                   type: "LineString",
                  coordinates: filteredCoordinates,
                    },
                  };

                map.addLayer({
                     id: `route-${routeIndex}`,
                   type: "line",
                 source: {
                       type: "geojson",
                       data: geoJson,
                      },
                  layout: {
                        "line-join": "round",
                         "line-cap": "round",
                    },
                   paint: {
                     "line-color": "#3b9ddd",
                     "line-width": 4,
                     },
                });
              filteredCoordinates.forEach(([lng, lat]) => {
                  new mapboxgl.Marker().setLngLat([lng, lat]).addTo(map);
               });
         }
      } catch (error) {
         console.error("Error fetching optimized routes:", error);
       } finally {
       setLoading(false);
        }
   };


 const onSelectChange = (customerLocation) => {
      setSelectedCustomerLocation(customerLocation)
    }


 return (
      <div>
          <h1>Mapbox Optimized Routes</h1>
           <button onClick={handleFetchRoutes} disabled={loading}>
             {loading ? "Loading Routes" : "Fetch Routes"}
          </button>
            <div ref={mapContainerRef} style={{ height: "500px", width: "100%" }} />
        <DeliveryInfo onSelectChange={onSelectChange}/>
       </div>
    );
};
export default GooglemapComponent;