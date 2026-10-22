import { NavLink } from "react-router-dom";
import { useCampaigns } from "@/api/queries/campaigns";
import Avatar from "@/components/ui/Avatar";
import Icon, { type IconName } from "@/components/ui/Icon";
import Menu from "@/components/ui/Menu";
import BrandMark from "./BrandMark";

interface SidebarProps {
  name: string;
  email: string;
  signingOut: boolean;
  onSignOut: () => void;
  onNavigate?: () => void;
}

// App sidebar from the design. Only pages that exist are listed.
export default function Sidebar({ name, email, signingOut, onSignOut, onNavigate }: SidebarProps) {
  const activeCampaigns = useCampaigns("active").data?.length;
  const items: { to: string; label: string; icon: IconName; count?: number }[] = [
    { to: "/overview", label: "Overview", icon: "layout-dashboard" },
    { to: "/campaigns", label: "Campaigns", icon: "megaphone", count: activeCampaigns },
    { to: "/creators", label: "Creators", icon: "users" },
    { to: "/posts", label: "Post tracking", icon: "clapperboard" },
  ];

  return (
    <div className="flex h-full flex-col justify-between border-r border-line bg-surface px-4 pb-5 pt-[27px]">
      <div className="flex flex-col gap-7">
        <div className="pl-2.5">
          <BrandMark />
        </div>
        <nav aria-label="Workspace" className="flex flex-col gap-[5px]">
          <p className="px-0 text-[10px] font-semibold tracking-wide text-ink-subtle">WORKSPACE</p>
          {items.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              onClick={onNavigate}
              className={({ isActive }) =>
                `flex h-[43px] items-center gap-[11px] rounded-[7px] px-3 text-[13px] ${
                  isActive ? "bg-brand-soft font-semibold text-brand" : "text-ink-muted hover:bg-canvas hover:text-ink"
                }`
              }
            >
              <Icon name={item.icon} className="size-[18px]" />
              <span className="flex-1">{item.label}</span>
              {item.count !== undefined && item.count > 0 && <span className="text-[11px] font-normal">{item.count}</span>}
            </NavLink>
          ))}
        </nav>
      </div>

      <Menu
        label="Account"
        side="top"
        align="left"
        items={[{ label: signingOut ? "Logging out…" : "Log out", onSelect: onSignOut }]}
        triggerClassName="flex w-full items-center gap-2.5 rounded-lg p-[9px] text-left hover:bg-canvas"
        trigger={
          <>
            <Avatar name={name || email} />
            <span className="min-w-0 flex-1">
              <span className="block truncate text-xs font-semibold text-ink">{name || email}</span>
              {name && <span className="block truncate text-[10px] text-ink-muted">{email}</span>}
            </span>
            <Icon name="chevrons-up-down" className="size-3.5 text-ink-muted" />
          </>
        }
      />
    </div>
  );
}
