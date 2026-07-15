import React, { createContext, useContext, useState, useEffect, useCallback } from "react";
import api from "../utils/api";

interface User {
  id: string;
  email: string;
  role: string;
}

interface AuthContextType {
  user: User | null;
  loading: boolean;
  error: string | null;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [initializing, setInitializing] = useState<boolean>(true);

  const logout = useCallback(() => {
    localStorage.removeItem("token");
    setUser(null);
  }, []);

  const fetchMe = useCallback(async () => {
    try {
      const resp = await api.get("/auth/me");
      setUser(resp.data);
    } catch (e) {
      console.error("Failed to validate token:", e);
      logout();
    } finally {
      setInitializing(false);
    }
  }, [logout]);

  const login = async (email: string, password: string) => {
    setLoading(true);
    setError(null);
    try {
      const resp = await api.post("/auth/login", { email, password });
      const token = resp.data.access_token;
      localStorage.setItem("token", token);
      
      // Fetch user profile immediately with the new token
      const me = await api.get("/auth/me");
      setUser(me.data);
    } catch (e: any) {
      setError(e?.response?.data?.detail ?? "Login failed");
      throw e;
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (localStorage.getItem("token")) {
      fetchMe();
    } else {
      setInitializing(false);
    }
  }, [fetchMe]);

  return (
    <AuthContext.Provider value={{ user, loading: loading || initializing, error, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
};
