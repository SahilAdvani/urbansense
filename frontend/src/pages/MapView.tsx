import React, { useEffect, useState, useRef } from "react";
import { MapContainer, TileLayer, Marker, Popup, Tooltip, useMap } from "react-leaflet";
import "leaflet/dist/leaflet.css";
import L from "leaflet";
import { useNavigate } from "react-router-dom";
import api from "../utils/api";
import { useCity } from "../hooks/useCity";

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

// Canvas-based Heatmap Overlay for smooth gradient maps (AccuWeather/Google style)
const HeatmapOverlay: React.FC<{ points: { lat: number; lng: number; intensity: number }[] }> = ({ points }) => {
  const map = useMap();
  const canvasRef = useRef<HTMLCanvasElement | null>(null);

  useEffect(() => {
    const pane = map.getPane("overlayPane");
    if (!pane) return;

    // Create a high-performance transparent Canvas overlay
    const canvas = document.createElement("canvas");
    canvas.style.position = "absolute";
    canvas.style.top = "0";
    canvas.style.left = "0";
    canvas.style.pointerEvents = "none";
    canvas.style.opacity = "0.6";
    pane.appendChild(canvas);
    canvasRef.current = canvas;

    const draw = () => {
      const size = map.getSize();
      canvas.width = size.x;
      canvas.height = size.y;
      
      const ctx = canvas.getContext("2d");
      if (!ctx) return;
      ctx.clearRect(0, 0, canvas.width, canvas.height);

      // Reposition canvas relative to current map movement bounds
      const topLeft = map.containerPointToLayerPoint([0, 0]);
      L.DomUtil.setPosition(canvas, topLeft);

      points.forEach(point => {
        if (point.lat === null || point.lng === null) return;
        const latlng = L.latLng(point.lat, point.lng);
        const containerPoint = map.latLngToContainerPoint(latlng);
        
        // Define a smooth radial glow based on the AQI level
        // Radius of pollution dispersion scales slightly with intensity
        const radius = Math.min(130, Math.max(50, point.intensity * 0.45));
        const gradient = ctx.createRadialGradient(
          containerPoint.x, containerPoint.y, 0,
          containerPoint.x, containerPoint.y, radius
        );

        // Map AQI values to RGB coordinates
        let rgbColor = "16, 185, 129"; // Green
        if (point.intensity > 300) {
          rgbColor = "244, 63, 94"; // Rose/Hazardous
        } else if (point.intensity > 200) {
          rgbColor = "168, 85, 247"; // Purple/Very Poor
        } else if (point.intensity > 150) {
          rgbColor = "239, 68, 68"; // Red/Poor
        } else if (point.intensity > 100) {
          rgbColor = "249, 115, 22"; // Orange/Moderate
        } else if (point.intensity > 50) {
          rgbColor = "20, 184, 166"; // Teal/Satisfactory
        }

        gradient.addColorStop(0, `rgba(${rgbColor}, 0.85)`);
        gradient.addColorStop(0.35, `rgba(${rgbColor}, 0.45)`);
        gradient.addColorStop(1, `rgba(${rgbColor}, 0)`);

        ctx.fillStyle = gradient;
        ctx.beginPath();
        ctx.arc(containerPoint.x, containerPoint.y, radius, 0, Math.PI * 2);
        ctx.fill();
      });
    };

    draw();

    // Re-draw canvas dynamically when users zoom, pan, or resize the map
    map.on("move", draw);
    map.on("resize", draw);

    return () => {
      map.off("move", draw);
      map.off("resize", draw);
      if (canvas.parentNode) {
        canvas.parentNode.removeChild(canvas);
      }
    };
  }, [map, points]);

  return null;
};

export const MapView: React.FC = () => {
  const { activeCity } = useCity();
  const [wards, setWards] = useState<Ward[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [interventions, setInterventions] = useState<any[]>([]);
  const [facilities, setFacilities] = useState<any[]>([]);
  const [showInfrastructure, setShowInfrastructure] = useState(false);
  const [showInterventions, setShowInterventions] = useState(false);
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
    
    const fetchInterventions = async () => {
      try {
        const response = await api.get("/recommendations/interventions", {
          params: { city_id: activeCity.id, status: "active" }
        });
        setInterventions(response.data);
      } catch (err) {
        console.error("Failed to load active map interventions", err);
      }
    };

    const fetchFacilities = async () => {
      try {
        const response = await api.get(`/cities/${activeCity.id}/facilities`);
        setFacilities(response.data);
      } catch (err) {
        console.error("Failed to load OSM facilities", err);
      }
    };

    fetchWards();
    fetchInterventions();
    fetchFacilities();
  }, [activeCity]);

  const handleMarkerClick = (wardId: number) => {
    navigate(`/ward/${wardId}`);
  };

  const getAqiColor = (aqi: number) => {
    if (aqi <= 50) return "#10b981"; // Good (Green)
    if (aqi <= 100) return "#14b8a6"; // Satisfactory (Teal)
    if (aqi <= 150) return "#eab308"; // Moderate (Yellow)
    if (aqi <= 200) return "#f97316"; // Poor (Orange)
    if (aqi <= 300) return "#a855f7"; // Very Poor (Purple)
    return "#f43f5e"; // Severe (Rose)
  };

  // Generate beautiful pulsing markers for monitoring stations
  const createPulsingIcon = (aqi: number) => {
    const color = getAqiColor(aqi);
    return L.divIcon({
      html: `
        <div class="relative flex items-center justify-center w-6 h-6">
          <span class="animate-ping absolute inline-flex h-5 w-5 rounded-full opacity-60" style="background-color: ${color}"></span>
          <span class="relative inline-flex rounded-full h-3.5 w-3.5 border-2 border-slate-900 shadow-md" style="background-color: ${color}"></span>
        </div>
      `,
      className: "custom-glowing-marker",
      iconSize: [24, 24],
      iconAnchor: [12, 12]
    });
  };

  // Custom Red Cross Icon for Hospitals
  const hospitalIcon = L.divIcon({
    html: `
      <div class="relative flex items-center justify-center w-6 h-6 bg-slate-950 border-2 border-rose-500 rounded-full shadow-lg text-rose-500 font-bold text-xs select-none">
        +
      </div>
    `,
    className: "custom-hospital-marker",
    iconSize: [24, 24],
    iconAnchor: [12, 12]
  });

  // Custom Blue Cap Icon for Schools
  const schoolIcon = L.divIcon({
    html: `
      <div class="relative flex items-center justify-center w-6 h-6 bg-slate-950 border-2 border-cyan-500 rounded-full shadow-lg text-cyan-400 text-[10px] select-none">
        🎓
      </div>
    `,
    className: "custom-school-marker",
    iconSize: [24, 24],
    iconAnchor: [12, 12]
  });

  // Custom Green Gear Icon for Active Interventions
  const activeInterventionIcon = L.divIcon({
    html: `
      <div class="relative flex items-center justify-center w-6 h-6 bg-slate-950 border-2 border-emerald-500 rounded-full shadow-lg text-emerald-400 text-[10px] select-none animate-pulse">
        ⚙️
      </div>
    `,
    className: "custom-intervention-marker",
    iconSize: [24, 24],
    iconAnchor: [12, 12]
  });

  const defaultCenter: [number, number] = [28.6139, 77.2090]; // Delhi
  const center: [number, number] = activeCity 
    ? [activeCity.latitude, activeCity.longitude]
    : defaultCenter;

  // Map suburb elements to points payload for our Canvas heatmap
  const heatmapPoints = wards.map(w => ({
    lat: w.latitude,
    lng: w.longitude,
    intensity: w.aqi
  }));

  return (
    <div className="h-[calc(100vh-140px)] w-full bg-slate-950 flex flex-col rounded-2xl overflow-hidden border border-slate-900 shadow-2xl">
      <div className="px-6 py-4 border-b border-slate-900 bg-slate-900/60 backdrop-blur-md flex flex-col lg:flex-row justify-between items-start lg:items-center gap-4 shrink-0">
        <div>
          <h1 className="text-xl font-bold text-white tracking-tight">Geospatial Intelligence Map</h1>
          <p className="text-xs text-slate-400 mt-0.5">
            {activeCity ? `${activeCity.name} – ` : ""}Continuous monitoring heatmap and local station details
          </p>
        </div>
        
        {/* Overlays and Legend Controls */}
        <div className="flex flex-wrap items-center gap-4">
          <div className="flex items-center gap-3 bg-slate-900/80 px-3.5 py-1.5 rounded-xl border border-slate-800 text-xs font-semibold">
            <span className="text-slate-500 uppercase tracking-wider mr-1">Overlays:</span>
            <label className="flex items-center gap-1.5 text-slate-300 cursor-pointer select-none">
              <input 
                type="checkbox" 
                checked={showInfrastructure} 
                onChange={(e) => setShowInfrastructure(e.target.checked)}
                className="rounded border-slate-700 bg-slate-800 text-violet-600 focus:ring-violet-500 w-3.5 h-3.5" 
              />
              Sensitive Facilities
            </label>
            <label className="flex items-center gap-1.5 text-slate-300 cursor-pointer select-none">
              <input 
                type="checkbox" 
                checked={showInterventions} 
                onChange={(e) => setShowInterventions(e.target.checked)}
                className="rounded border-slate-700 bg-slate-800 text-violet-600 focus:ring-violet-500 w-3.5 h-3.5" 
              />
              Active Interventions
            </label>
          </div>

          <div className="flex items-center gap-3 bg-slate-950/80 px-3.5 py-1.5 rounded-xl border border-slate-800 text-[10px] font-semibold">
            <span className="text-slate-500 uppercase tracking-wider mr-1">AQI Level:</span>
            <span className="flex items-center gap-1"><span className="w-2.5 h-2.5 rounded-full bg-emerald-500"></span>&lt;50</span>
            <span className="flex items-center gap-1"><span className="w-2.5 h-2.5 rounded-full bg-teal-500"></span>51-100</span>
            <span className="flex items-center gap-1"><span className="w-2.5 h-2.5 rounded-full bg-yellow-500"></span>101-150</span>
            <span className="flex items-center gap-1"><span className="w-2.5 h-2.5 rounded-full bg-orange-500"></span>151-200</span>
            <span className="flex items-center gap-1"><span className="w-2.5 h-2.5 rounded-full bg-purple-500"></span>201-300</span>
            <span className="flex items-center gap-1"><span className="w-2.5 h-2.5 rounded-full bg-rose-500"></span>300+</span>
          </div>
        </div>
      </div>
 
       {loading && (
         <div className="flex-grow flex items-center justify-center text-slate-400">
           Loading map assets…
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
             
             {/* Layer 1: Smooth Canvas Heatmap Overlay */}
             {activeCity?.has_wards && <HeatmapOverlay points={heatmapPoints} />}
 
             {/* Layer 2: Interactive Glowing Suburb Stations */}
             {wards.map((ward) => {
               if (ward.latitude === null || ward.longitude === null) return null;
               
               const cleanSuburbName = ward.name.includes(" - ") 
                 ? ward.name.split(" - ")[1] 
                 : ward.name;
 
               return (
                 <React.Fragment key={ward.id}>
                   <Marker
                     position={[ward.latitude, ward.longitude]}
                     icon={createPulsingIcon(ward.aqi)}
                     eventHandlers={{ click: () => handleMarkerClick(ward.id) }}
                   >
                     <Tooltip direction="top" offset={[0, -10]} opacity={0.9}>
                       <div className="text-slate-900 font-semibold text-xs p-0.5">
                         <p className="font-bold">{cleanSuburbName}</p>
                         <p className="text-[10px] text-slate-500 mt-0.5">AQI: <span className="font-bold text-slate-800">{ward.aqi}</span> • Click for details</p>
                       </div>
                     </Tooltip>
                     <Popup>
                       <div className="text-slate-900 font-semibold p-1">
                         <p className="text-sm font-extrabold">{cleanSuburbName}</p>
                         <p className="text-xs mt-1">
                           Average AQI: <span className="font-bold text-slate-950">{ward.aqi}</span>
                         </p>
                         <p className="text-[10px] text-violet-600 mt-2 font-bold cursor-pointer hover:underline">
                           Click to view localized analytics →
                         </p>
                       </div>
                     </Popup>
                   </Marker>

                   {/* Layer 4: Active Interventions Layer */}
                   {showInterventions && interventions.some((i: any) => i.ward_id === ward.id) && (
                     <Marker
                       position={[ward.latitude - 0.002, ward.longitude - 0.002]}
                       icon={activeInterventionIcon}
                     >
                       <Popup>
                         <div className="text-slate-900 p-1">
                           <p className="text-xs font-extrabold text-emerald-600">⚙️ Active Intervention Logged</p>
                           <p className="text-[10px] text-slate-600 mt-1">
                             <b>Action:</b> {interventions.find((i: any) => i.ward_id === ward.id)?.title}
                           </p>
                           <p className="text-[9px] text-slate-400 mt-1 font-mono">
                             Status: ACTIVE • Running in this sector.
                           </p>
                         </div>
                       </Popup>
                     </Marker>
                   )}
                 </React.Fragment>
               );
             })}

             {/* Layer 3: Real Sensitive Infrastructure Layer (Hospitals & Schools) */}
             {showInfrastructure && facilities.map((f, idx) => (
               <Marker
                 key={`facility-${idx}`}
                 position={[f.latitude, f.longitude]}
                 icon={f.type === "hospital" ? hospitalIcon : schoolIcon}
               >
                 <Popup>
                   <div className="text-slate-900 p-1">
                     <p className="text-xs font-extrabold text-slate-800">
                       {f.type === "hospital" ? "🏥" : "🏫"} {f.name}
                     </p>
                     <p className="text-[10px] text-slate-600 mt-1 uppercase font-semibold">
                       Type: {f.type}
                     </p>
                     <p className="text-[9px] text-slate-400 mt-1 font-mono">
                       Location: {f.latitude.toFixed(4)}, {f.longitude.toFixed(4)}
                     </p>
                   </div>
                 </Popup>
               </Marker>
             ))}
           </MapContainer>
 
           {/* Level 1 Falling Back Banner Overlay */}
           {!activeCity?.has_wards && (
             <div className="absolute bottom-6 left-6 right-6 bg-slate-900/90 border border-slate-800 backdrop-blur-md px-6 py-4 rounded-2xl shadow-2xl z-[1000] flex justify-between items-center">
               <div>
                 <h4 className="text-sm font-bold text-white">City-Level Intelligence Mode</h4>
                 <p className="text-xs text-slate-400 mt-0.5">
                   Detailed local suburb sensors are not yet mapped for {activeCity?.name}. Displaying regional monitoring metrics.
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
