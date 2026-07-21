import React, { useEffect, useState, useCallback } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { 
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, 
  LineChart, Line 
} from "recharts";
import { 
  AlertTriangle, ShieldAlert, Sparkles, Send, CheckCircle2, ChevronLeft, 
  Activity, HelpCircle 
} from "lucide-react";
import api from "../utils/api";

interface WardStat {
  metric: string;
  value: number;
}

interface WardInfo {
  id: number;
  name: string;
}

interface ForecastPoint {
  timestamp: string;
  predicted_aqi: number;
  confidence_lower: number;
  confidence_upper: number;
}

interface AIRec {
  id: number;
  ward_id: number;
  trigger_aqi: number;
  primary_pollutant: string;
  estimated_source: string | null;
  confidence_score: number | null;
  recommendation_text: string;
  action_plan: { steps?: string[] } | null;
  status: string;
  timestamp: string;
}

interface CitizenAdvisory {
  id: number;
  ward_id: number;
  title: string;
  advisory_text: string;
  risk_level: string;
  target_population: string;
  status: string;
  created_at: string;
}

export const WardDetail: React.FC = () => {
  const { wardId } = useParams<{ wardId: string }>();
  const navigate = useNavigate();
  const [stats, setStats] = useState<WardStat[]>([]);
  const [wardName, setWardName] = useState<string>("");
  const [loading, setLoading] = useState(true);
  const [analyzing, setAnalyzing] = useState(false);
  const [publishing, setPublishing] = useState<number | null>(null);
  const [implementing, setImplementing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // AI & Forecasting states
  const [forecast, setForecast] = useState<ForecastPoint[]>([]);
  const [activeRecs, setActiveRecs] = useState<AIRec[]>([]);
  const [advisories, setAdvisories] = useState<CitizenAdvisory[]>([]);
  const [sourceReasoning, setSourceReasoning] = useState<string>("");
  const [loggedInterventions, setLoggedInterventions] = useState<{ id: number; title: string }[]>([]);

  const getCleanName = (name: string) => {
    return name.includes(" - ") ? name.split(" - ")[1] : name;
  };

  const getAqiColor = (aqi: number) => {
    if (aqi <= 50) return "bg-emerald-500/20 text-emerald-400 border-emerald-500/30";
    if (aqi <= 100) return "bg-teal-500/20 text-teal-400 border-teal-500/30";
    if (aqi <= 200) return "bg-amber-500/20 text-amber-400 border-amber-500/30";
    if (aqi <= 300) return "bg-orange-500/20 text-orange-400 border-orange-500/30";
    return "bg-rose-500/20 text-rose-400 border-rose-500/30";
  };

  const fetchWardData = useCallback(async () => {
    if (!wardId) return;
    try {
      const [wardRes, statsRes, forecastRes, recsRes, advisoriesRes, interventionsRes] = await Promise.all([
        api.get<WardInfo>(`/wards/${wardId}`),
        api.get<WardStat[]>(`/wards/${wardId}/stats`),
        api.get<ForecastPoint[]>(`/forecasting/${wardId}`),
        api.get<AIRec[]>("/recommendations", { params: { ward_id: wardId } }),
        api.get<CitizenAdvisory[]>("/recommendations/advisories", { params: { ward_id: wardId } }),
        api.get<{ id: number; title: string }[]>("/recommendations/interventions", { params: { ward_id: wardId } })
      ]);
      
      setWardName(wardRes.data.name);
      setStats(statsRes.data);
      setForecast(forecastRes.data);
      setActiveRecs(recsRes.data);
      setAdvisories(advisoriesRes.data);
      setLoggedInterventions(interventionsRes.data);
      
      // Auto-extract source explanation if available
      if (recsRes.data.length > 0) {
        setSourceReasoning("Analysis generated from historical data.");
      }
      setError(null);
    } catch (err) {
      console.error("Failed to load ward data", err);
      setError("Could not load ward details.");
    } finally {
      setLoading(false);
    }
  }, [wardId]);

  useEffect(() => {
    setLoading(true);
    fetchWardData();
  }, [wardId, fetchWardData]);

  // Request Groq AI recommendation on-demand
  const handleAnalyze = async () => {
    setAnalyzing(true);
    try {
      const res = await api.post(`/recommendations/generate/${wardId}`);
      setSourceReasoning(res.data.source_reasoning);
      await fetchWardData();
    } catch (err) {
      console.error("Analysis failed", err);
      alert("Failed to analyze coordinates with Groq AI.");
    } finally {
      setAnalyzing(false);
    }
  };

  // Implement intervention
  const handleImplementIntervention = async (title: string, type: string) => {
    setImplementing(true);
    try {
      await api.post("/recommendations/interventions", {
        ward_id: Number(wardId),
        title: `Executed: ${title}`,
        type: type,
        description: "Administrative action initiated via AI Recommendations Command Panel."
      });
      await fetchWardData();
      alert("Intervention logged successfully and status marked as Implemented.");
    } catch (err) {
      console.error("Intervention log failed", err);
    } finally {
      setImplementing(false);
    }
  };

  // Publish advisory
  const handlePublishAdvisory = async (advisoryId: number) => {
    setPublishing(advisoryId);
    try {
      await api.post(`/recommendations/advisories/${advisoryId}/publish`);
      await fetchWardData();
      alert("Citizen Advisory published successfully to regional alerts feed!");
    } catch (err) {
      console.error("Advisory publication failed", err);
    } finally {
      setPublishing(null);
    }
  };

  // Parse percentages from raw string: e.g. "Traffic: 45%, Industry: 30%, ..."
  const parseSourcePercent = (estimatedSource: string | null) => {
    if (!estimatedSource) return { Traffic: 30, Industrial: 20, Construction: 25, Dust: 20, Biomass: 5 };
    const values: Record<string, number> = {};
    const parts = estimatedSource.split(",");
    parts.forEach(p => {
      const bits = p.split(":");
      if (bits.length === 2) {
        const label = bits[0].trim();
        const val = parseFloat(bits[1].replace("%", "").trim());
        values[label] = val;
      }
    });
    return {
      Traffic: values["Traffic"] ?? 30,
      Industrial: values["Industry"] ?? 20,
      Construction: values["Construction"] ?? 20,
      Dust: values["Road Dust"] ?? 20,
      Biomass: values["Biomass"] ?? 10
    };
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px] text-slate-400">
        Loading ward intelligence profiles...
      </div>
    );
  }

  if (error || !wardId) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[400px] text-rose-400 gap-4">
        <p>{error || "Ward not found"}</p>
        <button onClick={() => navigate(-1)} className="text-xs text-slate-400 hover:text-white bg-slate-900 px-4 py-2 border border-slate-800 rounded-xl">Back</button>
      </div>
    );
  }

  const currentAqi = stats.find(s => s.metric === "AQI")?.value || 0;
  const sources = parseSourcePercent(activeRecs[0]?.estimated_source || null);

  return (
    <div className="flex flex-col gap-6 max-w-6xl mx-auto py-4">
      {/* Header Panel */}
      <div className="flex items-center justify-between border-b border-slate-900 pb-4">
        <div className="flex items-center gap-3">
          <button
            onClick={() => navigate(-1)}
            className="flex items-center justify-center w-8 h-8 rounded-xl bg-slate-900 border border-slate-800 text-slate-400 hover:text-white transition-all cursor-pointer"
          >
            <ChevronLeft size={16} />
          </button>
          <div>
            <h1 className="text-2xl font-bold text-white tracking-tight">{getCleanName(wardName)}</h1>
            <p className="text-xs text-slate-400 mt-0.5">Locality Decision-Support System Profile</p>
          </div>
        </div>

        <button
          onClick={handleAnalyze}
          disabled={analyzing}
          className="flex items-center gap-1.5 text-xs font-bold px-4 py-2.5 rounded-xl bg-violet-600 hover:bg-violet-500 text-white transition-all cursor-pointer disabled:opacity-50"
        >
          <Sparkles size={13} className={analyzing ? "animate-pulse" : ""} />
          {analyzing ? "Analyzing..." : "Analyze with Groq AI"}
        </button>
      </div>

      {/* Main Grid: Data & Intelligence */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Left Column: Local Pollutant breakdown */}
        <div className="lg:col-span-2 flex flex-col gap-6">
          
          {/* Chart Card */}
          <div className="bg-slate-900/40 border border-slate-900 rounded-2xl p-6 backdrop-blur-md">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-sm font-bold text-slate-200 uppercase tracking-wider">Current Air Quality Metrics</h2>
              <span className={`px-2.5 py-0.5 rounded-full border text-xs font-semibold ${getAqiColor(currentAqi)}`}>
                AQI: {currentAqi}
              </span>
            </div>
            <ResponsiveContainer width="100%" height={320}>
              <BarChart data={stats.filter(s => s.metric !== "Temp (°C)" && s.metric !== "Humidity (%)" && s.metric !== "AQI")}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                <XAxis dataKey="metric" stroke="#64748b" fontSize={11} />
                <YAxis stroke="#64748b" fontSize={11} />
                <Tooltip contentStyle={{ backgroundColor: "#020617", border: "1px solid #1e293b" }} />
                <Bar dataKey="value" fill="#8b5cf6" radius={[4, 4, 0, 0]} barSize={40} />
              </BarChart>
            </ResponsiveContainer>
          </div>

          {/* Forecasting Panel */}
          {forecast.length > 0 && (
            <div className="bg-slate-900/40 border border-slate-900 rounded-2xl p-6 backdrop-blur-md">
              <h2 className="text-sm font-bold text-slate-200 uppercase tracking-wider mb-4">24-Hour Predictive Forecast</h2>
              <ResponsiveContainer width="100%" height={240}>
                <LineChart data={forecast}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                  <XAxis 
                    dataKey="timestamp" 
                    stroke="#64748b" 
                    fontSize={10} 
                    tickFormatter={(str) => {
                      const date = new Date(str);
                      return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
                    }}
                  />
                  <YAxis stroke="#64748b" fontSize={10} />
                  <Tooltip contentStyle={{ backgroundColor: "#020617", border: "1px solid #1e293b" }} />
                  <Line type="monotone" dataKey="predicted_aqi" stroke="#f43f5e" strokeWidth={2} activeDot={{ r: 6 }} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          )}
        </div>

        {/* Right Column: AI Insights & Administrative Action */}
        <div className="flex flex-col gap-6">

          {/* Source Attribution Panel */}
          <div className="bg-slate-900/40 border border-slate-900 rounded-2xl p-5 flex flex-col gap-4 backdrop-blur-md">
            <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider border-b border-slate-800 pb-2.5">
              Pollution Source Attribution
            </h3>
            
            <div className="flex flex-col gap-3">
              {[
                { label: "Vehicular Traffic", val: sources.Traffic, color: "bg-rose-500" },
                { label: "Industrial Output", val: sources.Industrial, color: "bg-violet-500" },
                { label: "Construction Activity", val: sources.Construction, color: "bg-amber-500" },
                { label: "Road Dust Suspension", val: sources.Dust, color: "bg-slate-500" },
                { label: "Biomass Burning", val: sources.Biomass, color: "bg-emerald-500" }
              ].map((s, idx) => (
                <div key={idx} className="flex flex-col gap-1.5">
                  <div className="flex justify-between items-center text-xs font-semibold">
                    <span className="text-slate-300">{s.label}</span>
                    <span className="text-white font-bold">{s.val}%</span>
                  </div>
                  <div className="w-full bg-slate-950 rounded-full h-2 overflow-hidden border border-slate-800/40">
                    <div className={`${s.color} h-2 rounded-full`} style={{ width: `${s.val}%` }}></div>
                  </div>
                </div>
              ))}
            </div>

            {sourceReasoning && (
              <div className="text-[11px] text-slate-400 bg-slate-950/60 p-3 rounded-xl border border-slate-800/80 leading-relaxed mt-2">
                <span className="font-bold text-violet-400 block mb-1">AI Reasoning Analysis:</span>
                {sourceReasoning}
              </div>
            )}
          </div>

          {/* Action Intervention Card */}
          {activeRecs.length > 0 && (
            <div className="bg-slate-900/40 border border-slate-900 rounded-2xl p-5 flex flex-col gap-4 backdrop-blur-md">
              <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider border-b border-slate-800 pb-2.5">
                AI Administrative Action Plan
              </h3>
              <div>
                <p className="text-xs text-slate-300 font-medium leading-relaxed">
                  {activeRecs[0].recommendation_text}
                </p>
              </div>

              {activeRecs[0].action_plan?.steps && (
                <div className="flex flex-col gap-2.5 bg-slate-950/60 border border-slate-850 p-4.5 rounded-xl">
                  {activeRecs[0].action_plan.steps.map((step, idx) => {
                    const isExecuted = loggedInterventions.some((i) => i.title.includes(step));
                    return (
                      <div key={idx} className="flex items-start gap-2 text-xs border-b border-slate-900 last:border-b-0 pb-2.5 last:pb-0">
                        <span className="text-violet-400 font-bold shrink-0">{idx + 1}.</span>
                        <div className="flex flex-col gap-1.5 w-full">
                          <span className="text-slate-300 leading-normal">{step}</span>
                          {isExecuted ? (
                            <span className="flex items-center gap-1 text-[10px] font-bold text-emerald-400 bg-emerald-500/10 border border-emerald-500/20 px-2 py-0.5 rounded-md w-fit">
                              <CheckCircle2 size={12} /> Implemented
                            </span>
                          ) : (
                            <button
                              onClick={() => handleImplementIntervention(step, "water_sprinkling")}
                              disabled={implementing}
                              className="text-[9px] font-bold text-violet-400 hover:text-white transition-colors mr-auto hover:underline"
                            >
                              Implement Action →
                            </button>
                          )}
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          )}

          {/* Citizen Advisories Card */}
          {advisories.length > 0 && (
            <div className="bg-slate-900/40 border border-slate-900 rounded-2xl p-5 flex flex-col gap-4 backdrop-blur-md">
              <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider border-b border-slate-800 pb-2.5">
                Citizen Advisories Feed
              </h3>
              
              <div className="flex flex-col gap-3">
                {advisories.map((ad) => (
                  <div key={ad.id} className="flex flex-col gap-2.5 p-3.5 rounded-xl bg-slate-950/60 border border-slate-800">
                    <div className="flex items-center justify-between">
                      <h4 className="text-xs font-bold text-white">{ad.title}</h4>
                      <span className={`text-[9px] uppercase tracking-wider font-extrabold px-1.5 py-0.5 rounded border border-rose-500/20 text-rose-400 bg-rose-500/10`}>
                        {ad.risk_level}
                      </span>
                    </div>
                    <p className="text-[11px] text-slate-400 leading-normal">{ad.advisory_text}</p>
                    
                    {ad.status === "draft" ? (
                      <button
                        onClick={() => handlePublishAdvisory(ad.id)}
                        disabled={publishing === ad.id}
                        className="flex items-center gap-1 text-[10px] font-bold text-violet-400 hover:text-white transition-colors cursor-pointer hover:underline"
                      >
                        <Send size={10} />
                        Publish Advisory to Public
                      </button>
                    ) : (
                      <span className="text-[10px] text-emerald-400 font-bold flex items-center gap-1 mt-1">
                        <CheckCircle2 size={11} /> Published to Citizens
                      </span>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

        </div>
      </div>
    </div>
  );
};
