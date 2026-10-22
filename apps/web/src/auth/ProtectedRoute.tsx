import { Navigate, Outlet, useLocation } from "react-router-dom";
import FullPageSpinner from "@/components/ui/FullPageSpinner";
import { useAuth } from "./AuthProvider";

// Only signed-in managers get past here; everyone else goes to /login and comes back after.
export default function ProtectedRoute() {
  const { status } = useAuth();
  const location = useLocation();

  if (status === "loading") return <FullPageSpinner />;
  if (status === "signedOut") {
    return <Navigate to="/login" replace state={{ from: location.pathname + location.search }} />;
  }
  return <Outlet />;
}
