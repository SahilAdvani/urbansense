import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import { AuthProvider } from "./hooks/useAuth";
import { CityProvider } from "./hooks/useCity";
import { ProtectedRoute } from "./components/ProtectedRoute";
import { Layout } from "./components/Layout";
import { Login } from "./pages/Login";
import { Dashboard } from "./pages/Dashboard";
import { MapView } from "./pages/MapView";
import { WardDetail } from "./pages/WardDetail";
import { AIRecommendations } from "./pages/AIRecommendations";
import { WardsDirectory } from "./pages/WardsDirectory";
import { Interventions } from "./pages/Interventions";
import { Reports } from "./pages/Reports";

export const AppRouter = () => (
  <AuthProvider>
    <CityProvider>
      <Router>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route element={<ProtectedRoute />}>
            <Route element={<Layout />}>
              <Route path="/" element={<Dashboard />} />
              <Route path="/map" element={<MapView />} />
              <Route path="/ward/:wardId" element={<WardDetail />} />
              <Route path="/recommendations" element={<AIRecommendations />} />
              <Route path="/wards-directory" element={<WardsDirectory />} />
              <Route path="/interventions" element={<Interventions />} />
              <Route path="/reports" element={<Reports />} />
            </Route>
          </Route>
        </Routes>
      </Router>
    </CityProvider>
  </AuthProvider>
);

export default AppRouter;
