import React, { useEffect, useState } from "react";
import api from "../utils/api";

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

const statusColor: Record<string, string> = {
  pending: "text-amber-400 bg-amber-400/10 border-amber-400/20",
  implemented: "text-emerald-400 bg-emerald-400/10 border-emerald-400/20",
  dismissed: "text-slate-400 bg-slate-400/10 border-slate-400/20",
};

export const AIRecommendations: React.FC = () => {
  const [recs, setRecs] = useState<AIRec[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchRecs = async () => {
      try {
        const response = await api.get<AIRec[]>("/recommendations");
        setRecs(response.data);
      } catch (err) {
        console.error("Failed to fetch AI recommendations", err);
        setError("Could not load AI recommendations from the server.");
      } finally {
        setLoading(false);
      }
    };
    fetchRecs();
  }, []);

  return (
    <div className="min-h-screen bg-slate-950 text-white p-6">
      <h1 className="text-2xl font-bold mb-1">AI Recommendations</h1>
      <p className="text-slate-400 text-sm mb-6">
        AI-generated intervention suggestions based on current AQI data
      </p>

      {loading && <p className="text-slate-400">Loading recommendations…</p>}
      {error && <p className="text-rose-400">{error}</p>}

      {!loading && !error && recs.length === 0 && (
        <p className="text-slate-400">No AI recommendations available yet.</p>
      )}

      {!loading && !error && recs.length > 0 && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {recs.map((rec) => (
            <div
              key={rec.id}
              className="bg-slate-900/60 border border-slate-800 rounded-2xl p-5 flex flex-col gap-4"
            >
              <div className="flex items-start justify-between gap-3">
                <div>
                  <p className="text-xs text-slate-400 uppercase tracking-wider mb-1">
                    Ward {rec.ward_id}
                  </p>
                  <h2 className="text-base font-semibold text-white">
                    Trigger AQI: {rec.trigger_aqi}
                  </h2>
                  <p className="text-xs text-violet-400 mt-0.5">
                    Primary: {rec.primary_pollutant}
                    {rec.estimated_source && ` — ${rec.estimated_source}`}
                  </p>
                </div>
                <span
                  className={`text-xs font-semibold px-2.5 py-1 rounded-full border capitalize shrink-0 ${
                    statusColor[rec.status] ?? statusColor.dismissed
                  }`}
                >
                  {rec.status}
                </span>
              </div>

              <p className="text-slate-300 text-sm leading-relaxed">
                {rec.recommendation_text}
              </p>

              {rec.action_plan?.steps && rec.action_plan.steps.length > 0 && (
                <div className="bg-slate-800/60 rounded-xl p-4">
                  <p className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-2">
                    Action Plan
                  </p>
                  <ul className="space-y-1.5">
                    {rec.action_plan.steps.map((step, i) => (
                      <li
                        key={i}
                        className="flex gap-2 text-xs text-slate-300"
                      >
                        <span className="text-violet-400 shrink-0">
                          {i + 1}.
                        </span>
                        {step}
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {rec.confidence_score != null && (
                <p className="text-xs text-slate-500">
                  Confidence: {(rec.confidence_score * 100).toFixed(0)}%
                </p>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
