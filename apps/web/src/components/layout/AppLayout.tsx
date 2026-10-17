import { useState } from "react";
import { NavLink, Outlet, useNavigate } from "react-router-dom";
import { useMe } from "@/api/queries/me";
import { useAuth } from "@/auth/AuthProvider";
import Button from "@/components/ui/Button";

const NAV_ITEMS = [
  { to: "/campaigns", label: "Campaigns" },
  { to: "/creators", label: "Creators" },
];

export default function AppLayout() {
  const navigate = useNavigate();
  const { user, signOut } = useAuth();
  const me = useMe();
  const [signingOut, setSigningOut] = useState(false);

  async function handleSignOut() {
    setSigningOut(true);
    try {
      await signOut();
    } finally {
      navigate("/login", { replace: true });
    }
  }

  const displayName = me.data?.name ?? user?.signInDetails?.loginId ?? "";

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="border-b border-gray-200 bg-white">
        <div className="mx-auto flex max-w-6xl flex-wrap items-center gap-x-6 gap-y-2 px-4 py-3">
          <span className="font-bold tracking-tight">
            Hookd <span className="text-brand">Tracker</span>
          </span>
          <nav className="flex gap-4 text-sm">
            {NAV_ITEMS.map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                className={({ isActive }) =>
                  isActive ? "font-medium text-gray-900" : "text-gray-500 hover:text-gray-900"
                }
              >
                {item.label}
              </NavLink>
            ))}
          </nav>
          <div className="ml-auto flex items-center gap-3">
            <span className="max-w-48 truncate text-sm text-gray-600" title={displayName}>
              {displayName}
            </span>
            <Button variant="secondary" onClick={handleSignOut} loading={signingOut}>
              Log out
            </Button>
          </div>
        </div>
      </header>
      {me.isError && (
        <p role="alert" className="mx-auto max-w-6xl px-4 pt-4 text-sm text-behind">
          {me.error.message}
        </p>
      )}
      <main className="mx-auto max-w-6xl">
        <Outlet />
      </main>
    </div>
  );
}
