import React, { useState, useRef, useEffect } from "react";
import { Link, Outlet, useLocation, useNavigate } from "react-router-dom";
import { Wind, Map, BarChart3, ShieldAlert, LogOut, User, Search, Plus, MapPin, Loader2, Activity, FileText } from "lucide-react";
import { useAuth } from "../hooks/useAuth";
import { useCity } from "../hooks/useCity";

export const Layout: React.FC = () => {
  const { user, logout } = useAuth();
  const { activeCity, cities, selectCity, registerCity } = useCity();
  
  const location = useLocation();
  const navigate = useNavigate();

  const [searchQuery, setSearchQuery] = useState("");
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const [registering, setRegistering] = useState(false);
  
  const dropdownRef = useRef<HTMLDivElement>(null);

  const handleLogout = () => {
    logout();
    navigate("/login");
  };

  const navItems = [
    { label: "Dashboard", path: "/", icon: BarChart3 },
    { label: "Map", path: "/map", icon: Map },
    { label: "AI Insights", path: "/recommendations", icon: ShieldAlert },
    { label: "Interventions", path: "/interventions", icon: Activity },
    { label: "Reports", path: "/reports", icon: FileText },
  ];

  // Close dropdown on click outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setDropdownOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const filteredCities = cities.filter(city => 
    city.name.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const handleCitySelect = (cityId: string) => {
    selectCity(cityId);
    setDropdownOpen(false);
    setSearchQuery("");
  };

  const handleRegisterCity = async () => {
    if (!searchQuery.trim()) return;
    setRegistering(true);
    try {
      const newCity = await registerCity(searchQuery);
      handleCitySelect(newCity.id);
    } catch (e) {
      alert("Failed to resolve city coordinates in India. Try another city name.");
    } finally {
      setRegistering(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col antialiased">
      {/* Premium Header */}
      <header className="border-b border-slate-800 bg-slate-900/80 backdrop-blur-md sticky top-0 z-50 px-4 md:px-6 py-3 flex items-center justify-between gap-2">
        {/* Brand & City Dropdown */}
        <div className="flex items-center gap-3 md:gap-4 shrink-0">
          <div className="flex items-center gap-2.5">
            <div className="bg-violet-600 p-1.5 rounded-xl text-white shadow-md shadow-violet-500/30">
              <Wind size={20} />
            </div>
            <div>
              <h1 className="text-lg font-bold tracking-tight text-white leading-none">
                UrbanSense
              </h1>
              <span className="text-[10px] text-violet-400 font-medium">
                AQI Portal
              </span>
            </div>
          </div>

          {/* Interactive City Selector */}
          <div className="relative" ref={dropdownRef}>
            <button
              onClick={() => setDropdownOpen(!dropdownOpen)}
              className="flex items-center gap-1.5 bg-slate-800/80 border border-slate-700 hover:border-violet-500/40 text-slate-200 hover:text-white px-2.5 py-1.5 rounded-xl text-xs font-semibold transition-all cursor-pointer min-w-[120px] justify-between"
            >
              <div className="flex items-center gap-1 text-xs truncate max-w-[90px]">
                <MapPin size={13} className="text-violet-400 shrink-0" />
                <span className="truncate">{activeCity ? activeCity.name : "Select City"}</span>
              </div>
              <span className="text-[9px] text-slate-400 shrink-0">▼</span>
            </button>

            {dropdownOpen && (
              <div className="absolute left-0 mt-2 w-64 bg-slate-900 border border-slate-800 rounded-xl shadow-2xl z-50 p-2 flex flex-col gap-2">
                <div className="relative flex items-center">
                  <Search size={14} className="absolute left-3 text-slate-500" />
                  <input
                    type="text"
                    placeholder="Search or register city..."
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg pl-9 pr-3 py-1.5 text-xs text-slate-100 placeholder:text-slate-600 focus:outline-none focus:border-violet-600"
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === "Enter" && filteredCities.length === 0) {
                        handleRegisterCity();
                      }
                    }}
                  />
                </div>

                <div className="max-h-48 overflow-y-auto space-y-0.5">
                  {filteredCities.map((city) => (
                    <button
                      key={city.id}
                      onClick={() => handleCitySelect(city.id)}
                      className={`w-full text-left px-3 py-2 rounded-lg text-xs font-medium transition-colors flex items-center justify-between cursor-pointer ${
                        activeCity?.id === city.id
                          ? "bg-violet-600/20 text-violet-400 font-semibold"
                          : "text-slate-300 hover:bg-slate-800 hover:text-white"
                      }`}
                    >
                      <span>{city.name}</span>
                      <span className="text-[9px] text-slate-500 font-mono">
                        {city.has_wards ? "Level 2" : "Level 1"}
                      </span>
                    </button>
                  ))}

                  {filteredCities.length === 0 && searchQuery && (
                    <button
                      onClick={handleRegisterCity}
                      disabled={registering}
                      className="w-full flex items-center justify-center gap-1.5 py-2 px-3 rounded-lg text-xs font-semibold bg-violet-600/10 text-violet-400 hover:bg-violet-600/20 transition-all border border-violet-500/20 cursor-pointer"
                    >
                      {registering ? (
                        <Loader2 size={12} className="animate-spin" />
                      ) : (
                        <Plus size={12} />
                      )}
                      {registering ? "Registering..." : `Register "${searchQuery}"`}
                    </button>
                  )}
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Navigation Tabs */}
        <nav className="flex items-center gap-1 md:gap-1.5 overflow-x-auto py-1">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = location.pathname === item.path;
            return (
              <Link
                key={item.path}
                to={item.path}
                className={`flex items-center gap-1.5 text-xs font-medium px-3 py-1.5 rounded-xl transition-all ${
                  isActive
                    ? "bg-violet-600/20 text-violet-300 border border-violet-500/30 shadow-sm"
                    : "text-slate-300 hover:text-white hover:bg-slate-800/60 border border-transparent"
                }`}
              >
                <Icon size={14} />
                <span>{item.label}</span>
              </Link>
            );
          })}
        </nav>

        {/* User profile & Logout */}
        <div className="flex items-center gap-2 shrink-0">
          <div className="hidden sm:flex items-center gap-1.5 bg-slate-900/90 px-2.5 py-1.5 rounded-xl border border-slate-800 text-xs">
            <User size={13} className="text-violet-400 shrink-0" />
            <span className="font-semibold text-slate-300 max-w-[100px] md:max-w-[130px] truncate">
              {user?.email || "Admin User"}
            </span>
          </div>
          <button
            onClick={handleLogout}
            title="Log Out"
            className="flex items-center gap-1.5 bg-rose-500/10 hover:bg-rose-500/20 text-rose-400 border border-rose-500/20 px-2.5 py-1.5 rounded-xl text-xs font-semibold transition-all cursor-pointer shrink-0"
          >
            <LogOut size={14} />
            <span className="hidden md:inline">Logout</span>
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
