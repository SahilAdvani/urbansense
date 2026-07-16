import React, { useEffect, useState } from "react";
import { MapContainer, TileLayer, Marker, Popup, GeoJSON, useMap } from "react-leaflet";
import "leaflet/dist/leaflet.css";
import L from "leaflet";
import { useNavigate } from "react-router-dom";
import api from "../utils/api";
import { useCity } from "../hooks/useCity";

// Fix default marker icons for Leaflet in Vite/Webpack bundling
delete (L.Icon.Default.prototype as any)._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: new URL("leaflet/dist/images/marker-icon-2x.png", import.meta.url).href,
  iconUrl: new URL("leaflet/dist/images/marker-icon.png", import.meta.url).href,
  shadowUrl: new URL("leaflet/dist/images/marker-shadow.png", import.meta.url).href,
});

interface Ward {
  id: number;
  name: string;
  latitude: number;
  longitude: number;
  geojson_boundary: any;
  aqi: number;
}

// Helper component to dynamically change Leaflet map viewport when active city changes
const ChangeMapView: React.FC<{ center: [number, number] }> = ({ center }) => {
  const map = useMap();
  useEffect(() => {
    map.setView(center, 12);
  }, [center, map]);
  return null;
};

export const MapView: React.FC = () => {
  const { activeCity } = useCity();
  const [wards, setWards] = useState<Ward[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const navigate = useNavigate();

  useEffect(() => {
    if (!activeCity) return;
    
    const fetchWards = async () => {
      setLoading(true);
      try {
        const response = await api.get<Ward[]>("/wards", {
          params: { city_id: activeCity.id }
        });
        setWards(response.data);
        setError(null);
      } catch (err) {
        console.error("Failed to load wards", err);
        setError("Could not load ward data from the server.");
      } finally {
        setLoading(false);
      }
    };
    fetchWards();
  }, [activeCity]);

  const handleMarkerClick = (wardId: number) => {
    navigate(`/ward/${wardId}`);
  };

  const getAqiColor = (aqi: number) => {
    if (aqi <= 50) return "#10b981"; // Good (Green)
    if (aqi <= 100) return "#14b8a6"; // Satisfactory (Teal)
    if (aqi <= 200) return "#f59e0b"; // Moderate (Yellow)
    if (aqi <= 300) return "#f97316"; // Poor (Orange)
    return "#f43f5e"; // Very Poor (Red)
  };

  const defaultCenter: [number, number] = [28.6139, 77.2090]; // Delhi
  const center: [number, number] = activeCity 
    ? [activeCity.latitude, activeCity.longitude]
    : defaultCenter;

  return (
    <div className="h-[calc(100vh-140px)] w-full bg-slate-950 flex flex-col rounded-2xl overflow-hidden border border-slate-900">
      <div className="px-6 py-4 border-b border-slate-900 bg-slate-900/60 backdrop-blur-md flex justify-between items-center shrink-0">
        <div>
          <h1 className="text-xl font-bold text-white">Geospatial Intelligence Map</h1>
          <p className="text-xs text-slate-400 mt-0.5">
            {activeCity ? `${activeCity.name} – ` : ""}Ward-level pollution heatmaps and monitoring stations
          </p>
        </div>
        
        {/* Heatmap Legend */}
        <div className="flex items-center gap-3 bg-slate-950/80 px-3.5 py-1.5 rounded-xl border border-slate-800 text-[10px] font-semibold">
          <span className="text-slate-500 uppercase tracking-wider mr-1">AQI Level:</span>
          <span className="flex items-center gap-1"><span className="w-2.5 h-2.5 rounded-full bg-emerald-500"></span>&lt;50</span>
          <span className="flex items-center gap-1"><span className="w-2.5 h-2.5 rounded-full bg-teal-500"></span>51-100</span>
          <span className="flex items-center gap-1"><span className="w-2.5 h-2.5 rounded-full bg-amber-500"></span>101-200</span>
          <span className="flex items-center gap-1"><span className="w-2.5 h-2.5 rounded-full bg-orange-500"></span>201-300</span>
          <span className="flex items-center gap-1"><span className="w-2.5 h-2.5 rounded-full bg-rose-500"></span>300+</span>
        </div>
      </div>

      {loading && (
        <div className="flex-grow flex items-center justify-center text-slate-400">
          Loading map data…
        </div>
      )}

      {error && (
        <div className="flex-grow flex items-center justify-center text-rose-400">
          {error}
        </div>
      )}

      {!loading && !error && (
        <div className="flex-grow relative w-full h-full">
          <MapContainer center={center} zoom={12} className="h-full w-full">
            <ChangeMapView center={center} />
            
            <TileLayer
              attribution='&copy; <a href="https://www.openstreetmap.org/">OpenStreetMap</a> contributors'
              url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
            />
            
            {/* Layer 2: Ward Boundaries Heatmap (when available) */}
            {activeCity?.has_wards && wards.map((ward) => {
              if (!ward.geojson_boundary) return null;
              
              const color = getAqiColor(ward.aqi);
              const pathOptions = {
                fillColor: color,
                fillOpacity: 0.5,
                color: "#1e293b",
                weight: 1.5,
              };

              return (
                <GeoJSON
                  key={ward.id}
                  data={ward.geojson_boundary}
                  style={pathOptions}
                  eventHandlers={{
                    click: () => handleMarkerClick(ward.id),
                    mouseover: (e) => {
                      const layer = e.target;
                      layer.setStyle({ fillOpacity: 0.7, weight: 2.5 });
                    },
                    mouseout: (e) => {
                      const layer = e.target;
                      layer.setStyle({ fillOpacity: 0.5, weight: 1.5 });
                    }
                  }}
                >
                  <Popup>
                    <div className="text-slate-900 font-semibold p-1">
                      <p className="text-sm font-bold">{ward.name}</p>
                      <p className="text-xs mt-1">Average AQI: <span className="font-bold">{ward.aqi}</span></p>
                      <p className="text-[10px] text-violet-600 mt-2 font-bold cursor-pointer hover:underline">
                        Click to view analytics →
                      </p>
                    </div>
                  </Popup>
                </GeoJSON>
              );
            })}

            {/* Layer 1: Central City Marker (always shown for context/monitoring station) */}
            {wards.map((ward) => {
              // Only render standard markers when polygons are not present (Level 1) or on the ward centroid
              if (activeCity?.has_wards && ward.geojson_boundary) return null;
              if (ward.latitude === null || ward.longitude === null) return null;
              
              return (
                <Marker
                  key={ward.id}

                  position={[ward.latitude, ward.longitude]}
                  eventHandlers={{ click: () => handleMarkerClick(ward.id) }}
                >
                  <Popup>
                    <div className="text-slate-900 font-semibold p-1">
                      <p className="text-sm font-bold">{ward.name}</p>
                      <p className="text-xs mt-1">Average AQI: <span className="font-bold">{ward.aqi}</span></p>
                      <p className="text-[10px] text-violet-600 mt-2 font-bold cursor-pointer hover:underline">
                        Click to view analytics →
                      </p>
                    </div>
                  </Popup>
                </Marker>
              );
            })}
          </MapContainer>

          {/* Level 1 Falling Back Banner Overlay */}
          {!activeCity?.has_wards && (
            <div className="absolute bottom-6 left-6 right-6 bg-slate-900/90 border border-slate-800 backdrop-blur-md px-6 py-4 rounded-2xl shadow-2xl z-[1000] flex justify-between items-center">
              <div>
                <h4 className="text-sm font-bold text-white">City-Level Intelligence Mode</h4>
                <p className="text-xs text-slate-400 mt-0.5">
                  Detailed geospatial ward boundaries are not yet seeded for {activeCity?.name}. Displaying regional monitoring sensors.
                </p>
              </div>
              <span className="text-[10px] font-bold bg-violet-600/20 text-violet-400 px-2 py-1 rounded border border-violet-500/20 uppercase tracking-wider">
                Level 1 Active
              </span>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default MapView;
