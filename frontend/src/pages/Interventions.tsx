import React, { useEffect, useState, useCallback } from "react";
import { ShieldAlert, Activity, CheckCircle2, Clock, Filter, Wind, RefreshCw } from "lucide-react";
import api from "../utils/api";
import { useCity } from "../hooks/useCity";

interface Intervention {
  id: number;
  ward_id: number;
  ward_name?: string;
  city_id?: string;
  title: string;
  description?: string;
  type: string;
  status: string;
  start_time: string;
  end_time?: string;
}

export const Interventions: React.FC = () => {
  const { activeCity, cities } = useCity();
  const [interventions, setInterventions] = useState<Intervention[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedCityId, setSelectedCityId] = useState<string>("");
  const [statusFilter, setStatusFilter] = useState<string>("all");

  const fetchInterventions = useCallback(async () => {
    setLoading(true);
    try {
      const params: Record<string, string> = {};
      if (selectedCityId) params.city_id = selectedCityId;
      if (statusFilter !== "all") params.status = statusFilter;

      const res = await api.get<Intervention[]>("/recommendations/interventions", { params });
      setInterventions(res.data);
    } catch (err) {
      console.error("Failed to load interventions", err);
    } finally {
      setLoading(false);
    }
  }, [selectedCityId, statusFilter]);

  useEffect(() => {
    if (activeCity && !selectedCityId) {
      setSelectedCityId(activeCity.id);
    }
  }, [activeCity, selectedCityId]);

  useEffect(() => {
    fetchInterventions();
  }, [fetchInterventions]);

  const getTypeBadge = (type: string) => {
    switch (type) {
      case "water_sprinkling":
        return { label: "Water Sprinkling", color: "bg-cyan-500/10 text-cyan-400 border-cyan-500/20" };
      case "construction_halt":
        return { label: "Construction Halt", color: "bg-amber-500/10 text-amber-400 border-amber-500/20" };
      case "traffic_diversion":
        return { label: "Traffic Diversion", color: "bg-violet-500/10 text-violet-400 border-violet-500/20" };
      case "smog_tower_active":
        return { label: "Smog Tower Active", color: "bg-emerald-500/10 text-emerald-400 border-emerald-500/20" };
      default:
        return { label: type.replace(/_/g, " "), color: "bg-slate-800 text-slate-300 border-slate-700" };
    }
  };

  return (
    <div className="flex flex-col gap-6 max-w-6xl mx-auto py-4">
      {/* Header Banner */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 flex flex-col md:flex-row items-start md:items-center justify-between gap-4 shadow-xl">
        <div className="flex items-center gap-4">
          <div className="bg-violet-600/20 p-3 rounded-2xl text-violet-400 border border-violet-500/30">
            <ShieldAlert size={28} />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-white tracking-tight">Municipal Intervention Logs</h1>
            <p className="text-sm text-slate-400">Audit trail of executive environmental actions implemented across urban wards.</p>
          </div>
        </div>
        <button
          onClick={fetchInterventions}
          className="flex items-center gap-2 bg-slate-800 hover:bg-slate-700 text-slate-200 text-sm font-medium px-4 py-2 rounded-xl transition border border-slate-700"
        >
          <RefreshCw size={16} className={loading ? "animate-spin" : ""} />
          Refresh Audit Trail
        </button>
      </div>

      {/* Filter Controls */}
      <div className="flex flex-col sm:flex-row items-center justify-between gap-4 bg-slate-900/60 border border-slate-800 rounded-xl p-4 backdrop-blur-md">
        <div className="flex items-center gap-3 w-full sm:w-auto">
          <Filter size={16} className="text-slate-400" />
          <span className="text-sm font-medium text-slate-300">Filter By City:</span>
          <select
            value={selectedCityId}
            onChange={(e) => setSelectedCityId(e.target.value)}
            className="bg-slate-800 border border-slate-700 text-slate-200 text-sm rounded-lg px-3 py-1.5 focus:outline-none focus:border-violet-500"
          >
            <option value="">All Cities</option>
            {cities.map((c) => (
              <option key={c.id} value={c.id}>
                {c.name}
              </option>
            ))}
          </select>
        </div>

        <div className="flex items-center gap-3 w-full sm:w-auto justify-end">
          <span className="text-sm font-medium text-slate-300">Status:</span>
          <div className="flex bg-slate-800 p-1 rounded-lg border border-slate-700 text-xs">
            {["all", "active", "completed"].map((st) => (
              <button
                key={st}
                onClick={() => setStatusFilter(st)}
                className={`px-3 py-1 rounded-md capitalize font-medium transition ${
                  statusFilter === st ? "bg-violet-600 text-white shadow" : "text-slate-400 hover:text-slate-200"
                }`}
              >
                {st}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Interventions Audit Table / List */}
      {loading ? (
        <div className="flex flex-col items-center justify-center py-16 gap-3">
          <div className="animate-spin rounded-full h-10 w-10 border-t-2 border-b-2 border-violet-500"></div>
          <span className="text-sm text-slate-400 font-medium">Retrieving intervention audit logs...</span>
        </div>
      ) : interventions.length === 0 ? (
        <div className="bg-slate-900/40 border border-slate-800/80 rounded-2xl p-12 text-center flex flex-col items-center gap-3">
          <Wind size={40} className="text-slate-600" />
          <h3 className="text-base font-semibold text-slate-300">No Interventions Recorded</h3>
          <p className="text-xs text-slate-500 max-w-md">
            No administrative actions have been logged for this city yet. Execute recommendations directly from the Ward Details panel.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-4">
          {interventions.map((item) => {
            const badge = getTypeBadge(item.type);
            return (
              <div
                key={item.id}
                className="bg-slate-900/80 border border-slate-800 rounded-2xl p-5 hover:border-slate-700 transition shadow-lg flex flex-col md:flex-row items-start md:items-center justify-between gap-4"
              >
                <div className="flex items-start gap-4">
                  <div className="bg-slate-800 p-3 rounded-xl text-violet-400 border border-slate-700/60 mt-1 md:mt-0">
                    <Activity size={20} />
                  </div>
                  <div>
                    <div className="flex items-center gap-3 flex-wrap">
                      <h3 className="text-base font-bold text-white tracking-tight">{item.title}</h3>
                      <span className={`text-xs font-semibold px-2.5 py-0.5 rounded-full border ${badge.color}`}>
                        {badge.label}
                      </span>
                    </div>
                    <p className="text-xs text-slate-400 mt-1">
                      Target Location: <span className="text-slate-200 font-medium">{item.ward_name || `Ward #${item.ward_id}`}</span> ({item.city_id?.toUpperCase() || "CITY"})
                    </p>
                    {item.description && <p className="text-xs text-slate-500 mt-2 bg-slate-950/40 p-2 rounded-lg border border-slate-800/60">{item.description}</p>}
                  </div>
                </div>

                <div className="flex flex-row md:flex-col items-center md:items-end justify-between w-full md:w-auto border-t md:border-t-0 border-slate-800/80 pt-3 md:pt-0 gap-2">
                  <span className="flex items-center gap-1.5 text-xs text-emerald-400 bg-emerald-500/10 border border-emerald-500/20 px-2.5 py-1 rounded-full font-medium">
                    <CheckCircle2 size={12} /> {item.status.toUpperCase()}
                  </span>
                  <span className="flex items-center gap-1 text-xs text-slate-400 font-mono">
                    <Clock size={12} /> {new Date(item.start_time).toLocaleString()}
                  </span>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};
