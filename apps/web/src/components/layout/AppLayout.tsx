import { useState } from "react";
import { Outlet, useLocation, useNavigate } from "react-router-dom";
import { useMe } from "@/api/queries/me";
import { useAuth } from "@/auth/AuthProvider";
import Icon from "@/components/ui/Icon";
import BrandMark from "./BrandMark";
import Sidebar from "./Sidebar";

const SECTIONS: [prefix: string, label: string][] = [
  ["/overview", "Overview"],
  ["/campaigns", "Campaigns"],
  ["/creators", "Creators"],
  ["/posts", "Post tracking"],
];

// Signed-in shell: sidebar (a drawer on small screens), header with breadcrumb, page.
export default function AppLayout() {
  const navigate = useNavigate();
  const { pathname } = useLocation();
  const { user, signOut } = useAuth();
  const me = useMe();
  const [signingOut, setSigningOut] = useState(false);
  const [drawerOpen, setDrawerOpen] = useState(false);

  async function handleSignOut() {
    setSigningOut(true);
    try {
      await signOut();
    } finally {
      navigate("/login", { replace: true });
    }
  }

  const section = SECTIONS.find(([prefix]) => pathname.startsWith(prefix))?.[1];
  const sidebar = (
    <Sidebar
      name={me.data?.name ?? ""}
      email={me.data?.email ?? user?.signInDetails?.loginId ?? ""}
      signingOut={signingOut}
      onSignOut={handleSignOut}
      onNavigate={() => setDrawerOpen(false)}
    />
  );

  return (
    <div className="min-h-screen bg-canvas lg:pl-56">
      <aside className="fixed inset-y-0 left-0 hidden w-56 lg:block">{sidebar}</aside>

      {drawerOpen && (
        <div className="fixed inset-0 z-40 lg:hidden">
          <button
            aria-label="Close menu"
            className="absolute inset-0 bg-ink/40"
            onClick={() => setDrawerOpen(false)}
          />
          <aside className="absolute inset-y-0 left-0 w-64 max-w-[85vw]">{sidebar}</aside>
        </div>
      )}

      <header className="sticky top-0 z-30 flex h-16 items-center gap-3 border-b border-line bg-surface px-4 sm:px-8 lg:h-[76px]">
        <button
          type="button"
          aria-label="Open menu"
          onClick={() => setDrawerOpen(true)}
          className="-ml-1 flex size-9 flex-col items-center justify-center gap-[3px] rounded-lg hover:bg-canvas lg:hidden"
        >
          {[0, 1, 2].map((i) => (
            <span key={i} className="block h-px w-4 bg-ink" />
          ))}
        </button>
        <span className="lg:hidden">
          <BrandMark />
        </span>
        <nav aria-label="Breadcrumb" className="hidden items-center gap-[9px] text-xs lg:flex">
          <span className="text-ink-muted">Workspace</span>
          {section && (
            <>
              <Icon name="chevron-right" className="size-3 text-ink-muted" />
              <span className="font-medium text-ink">{section}</span>
            </>
          )}
        </nav>
      </header>

      {me.isError && (
        <p role="alert" className="px-4 pt-4 text-[13px] text-danger sm:px-8">
          {me.error.message}
        </p>
      )}
      <main className="mx-auto max-w-[1216px] px-4 py-6 sm:px-8 sm:py-8">
        <Outlet />
      </main>
    </div>
  );
}
