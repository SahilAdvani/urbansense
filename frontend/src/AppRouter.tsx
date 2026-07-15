import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import { AuthProvider } from "./hooks/useAuth";
import { ProtectedRoute } from "./components/ProtectedRoute";
import { Layout } from "./components/Layout";
import { Login } from "./pages/Login";
import { Dashboard } from "./pages/Dashboard";
import { MapView } from "./pages/MapView";
import { WardDetail } from "./pages/WardDetail";
import { AIRecommendations } from "./pages/AIRecommendations";

export const AppRouter = () => (
  <AuthProvider>
    <Router>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route element={<ProtectedRoute />}>
          <Route element={<Layout />}>
            <Route path="/" element={<Dashboard />} />
            <Route path="/map" element={<MapView />} />
            <Route path="/ward/:wardId" element={<WardDetail />} />
            <Route path="/recommendations" element={<AIRecommendations />} />
          </Route>
        </Route>
      </Routes>
    </Router>
  </AuthProvider>
);

export default AppRouter;
