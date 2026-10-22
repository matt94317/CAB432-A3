import { Navigate, Outlet } from "react-router-dom";
import FullPageSpinner from "@/components/ui/FullPageSpinner";
import { useAuth } from "./AuthProvider";

// Login and sign-up pages: send managers who are already signed in to the app.
export default function PublicOnlyRoute() {
  const { status } = useAuth();

  if (status === "loading") return <FullPageSpinner />;
  if (status === "signedIn") return <Navigate to="/overview" replace />;
  return <Outlet />;
}
