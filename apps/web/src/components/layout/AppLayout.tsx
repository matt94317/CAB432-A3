import { NavLink, Outlet } from "react-router-dom";

export default function AppLayout() {
  return (
    <div className="flex min-h-screen">
      <nav className="flex w-56 flex-col gap-2 border-r p-4">
        <NavLink to="/campaigns">Campaigns</NavLink>
        <NavLink to="/creators">Creators</NavLink>
      </nav>
      <main className="flex-1">
        <Outlet />
      </main>
    </div>
  );
}
