import { Outlet } from "react-router-dom";

// Redirects to /login when signed out. TODO: check auth state.
export default function ProtectedRoute() {
  return <Outlet />;
}
