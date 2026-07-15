import React from "react";
import { Link, Outlet, useLocation, useNavigate } from "react-router-dom";
import { Wind, Map, BarChart3, ShieldAlert, LogOut, User } from "lucide-react";
import { useAuth } from "../hooks/useAuth";

export const Layout: React.FC = () => {
  const { user, logout } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate("/login");
  };

  const navItems = [
    { label: "Dashboard", path: "/", icon: BarChart3 },
    { label: "Geospatial Map", path: "/map", icon: Map },
    { label: "AI Recommendations", path: "/recommendations", icon: ShieldAlert },
  ];

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col antialiased">
      {/* Premium Header */}
      <header className="border-b border-slate-800 bg-slate-900/60 backdrop-blur-md sticky top-0 z-50 px-6 py-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="bg-violet-600 p-2 rounded-xl text-white shadow-lg shadow-violet-500/30">
            <Wind size={24} />
          </div>
          <div>
            <h1 className="text-xl font-bold tracking-tight text-white leading-none">
              UrbanSense
            </h1>
            <span className="text-xs text-violet-400 font-medium">
              Smart City AQI Intelligence
            </span>
          </div>
        </div>

        {/* Navigation Tabs */}
        <nav className="flex items-center gap-2">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = location.pathname === item.path;
            return (
              <Link
                key={item.path}
                to={item.path}
                className={`flex items-center gap-2 text-sm font-medium px-4 py-2 rounded-xl transition-all ${
                  isActive
                    ? "bg-violet-600/10 text-violet-400 border border-violet-500/20"
                    : "text-slate-300 hover:text-white hover:bg-slate-800/50 border border-transparent"
                }`}
              >
                <Icon size={16} />
                {item.label}
              </Link>
            );
          })}
        </nav>

        {/* User profile & Logout */}
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2 bg-slate-900/80 px-3.5 py-1.5 rounded-xl border border-slate-800">
            <User size={14} className="text-violet-400" />
            <span className="text-xs font-semibold text-slate-300">
              {user?.email || "Admin User"}
            </span>
            <span className="text-[10px] bg-violet-600/20 text-violet-400 px-1.5 py-0.5 rounded font-mono uppercase">
              {user?.role || "Admin"}
            </span>
          </div>
          <button
            onClick={handleLogout}
            title="Log Out"
            className="p-2 rounded-xl text-slate-400 hover:text-rose-400 hover:bg-rose-500/10 border border-transparent hover:border-rose-500/20 transition-all cursor-pointer"
          >
            <LogOut size={16} />
          </button>
        </div>
      </header>

      {/* Main Content Viewport */}
      <main className="flex-grow max-w-7xl mx-auto w-full p-6">
        <Outlet />
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-900 bg-slate-950/20 py-4 px-6 text-center">
        <p className="text-xs text-slate-500">
          UrbanSense Decision Support System &copy; {new Date().getFullYear()}. Developed for Smart City Command Centers.
        </p>
      </footer>
    </div>
  );
};

export default Layout;
