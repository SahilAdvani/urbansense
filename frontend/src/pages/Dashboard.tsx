import React, { useEffect, useState, useCallback } from "react";
import { Link } from "react-router-dom";
import { AlertTriangle, ShieldAlert, Thermometer, Wind, RefreshCw, ChevronRight } from "lucide-react";
import api from "../utils/api";
import { useCity } from "../hooks/useCity";

interface Ward {
  id: number;
  name: string;
}

interface WardWithStat extends Ward {
  aqi: number;
  status: string;
}

export const Dashboard = () => {
  const { activeCity, fetchCities } = useCity();
  const [wards, setWards] = useState<WardWithStat[]>([]);
  const [cityAvg, setCityAvg] = useState<number | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const getAqiStatus = (aqi: number) => {
    if (aqi <= 50) return { label: "Good", color: "text-emerald-400 bg-emerald-500/10 border-emerald-500/20" };
    if (aqi <= 100) return { label: "Satisfactory", color: "text-teal-400 bg-teal-500/10 border-teal-500/20" };
    if (aqi <= 200) return { label: "Moderate", color: "text-amber-400 bg-amber-500/10 border-amber-500/20" };
    if (aqi <= 300) return { label: "Poor", color: "text-orange-400 bg-orange-500/10 border-orange-500/20" };
    return { label: "Very Poor", color: "text-rose-400 bg-rose-500/10 border-rose-500/20" };
  };

  const fetchDashboardData = useCallback(async () => {
    if (!activeCity) return;
    try {
      const wardsRes = await api.get<Ward[]>("/wards", {
        params: { city_id: activeCity.id }
      });
      const wardsList = wardsRes.data;

      const wardsWithStats = await Promise.all(
        wardsList.map(async (w) => {
          try {
            const statsRes = await api.get<{ metric: string; value: number }[]>(`/wards/${w.id}/stats`);
            const aqiStat = statsRes.data.find((s) => s.metric === "AQI");
            const aqiValue = aqiStat ? aqiStat.value : 0;
            return {
              ...w,
              aqi: aqiValue,
              status: getAqiStatus(aqiValue).label,
            };
          } catch {
            return { ...w, aqi: 0, status: "Unknown" };
          }
        })
      );

      setWards(wardsWithStats);

      const validAqis = wardsWithStats.filter((w) => w.aqi > 0).map((w) => w.aqi);
      if (validAqis.length > 0) {
        const avg = Math.round(validAqis.reduce((sum, val) => sum + val, 0) / validAqis.length);
        setCityAvg(avg);
      } else {
        setCityAvg(null);
      }
      setError(null);
    } catch (err) {
      console.error(err);
      setError("Failed to load dashboard data.");
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [activeCity]);

  // Short poll city status while is_syncing is true (asynchronous background loader)
  useEffect(() => {
    if (!activeCity || !activeCity.is_syncing) return;

    const interval = setInterval(async () => {
      try {
        await fetchCities(activeCity.id);
        await fetchDashboardData();
      } catch (err) {
        console.error("Polling sync status failed:", err);
      }
    }, 3000);

    return () => clearInterval(interval);
  }, [activeCity?.is_syncing, activeCity?.id, fetchCities, fetchDashboardData]);

  const [prevCityId, setPrevCityId] = useState<string | null>(null);

  useEffect(() => {
    if (activeCity) {
      if (activeCity.id !== prevCityId) {
        setLoading(true);
        setPrevCityId(activeCity.id);
      }
    }
    fetchDashboardData();
  }, [activeCity, fetchDashboardData, prevCityId]);


  const handleRefresh = async () => {
    if (!activeCity) return;
    setRefreshing(true);
    try {
      await api.post(`/cities/${activeCity.id}/sync`);
      // Update local city state immediately to show progress
      await fetchCities(activeCity.id);
    } catch (err: any) {
      console.error("Sync failed:", err);
      alert(err?.response?.data?.detail ?? "Failed to sync live sensor metrics from OpenWeatherMap.");
    } finally {
      setRefreshing(false);
    }
  };


  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px] text-slate-400">
        Loading Command Dashboard…
      </div>
    );
  }

  const cityAvgStatus = cityAvg ? getAqiStatus(cityAvg) : null;
  const hotspotWards = wards.filter((w) => w.aqi > 200);

  return (
    <div className="flex flex-col gap-6">
      {/* Dashboard Toolbar */}
      <div className="flex items-center justify-between border-b border-slate-900 pb-4">
        <div>
          <h2 className="text-2xl font-bold tracking-tight text-white">City Dashboard</h2>
          <p className="text-slate-400 text-xs mt-0.5">Real-time command center summary</p>
        </div>
        <button
          onClick={handleRefresh}
          disabled={refreshing}
          className="flex items-center gap-1.5 text-xs font-semibold px-3.5 py-2 rounded-xl bg-slate-900 border border-slate-800 text-slate-300 hover:text-white transition-all cursor-pointer disabled:opacity-50"
        >
          <RefreshCw size={12} className={refreshing ? "animate-spin" : ""} />
          {refreshing ? "Refreshing…" : "Sync Sensors"}
        </button>
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-400 text-sm">
          {error}
        </div>
      )}

      {activeCity?.is_syncing && (
        <div className="flex items-center gap-3 p-4 rounded-xl bg-violet-500/10 border border-violet-500/20 text-violet-400 text-xs font-semibold">
          <span className="relative flex h-2.5 w-2.5">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-violet-400 opacity-75"></span>
            <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-violet-500"></span>
          </span>
          Synchronizing local sensors... Real-time suburb coordinates are updating asynchronously.
        </div>
      )}

      {/* Metric Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* City Average AQI Card */}
        <div className="bg-slate-900/40 border border-slate-800/80 rounded-2xl p-5 flex flex-col gap-3 relative overflow-hidden backdrop-blur-md">
          <div className="absolute top-0 right-0 w-24 h-24 bg-violet-600/10 rounded-full blur-xl"></div>
          <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
            City-Wide Average AQI
          </span>
          <div className="flex items-baseline gap-2 mt-1">
            <span className="text-5xl font-black tracking-tight text-violet-400">
              {cityAvg ?? "N/A"}
            </span>
            {cityAvgStatus && (
              <span
                className={`text-xs font-semibold px-2.5 py-0.5 rounded-full border ${cityAvgStatus.color}`}
              >
                {cityAvgStatus.label}
              </span>
            )}
          </div>
          <p className="text-xs text-slate-500 mt-2">
            Calculated across {wards.length} active municipal wards
          </p>
        </div>

        {/* Active Sensors */}
        <div className="bg-slate-900/40 border border-slate-800/80 rounded-2xl p-5 flex flex-col gap-3 relative overflow-hidden backdrop-blur-md">
          <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
            System Sensors
          </span>
          <div className="flex items-baseline gap-2 mt-1">
            <span className="text-5xl font-black tracking-tight text-emerald-400">
              {wards.length}
            </span>
            <span className="text-xs font-semibold px-2.5 py-0.5 rounded-full border text-emerald-400 bg-emerald-500/10 border-emerald-500/20">
              Online
            </span>
          </div>
          <p className="text-xs text-slate-500 mt-2">All stations reporting normal diagnostic signals</p>
        </div>

        {/* AI Recommendations Alert Card */}
        <div className="bg-slate-900/40 border border-slate-800/80 rounded-2xl p-5 flex flex-col gap-3 relative overflow-hidden backdrop-blur-md">
          <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
            AI Advisory Alerts
          </span>
          <div className="flex items-baseline gap-2 mt-1">
            <span className="text-5xl font-black tracking-tight text-amber-400">
              {hotspotWards.length}
            </span>
            {hotspotWards.length > 0 ? (
              <span className="text-xs font-semibold px-2.5 py-0.5 rounded-full border text-amber-400 bg-amber-500/10 border-amber-500/20">
                Action Required
              </span>
            ) : (
              <span className="text-xs font-semibold px-2.5 py-0.5 rounded-full border text-emerald-400 bg-emerald-500/10 border-emerald-500/20">
                Clear
              </span>
            )}
          </div>
          <p className="text-xs text-slate-500 mt-2">
            {hotspotWards.length > 0
              ? `${hotspotWards.length} wards reporting critical pollution levels`
              : "No warnings issued"}
          </p>
        </div>
      </div>

      {/* Main Grid: Wards & Active Alerts */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Ward List */}
        <div className="lg:col-span-2 bg-slate-900/40 border border-slate-800/80 rounded-2xl p-6 flex flex-col gap-4 backdrop-blur-md">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            <h3 className="text-sm font-bold text-white uppercase tracking-wider">
              Municipal Wards
            </h3>
            <span className="text-xs text-slate-500">{wards.length} Wards Loaded</span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {[...wards]
              .sort((a, b) => b.aqi - a.aqi)
              .slice(0, 6)
              .map((ward) => {
                const currentStatus = getAqiStatus(ward.aqi);
                return (
                  <Link
                    key={ward.id}
                    to={`/ward/${ward.id}`}
                    className="flex items-center justify-between p-4 rounded-xl bg-slate-950/60 border border-slate-800/80 hover:border-violet-500/40 hover:bg-slate-900/40 transition-all group"
                  >
                    <div className="flex flex-col gap-1">
                      <span className="text-sm font-semibold text-slate-200 group-hover:text-violet-400 transition-colors">
                        {ward.name.split(" - ")[1] || ward.name}
                      </span>
                      <span className="text-[10px] text-slate-500 font-medium">
                        {ward.name.split(" - ")[0]}
                      </span>
                    </div>
                    <div className="flex items-center gap-3">
                      <div className="flex flex-col items-end">
                        <span className="text-base font-bold text-slate-200">{ward.aqi} AQI</span>
                        <span className={`text-[10px] px-2 py-0.5 rounded-full border mt-1 ${currentStatus.color}`}>
                          {currentStatus.label}
                        </span>
                      </div>
                      <ChevronRight size={16} className="text-slate-600 group-hover:text-violet-400 transition-colors" />
                    </div>
                  </Link>
                );
              })}
          </div>

          <div className="flex justify-center border-t border-slate-800/60 pt-4 mt-2">
            <Link
              to="/wards-directory"
              className="inline-flex items-center gap-1.5 text-xs text-violet-400 hover:text-white font-bold tracking-wide transition-colors"
            >
              View All {wards.length} Wards & Sectors
              <ChevronRight size={14} />
            </Link>
          </div>
        </div>

        {/* Hotspots / Active Advisories Column */}
        <div className="bg-slate-900/40 border border-slate-800/80 rounded-2xl p-6 flex flex-col gap-4 backdrop-blur-md">
          <h3 className="text-sm font-bold text-white uppercase tracking-wider border-b border-slate-800 pb-3">
            Active Alerts
          </h3>

          {hotspotWards.length > 0 ? (
            <div className="flex flex-col gap-4">
              {hotspotWards.map((w) => (
                <div
                  key={w.id}
                  className="flex gap-3 items-start bg-rose-500/10 border border-rose-500/20 p-4 rounded-xl"
                >
                  <AlertTriangle className="text-rose-500 shrink-0 mt-0.5" size={18} />
                  <div>
                    <h4 className="text-xs font-bold text-rose-400">
                      Hotspot Detected: {w.name.split(" - ")[1]}
                    </h4>
                    <p className="text-[11px] text-slate-400 mt-1">
                      AQI reached {w.aqi} ({getAqiStatus(w.aqi).label}). Action and localized advisories suggested.
                    </p>
                    <Link
                      to="/recommendations"
                      className="inline-flex items-center gap-1 text-[10px] font-semibold text-rose-400 hover:underline mt-2.5"
                    >
                      <ShieldAlert size={10} /> View AI Interventions
                    </Link>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="flex flex-col items-center justify-center p-8 text-center text-slate-500 gap-2 flex-grow">
              <Thermometer size={24} className="text-slate-700" />
              <span className="text-xs">No active pollution hotspots or emergency level warnings detected.</span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
