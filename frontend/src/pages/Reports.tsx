import React, { useState, useEffect } from "react";
import { FileText, Download, Building2, Wind, ShieldAlert, CheckCircle2, RefreshCw } from "lucide-react";
import api from "../utils/api";
import { useCity } from "../hooks/useCity";

interface Ward {
  id: number;
  name: string;
}

export const Reports: React.FC = () => {
  const { activeCity, cities } = useCity();
  const [selectedCityId, setSelectedCityId] = useState<string>("");
  const [downloading, setDownloading] = useState(false);
  const [wardCount, setWardCount] = useState<number>(0);
  const [cityAvgAqi, setCityAvgAqi] = useState<number | null>(null);
  const [loadingPreview, setLoadingPreview] = useState(false);

  useEffect(() => {
    if (activeCity && !selectedCityId) {
      setSelectedCityId(activeCity.id);
    }
  }, [activeCity, selectedCityId]);

  useEffect(() => {
    const fetchCitySummary = async () => {
      if (!selectedCityId) return;
      setLoadingPreview(true);
      try {
        const wardsRes = await api.get<Ward[]>("/wards", { params: { city_id: selectedCityId } });
        const wardsList = wardsRes.data;
        setWardCount(wardsList.length);

        if (wardsList.length > 0) {
          const statsList = await Promise.all(
            wardsList.map(async (w) => {
              try {
                const s = await api.get<{ metric: string; value: number }[]>(`/wards/${w.id}/stats`);
                const aqiStat = s.data.find((m) => m.metric === "AQI");
                return aqiStat ? aqiStat.value : 0;
              } catch {
                return 0;
              }
            })
          );
          const validAqis = statsList.filter((a) => a > 0);
          if (validAqis.length > 0) {
            setCityAvgAqi(Math.round(validAqis.reduce((sum, v) => sum + v, 0) / validAqis.length));
          } else {
            setCityAvgAqi(null);
          }
        }
      } catch (err) {
        console.error("Failed to load city report summary", err);
      } finally {
        setLoadingPreview(false);
      }
    };

    fetchCitySummary();
  }, [selectedCityId]);

  const handleDownloadPdf = async () => {
    if (!selectedCityId) return;
    setDownloading(true);
    try {
      const response = await api.get(`/reports/pdf/${selectedCityId}`, {
        responseType: "blob",
      });

      // Create download link for PDF blob
      const url = window.URL.createObjectURL(new Blob([response.data], { type: "application/pdf" }));
      const link = document.createElement("a");
      link.href = url;
      link.setAttribute("download", `urbansense_report_${selectedCityId}.pdf`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      console.error("Failed to download PDF report", err);
      alert("Failed to generate PDF report. Please try again.");
    } finally {
      setDownloading(false);
    }
  };

  const getCityObj = cities.find((c) => c.id === selectedCityId) || activeCity;

  return (
    <div className="flex flex-col gap-6 max-w-5xl mx-auto py-4">
      {/* Header Banner */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 flex flex-col md:flex-row items-start md:items-center justify-between gap-4 shadow-xl">
        <div className="flex items-center gap-4">
          <div className="bg-violet-600/20 p-3 rounded-2xl text-violet-400 border border-violet-500/30">
            <FileText size={28} />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-white tracking-tight">Executive Reports Center</h1>
            <p className="text-sm text-slate-400">Generate and export automated PDF intelligence briefs for city administrators.</p>
          </div>
        </div>
      </div>

      {/* Main Selection & Download Card */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* City Selector & Action Panel */}
        <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6 flex flex-col justify-between gap-6 shadow-xl">
          <div>
            <h3 className="text-base font-bold text-white mb-1">Select Target Jurisdiction</h3>
            <p className="text-xs text-slate-400 mb-4">Choose a city to compile executive statistics and active intervention logs into a PDF.</p>

            <label className="text-xs font-semibold text-slate-300 block mb-2">City:</label>
            <select
              value={selectedCityId}
              onChange={(e) => setSelectedCityId(e.target.value)}
              className="w-full bg-slate-950 border border-slate-700 text-slate-100 text-sm rounded-xl p-3 focus:outline-none focus:border-violet-500 font-medium"
            >
              {cities.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.name}
                </option>
              ))}
            </select>
          </div>

          <button
            onClick={handleDownloadPdf}
            disabled={downloading || !selectedCityId}
            className="w-full bg-violet-600 hover:bg-violet-500 disabled:opacity-50 text-white font-semibold py-3 px-4 rounded-xl shadow-lg transition flex items-center justify-center gap-2"
          >
            {downloading ? (
              <>
                <RefreshCw size={18} className="animate-spin" />
                Compiling Report...
              </>
            ) : (
              <>
                <Download size={18} />
                Export PDF Briefing
              </>
            )}
          </button>
        </div>

        {/* Live Preview Summary Sheet */}
        <div className="md:col-span-2 bg-slate-900/80 border border-slate-800 rounded-2xl p-6 shadow-xl flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between border-b border-slate-800 pb-4 mb-4">
              <div>
                <span className="text-xs font-semibold text-violet-400 uppercase tracking-wider">Report Preview</span>
                <h2 className="text-xl font-bold text-white">{getCityObj?.name || "Target City"} Briefing Overview</h2>
              </div>
              <span className="text-xs text-slate-500 bg-slate-950 border border-slate-800 px-3 py-1 rounded-full font-mono">
                {new Date().toLocaleDateString()}
              </span>
            </div>

            {loadingPreview ? (
              <div className="py-12 flex flex-col items-center justify-center gap-2">
                <RefreshCw size={24} className="animate-spin text-violet-500" />
                <span className="text-xs text-slate-400">Loading summary metrics...</span>
              </div>
            ) : (
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div className="bg-slate-950/60 border border-slate-800 p-4 rounded-xl flex items-center gap-3">
                  <div className="bg-slate-800 p-2.5 rounded-lg text-slate-300">
                    <Building2 size={20} />
                  </div>
                  <div>
                    <span className="text-xs text-slate-400 block">Monitored Suburbs</span>
                    <span className="text-lg font-bold text-white">{wardCount} Active Wards</span>
                  </div>
                </div>

                <div className="bg-slate-950/60 border border-slate-800 p-4 rounded-xl flex items-center gap-3">
                  <div className="bg-slate-800 p-2.5 rounded-lg text-amber-400">
                    <Wind size={20} />
                  </div>
                  <div>
                    <span className="text-xs text-slate-400 block">City Average AQI</span>
                    <span className="text-lg font-bold text-white">{cityAvgAqi ?? "N/A"}</span>
                  </div>
                </div>

                <div className="bg-slate-950/60 border border-slate-800 p-4 rounded-xl flex items-center gap-3">
                  <div className="bg-slate-800 p-2.5 rounded-lg text-emerald-400">
                    <CheckCircle2 size={20} />
                  </div>
                  <div>
                    <span className="text-xs text-slate-400 block">Format</span>
                    <span className="text-sm font-semibold text-slate-200">ISO Standard PDF</span>
                  </div>
                </div>

                <div className="bg-slate-950/60 border border-slate-800 p-4 rounded-xl flex items-center gap-3">
                  <div className="bg-slate-800 p-2.5 rounded-lg text-violet-400">
                    <ShieldAlert size={20} />
                  </div>
                  <div>
                    <span className="text-xs text-slate-400 block">Included Sections</span>
                    <span className="text-sm font-semibold text-slate-200">Wards, AI & Actions</span>
                  </div>
                </div>
              </div>
            )}
          </div>

          <p className="text-xs text-slate-500 mt-6 pt-4 border-t border-slate-800/80">
            Reports are dynamically built from real-time OpenWeatherMap telemetry and Groq AI action plans stored in Supabase.
          </p>
        </div>
      </div>
    </div>
  );
};
