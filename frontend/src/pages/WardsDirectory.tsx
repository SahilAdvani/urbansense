import React, { useEffect, useState, useCallback } from "react";
import { Link } from "react-router-dom";
import { ArrowLeft, Search, SlidersHorizontal, ChevronRight, Wind } from "lucide-react";
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

export const WardsDirectory: React.FC = () => {
  const { activeCity } = useCity();
  const [wards, setWards] = useState<WardWithStat[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");
  const [sortBy, setSortBy] = useState<"aqi-desc" | "aqi-asc" | "name-asc">("aqi-desc");
  const [error, setError] = useState<string | null>(null);

  const getAqiStatus = (aqi: number) => {
    if (aqi <= 50) return { label: "Good", color: "text-emerald-400 bg-emerald-500/10 border-emerald-500/20" };
    if (aqi <= 100) return { label: "Satisfactory", color: "text-teal-400 bg-teal-500/10 border-teal-500/20" };
    if (aqi <= 200) return { label: "Moderate", color: "text-amber-400 bg-amber-500/10 border-amber-500/20" };
    if (aqi <= 300) return { label: "Poor", color: "text-orange-400 bg-orange-500/10 border-orange-500/20" };
    return { label: "Very Poor", color: "text-rose-400 bg-rose-500/10 border-rose-500/20" };
  };

  const fetchWardsData = useCallback(async () => {
    if (!activeCity) return;
    setLoading(true);
    try {
      const response = await api.get<Ward[]>("/wards", {
        params: { city_id: activeCity.id }
      });
      const wardsList = response.data;

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
      setError(null);
    } catch (err) {
      console.error(err);
      setError("Failed to load wards directory.");
    } finally {
      setLoading(false);
    }
  }, [activeCity]);

  useEffect(() => {
    fetchWardsData();
  }, [activeCity, fetchWardsData]);

  // Clean names (remove city prefix)
  const getCleanName = (name: string) => {
    return name.includes(" - ") ? name.split(" - ")[1] : name;
  };

  // Filter and Sort
  const filteredWards = wards.filter(w => 
    getCleanName(w.name).toLowerCase().includes(searchQuery.toLowerCase())
  );

  const sortedWards = [...filteredWards].sort((a, b) => {
    if (sortBy === "aqi-desc") return b.aqi - a.aqi;
    if (sortBy === "aqi-asc") return a.aqi - b.aqi;
    return getCleanName(a.name).localeCompare(getCleanName(b.name));
  });

  return (
    <div className="flex flex-col gap-6 max-w-5xl mx-auto py-4">
      {/* Header & Back Navigation */}
      <div className="flex flex-col gap-3">
        <Link 
          to="/" 
          className="flex items-center gap-2 text-slate-400 hover:text-white text-xs font-semibold tracking-wide transition-colors shrink-0 mr-auto bg-slate-900/60 px-3 py-1.5 rounded-lg border border-slate-800"
        >
          <ArrowLeft className="w-3.5 h-3.5" />
          Back to Command Dashboard
        </Link>
        <div>
          <h1 className="text-2xl font-bold text-white tracking-tight">Wards & Sectors Directory</h1>
          <p className="text-xs text-slate-400 mt-1">
            Complete list of monitoring zones in <span className="text-violet-400 font-semibold">{activeCity?.name}</span> ({wards.length} total)
          </p>
        </div>
      </div>

      {/* Filter and Search Bar Card */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 bg-slate-900/40 border border-slate-900 rounded-2xl p-4 backdrop-blur-md">
        {/* Search */}
        <div className="relative md:col-span-2">
          <Search className="absolute left-3.5 top-3 w-4 h-4 text-slate-500" />
          <input
            type="text"
            placeholder="Search by ward or area name..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full bg-slate-950/80 border border-slate-800 focus:border-violet-600 focus:outline-none rounded-xl pl-11 pr-4 py-2 text-sm text-white placeholder-slate-500 transition-colors"
          />
        </div>

        {/* Sort Dropdown */}
        <div className="relative">
          <SlidersHorizontal className="absolute left-3.5 top-3 w-4 h-4 text-slate-500" />
          <select
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value as any)}
            className="w-full bg-slate-950/80 border border-slate-800 focus:border-violet-600 focus:outline-none rounded-xl pl-11 pr-4 py-2.5 text-xs text-white appearance-none cursor-pointer transition-colors"
          >
            <option value="aqi-desc">Sort by AQI (Highest first)</option>
            <option value="aqi-asc">Sort by AQI (Lowest first)</option>
            <option value="name-asc">Sort by Name (A-Z)</option>
          </select>
        </div>
      </div>

      {/* Wards Directory Table / Grid */}
      {loading ? (
        <div className="flex items-center justify-center min-h-[300px] text-slate-400 font-medium">
          Loading wards directory...
        </div>
      ) : error ? (
        <div className="flex items-center justify-center min-h-[300px] text-rose-400 font-medium">
          {error}
        </div>
      ) : sortedWards.length === 0 ? (
        <div className="flex items-center justify-center min-h-[300px] text-slate-500 font-medium">
          No monitoring zones found matching your search.
        </div>
      ) : (
        <div className="bg-slate-900/40 border border-slate-900 rounded-2xl overflow-hidden backdrop-blur-md">
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="border-b border-slate-900 bg-slate-950/40 text-[10px] uppercase tracking-wider text-slate-500 font-bold">
                  <th className="px-6 py-4">Ward / Sub-Locality Name</th>
                  <th className="px-6 py-4 text-center">AQI Rating</th>
                  <th className="px-6 py-4 text-center">Status</th>
                  <th className="px-6 py-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-900/60">
                {sortedWards.map((ward) => {
                  const status = getAqiStatus(ward.aqi);
                  return (
                    <tr 
                      key={ward.id}
                      className="hover:bg-slate-900/20 transition-colors"
                    >
                      <td className="px-6 py-4.5 font-semibold text-sm text-slate-200">
                        {getCleanName(ward.name)}
                      </td>
                      <td className="px-6 py-4.5 text-center font-bold text-sm text-white">
                        {ward.aqi > 0 ? ward.aqi : "—"}
                      </td>
                      <td className="px-6 py-4.5 text-center">
                        {ward.aqi > 0 ? (
                          <span className={`inline-flex px-2.5 py-1 text-[10px] font-bold rounded-lg border uppercase tracking-wider ${status.color}`}>
                            {status.label}
                          </span>
                        ) : (
                          <span className="text-slate-500 text-xs">—</span>
                        )}
                      </td>
                      <td className="px-6 py-4.5 text-right">
                        <Link
                          to={`/ward/${ward.id}`}
                          className="inline-flex items-center gap-1 text-xs text-violet-400 hover:text-white font-bold transition-colors"
                        >
                          View Analytics
                          <ChevronRight className="w-3.5 h-3.5" />
                        </Link>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
};
