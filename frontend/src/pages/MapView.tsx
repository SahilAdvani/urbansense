import React, { useEffect, useState } from "react";
import { MapContainer, TileLayer, Marker, Popup } from "react-leaflet";
import "leaflet/dist/leaflet.css";
import L from "leaflet";
import { useNavigate } from "react-router-dom";
import api from "../utils/api";

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
}

export const MapView: React.FC = () => {
  const [wards, setWards] = useState<Ward[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const navigate = useNavigate();

  useEffect(() => {
    const fetchWards = async () => {
      try {
        const response = await api.get("/wards");
        setWards(response.data);
      } catch (err) {
        console.error("Failed to load wards", err);
        setError("Could not load ward data from the server.");
      } finally {
        setLoading(false);
      }
    };
    fetchWards();
  }, []);

  const handleMarkerClick = (wardId: number) => {
    navigate(`/ward/${wardId}`);
  };

  // Default centre on New Delhi area (matches mock ward data)
  const defaultCenter: [number, number] = [28.61, 77.21];
  const center: [number, number] =
    wards.length > 0
      ? [
          wards[0].latitude ?? defaultCenter[0],
          wards[0].longitude ?? defaultCenter[1],
        ]
      : defaultCenter;

  return (
    <div className="h-screen w-full bg-slate-950 flex flex-col">
      <div className="px-6 py-4 border-b border-slate-800 bg-slate-900/60 backdrop-blur-md">
        <h1 className="text-xl font-bold text-white">Geospatial Intelligence Map</h1>
        <p className="text-xs text-slate-400 mt-0.5">Ward-level pollution heatmaps and monitoring stations</p>
      </div>

      {loading && (
        <div className="flex-1 flex items-center justify-center text-slate-400">
          Loading map data…
        </div>
      )}

      {error && (
        <div className="flex-1 flex items-center justify-center text-rose-400">
          {error}
        </div>
      )}

      {!loading && !error && (
        <div className="flex-1">
          <MapContainer center={center} zoom={12} className="h-full w-full">
            <TileLayer
              attribution='&copy; <a href="https://www.openstreetmap.org/">OpenStreetMap</a> contributors'
              url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
            />
            {wards.map((ward) => (
              <Marker
                key={ward.id}
                position={[ward.latitude, ward.longitude]}
                eventHandlers={{ click: () => handleMarkerClick(ward.id) }}
              >
                <Popup>{ward.name}</Popup>
              </Marker>
            ))}
          </MapContainer>
        </div>
      )}
    </div>
  );
};
