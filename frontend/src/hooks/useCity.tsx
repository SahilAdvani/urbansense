import React, { createContext, useContext, useState, useEffect, useCallback } from "react";
import api from "../utils/api";

export interface City {
  id: string;
  name: string;
  latitude: number;
  longitude: number;
  has_wards: boolean;
}

interface CityContextType {
  activeCity: City | null;
  cities: City[];
  loading: boolean;
  error: string | null;
  selectCity: (cityId: string) => void;
  registerCity: (cityName: string) => Promise<City>;
}

const CityContext = createContext<CityContextType | undefined>(undefined);

export const CityProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [cities, setCities] = useState<City[]>([]);
  const [activeCity, setActiveCity] = useState<City | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const fetchCities = useCallback(async (selectId?: string) => {
    try {
      const resp = await api.get<City[]>("/cities");
      setCities(resp.data);
      if (resp.data.length > 0) {
        // Set active city: either the preferred one, or first from list
        const target = selectId 
          ? resp.data.find(c => c.id === selectId) 
          : resp.data.find(c => c.id === "delhi") || resp.data[0];
        setActiveCity(target || resp.data[0]);
      }
      setError(null);
    } catch (e) {
      console.error("Failed to load cities:", e);
      setError("Failed to load cities.");
    } finally {
      setLoading(false);
    }
  }, []);

  const selectCity = (cityId: string) => {
    const selected = cities.find((c) => c.id === cityId);
    if (selected) {
      setActiveCity(selected);
    }
  };

  const registerCity = async (cityName: string): Promise<City> => {
    setLoading(true);
    try {
      const resp = await api.post<City>(`/cities/register?name=${encodeURIComponent(cityName)}`);
      const newCity = resp.data;
      
      // Reload cities list and select the newly registered city
      await fetchCities(newCity.id);
      return newCity;
    } catch (e: any) {
      console.error("Failed to register city:", e);
      setError(e?.response?.data?.detail ?? "Failed to register city.");
      throw e;
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCities();
  }, [fetchCities]);

  return (
    <CityContext.Provider
      value={{
        activeCity,
        cities,
        loading,
        error,
        selectCity,
        registerCity,
      }}
    >
      {children}
    </CityContext.Provider>
  );
};

export const useCity = () => {
  const context = useContext(CityContext);
  if (context === undefined) {
    throw new Error("useCity must be used within a CityProvider");
  }
  return context;
};
