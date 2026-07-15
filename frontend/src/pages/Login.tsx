import React, { useState } from "react";
import { useAuth } from "../hooks/useAuth";
import { useNavigate } from "react-router-dom";
import { Wind, Lock, Mail, Loader2 } from "lucide-react";

export const Login = () => {
  const { login, loading, error } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await login(email, password);
      navigate("/", { replace: true });
    } catch {
      // Error is already set in context state and displayed in UI
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-slate-950 p-4 relative overflow-hidden">
      {/* Decorative Blur Backgrounds */}
      <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-violet-600/10 rounded-full blur-3xl"></div>
      <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-fuchsia-600/10 rounded-full blur-3xl"></div>

      <div className="w-full max-w-md bg-slate-900/40 border border-slate-800/80 backdrop-blur-xl p-8 rounded-2xl shadow-2xl z-10">
        <div className="flex flex-col items-center gap-3 mb-8 text-center">
          <div className="bg-violet-600 p-3 rounded-2xl text-white shadow-xl shadow-violet-500/20">
            <Wind size={32} />
          </div>
          <div>
            <h1 className="text-2xl font-bold tracking-tight text-white">UrbanSense</h1>
            <p className="text-xs text-slate-400 mt-1">Smart City Command & Control Portal</p>
          </div>
        </div>

        {error && (
          <div className="mb-6 p-4 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-400 text-xs font-semibold">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="flex flex-col gap-5">
          <div className="flex flex-col gap-1.5">
            <label className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
              Email Address
            </label>
            <div className="relative">
              <span className="absolute inset-y-0 left-0 flex items-center pl-3.5 text-slate-500">
                <Mail size={16} />
              </span>
              <input
                type="email"
                required
                placeholder="name@city.gov"
                className="w-full rounded-xl bg-slate-950/60 border border-slate-800 text-slate-100 pl-10 pr-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-violet-600 transition-all placeholder:text-slate-600"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
              />
            </div>
          </div>

          <div className="flex flex-col gap-1.5">
            <label className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
              Security Password
            </label>
            <div className="relative">
              <span className="absolute inset-y-0 left-0 flex items-center pl-3.5 text-slate-500">
                <Lock size={16} />
              </span>
              <input
                type="password"
                required
                placeholder="••••••••"
                className="w-full rounded-xl bg-slate-950/60 border border-slate-800 text-slate-100 pl-10 pr-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-violet-600 transition-all placeholder:text-slate-600"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-violet-600 hover:bg-violet-700 disabled:opacity-50 transition-all text-white font-semibold py-3 rounded-xl flex items-center justify-center gap-2 shadow-lg shadow-violet-500/20 cursor-pointer mt-2"
          >
            {loading ? (
              <>
                <Loader2 size={16} className="animate-spin" />
                Signing in…
              </>
            ) : (
              "Access System"
            )}
          </button>
        </form>
      </div>
    </div>
  );
};

export default Login;
