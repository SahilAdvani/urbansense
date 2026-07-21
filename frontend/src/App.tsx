import React from 'react'
import { 
  Activity, 
  Map as MapIcon, 
  AlertTriangle, 
  BarChart3, 
  Wind, 
  TrendingUp, 
  FileSpreadsheet, 
  ShieldAlert, 
  User 
} from 'lucide-react'

function App() {
  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col antialiased">
      {/* Header */}
      <header className="border-b border-slate-800 bg-slate-900/60 backdrop-blur-md sticky top-0 z-50 px-6 py-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="bg-violet-600 p-2 rounded-xl text-white shadow-lg shadow-violet-500/30 animate-pulse">
            <Wind size={24} />
          </div>
          <div>
            <h1 className="text-xl font-bold tracking-tight text-white m-0 leading-none">UrbanSense</h1>
            <span className="text-xs text-violet-400 font-medium">Smart City AQI Intelligence</span>
          </div>
        </div>

        <nav className="flex items-center gap-6">
          <a href="/" className="text-sm font-medium text-slate-300 hover:text-violet-400 transition-colors">Dashboard</a>
          <a href="/map" className="text-sm font-medium text-slate-300 hover:text-violet-400 transition-colors">Geospatial Map</a>
          <a href="/interventions" className="text-sm font-medium text-slate-300 hover:text-violet-400 transition-colors">Interventions</a>
          <a href="/reports" className="text-sm font-medium text-slate-300 hover:text-violet-400 transition-colors">Reports</a>
        </nav>

        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2 bg-slate-800/80 px-3 py-1.5 rounded-lg border border-slate-700/50">
            <User size={16} className="text-violet-400" />
            <span className="text-xs font-semibold text-slate-300">Admin Session</span>
          </div>
        </div>
      </header>

      {/* Main Content Area */}
      <main className="flex-grow p-6 max-w-7xl mx-auto w-full grid grid-cols-1 lg:grid-cols-4 gap-6">
        
        {/* Left Column: Wards & High-Level Metrics */}
        <div className="lg:col-span-1 flex flex-col gap-6">
          {/* Main Stat Card */}
          <div className="bg-slate-900/40 border border-slate-800/80 rounded-2xl p-5 flex flex-col gap-3 relative overflow-hidden backdrop-blur-md">
            <div className="absolute top-0 right-0 w-24 h-24 bg-violet-600/10 rounded-full blur-xl"></div>
            <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">City-Wide Average AQI</span>
            <div className="flex items-baseline gap-2">
              <span className="text-5xl font-black tracking-tight text-violet-400">142</span>
              <span className="text-sm font-medium text-amber-500 bg-amber-500/10 px-2 py-0.5 rounded-full border border-amber-500/20">Moderate</span>
            </div>
            <p className="text-xs text-slate-400">Calculated across 8 active municipal wards</p>
          </div>

          {/* Quick Actions / Status */}
          <div className="bg-slate-900/40 border border-slate-800/80 rounded-2xl p-5 flex flex-col gap-4 backdrop-blur-md">
            <h3 className="text-sm font-bold text-white uppercase tracking-wider border-b border-slate-800 pb-2">Active Alerts</h3>
            <div className="flex gap-3 items-start bg-rose-500/10 border border-rose-500/20 p-3 rounded-xl">
              <AlertTriangle className="text-rose-500 shrink-0 mt-0.5" size={18} />
              <div>
                <h4 className="text-xs font-bold text-rose-400">Hotspot Detected: Ward 3</h4>
                <p className="text-[11px] text-slate-400 mt-1">AQI reached 284 (Unhealthy). Construction dust suspected.</p>
              </div>
            </div>
          </div>
        </div>

        {/* Center/Right Columns: Map / Interactive View Placeholder */}
        <div className="lg:col-span-3 flex flex-col gap-6">
          <div className="bg-slate-900/40 border border-slate-800/80 rounded-2xl p-6 flex flex-col gap-4 min-h-[400px] relative overflow-hidden backdrop-blur-md justify-between">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-lg font-bold text-white">Geospatial Intelligence Map</h2>
                <p className="text-xs text-slate-400">Ward-level pollution heatmaps and monitoring stations</p>
              </div>
              <div className="flex gap-2">
                <button className="bg-violet-600 hover:bg-violet-700 transition-colors text-white text-xs font-semibold px-3 py-1.5 rounded-lg flex items-center gap-1.5">
                  <MapIcon size={14} /> Toggle Layer
                </button>
              </div>
            </div>

            {/* Map Placeholder Graphic */}
            <div className="flex-grow bg-slate-950/80 rounded-xl border border-slate-800/80 flex items-center justify-center p-6 relative overflow-hidden">
              {/* Simulated Map Background */}
              <div className="absolute inset-0 opacity-10 bg-[radial-gradient(#38bdf8_1px,transparent_1px)] [background-size:16px_16px]"></div>
              <div className="text-center z-10 flex flex-col items-center gap-3">
                <div className="w-12 h-12 bg-slate-900 rounded-full border border-slate-700 flex items-center justify-center text-slate-400">
                  <MapIcon size={24} />
                </div>
                <span className="text-xs text-slate-400 max-w-sm">
                  Interactive React Leaflet map layer initializing. Connect database and complete setup to populate ward boundary GeoJSONs.
                </span>
              </div>
            </div>

            {/* Bottom mini stats bar */}
            <div className="grid grid-cols-3 gap-4 border-t border-slate-800/80 pt-4">
              <div className="flex flex-col gap-1">
                <span className="text-[10px] uppercase font-bold text-slate-500">Active Sensors</span>
                <span className="text-sm font-semibold text-white">12 / 12 Online</span>
              </div>
              <div className="flex flex-col gap-1">
                <span className="text-[10px] uppercase font-bold text-slate-500">Last Synced</span>
                <span className="text-sm font-semibold text-white">Just Now</span>
              </div>
              <div className="flex flex-col gap-1">
                <span className="text-[10px] uppercase font-bold text-slate-500">AI Recommendations</span>
                <span className="text-sm font-semibold text-emerald-400">3 Pending Review</span>
              </div>
            </div>
          </div>
        </div>

      </main>

      {/* Footer */}
      <footer className="border-t border-slate-800 bg-slate-900/20 py-4 px-6 text-center">
        <p className="text-xs text-slate-500">UrbanSense Decision Support System. Developed for Smart City Command Centers.</p>
      </footer>
    </div>
  )
}

export default App
