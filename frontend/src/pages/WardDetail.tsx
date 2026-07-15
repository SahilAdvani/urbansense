import React, { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import api from "../utils/api";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
} from "recharts";

interface WardStat {
  metric: string;
  value: number;
}

interface WardInfo {
  id: number;
  name: string;
}

export const WardDetail: React.FC = () => {
  const { wardId } = useParams<{ wardId: string }>();
  const navigate = useNavigate();
  const [stats, setStats] = useState<WardStat[]>([]);
  const [wardName, setWardName] = useState<string>("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!wardId) return;

    const fetchWardData = async () => {
      setLoading(true);
      try {
        const [wardRes, statsRes] = await Promise.all([
          api.get<WardInfo>(`/wards/${wardId}`),
          api.get<WardStat[]>(`/wards/${wardId}/stats`),
        ]);
        setWardName(wardRes.data.name);
        setStats(statsRes.data);
      } catch (err) {
        console.error("Failed to load ward data", err);
        setError("Could not load ward details.");
      } finally {
        setLoading(false);
      }
    };

    fetchWardData();
  }, [wardId]);

  return (
    <div className="min-h-screen bg-slate-950 text-white p-6">
      <button
        onClick={() => navigate(-1)}
        className="mb-6 text-slate-400 hover:text-violet-400 text-sm flex items-center gap-1 transition-colors"
      >
        ← Back
      </button>

      {loading && <p className="text-slate-400">Loading ward details…</p>}

      {error && <p className="text-rose-400">{error}</p>}

      {!loading && !error && (
        <>
          <h1 className="text-2xl font-bold mb-1">{wardName}</h1>
          <p className="text-slate-400 mb-6 text-sm">
            Ward ID: {wardId} — Pollutant breakdown over the last 24 hours
          </p>

          {stats.length > 0 ? (
            <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-6">
              <h2 className="text-lg font-semibold mb-4 text-slate-200">
                AQI Metrics
              </h2>
              <ResponsiveContainer width="100%" height={400}>
                <BarChart
                  data={stats}
                  margin={{ top: 20, right: 30, left: 20, bottom: 5 }}
                >
                  <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                  <XAxis dataKey="metric" stroke="#94a3b8" />
                  <YAxis stroke="#94a3b8" />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: "#1e293b",
                      border: "1px solid #334155",
                      borderRadius: "8px",
                      color: "#f8fafc",
                    }}
                  />
                  <Bar dataKey="value" fill="#7c3aed" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          ) : (
            <p className="text-slate-400">No stats available for this ward yet.</p>
          )}
        </>
      )}
    </div>
  );
};
