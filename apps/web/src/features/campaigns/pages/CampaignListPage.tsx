import { useState } from "react";
import {
  type Campaign,
  type CampaignListItem,
  useArchiveCampaign,
  useCampaigns,
  useDeleteCampaign,
  useRestoreCampaign,
} from "@/api/queries/campaigns";
import Alert from "@/components/ui/Alert";
import Button from "@/components/ui/Button";
import ConfirmDialog from "@/components/ui/ConfirmDialog";
import PageHeader from "@/components/ui/PageHeader";
import SearchField from "@/components/ui/SearchField";
import StatCard from "@/components/ui/StatCard";
import Tabs from "@/components/ui/Tabs";
import BehindTargetList from "@/features/dashboard/components/BehindTargetList";
import CampaignCard from "../components/CampaignCard";
import CampaignFormDialog from "../components/CampaignFormDialog";

type Tab = "active" | "live" | "upcoming" | "ended" | "archived";

const TAB_FILTERS: Record<Tab, (c: CampaignListItem) => boolean> = {
  active: (c) => c.status === "active",
  live: (c) => c.status === "active" && c.phase === "live",
  upcoming: (c) => c.status === "active" && c.phase === "upcoming",
  ended: (c) => c.status === "active" && c.phase === "ended",
  archived: (c) => c.status === "archived",
};

const TAB_LABELS: Record<Tab, string> = {
  active: "All campaigns",
  live: "Live",
  upcoming: "Upcoming",
  ended: "Ended",
  archived: "Archived",
};

// All campaigns with status and progress (US-03 to US-06).
export default function CampaignListPage() {
  const [tab, setTab] = useState<Tab>("active");
  const [search, setSearch] = useState("");
  const campaigns = useCampaigns("all");
  const archive = useArchiveCampaign();
  const restore = useRestoreCampaign();
  const remove = useDeleteCampaign();

  const [formOpen, setFormOpen] = useState(false);
  const [editing, setEditing] = useState<Campaign | undefined>();
  const [deleting, setDeleting] = useState<CampaignListItem | undefined>();

  const busyId = (archive.isPending && archive.variables) || (restore.isPending && restore.variables) || undefined;
  const actionError = archive.error?.message ?? restore.error?.message;

  const all = campaigns.data ?? [];
  const needle = search.trim().toLowerCase();
  const shown = all
    .filter(TAB_FILTERS[tab])
    .filter((c) => !needle || c.name.toLowerCase().includes(needle) || c.brand.toLowerCase().includes(needle));

  const active = all.filter(TAB_FILTERS.active);
  const live = all.filter(TAB_FILTERS.live);
  const brands = new Set(live.map((c) => c.brand.toLowerCase())).size;
  const posts = live.reduce((sum, c) => sum + (c.progress?.posts ?? 0), 0);
  const target = live.reduce((sum, c) => sum + (c.progress?.target_posts ?? 0), 0);
  const behind = live.reduce((sum, c) => sum + (c.progress?.behind ?? 0), 0);
  const creators = live.reduce((sum, c) => sum + (c.progress?.creators ?? 0), 0);

  function openCreate() {
    setEditing(undefined);
    setFormOpen(true);
  }

  return (
    <div className="flex flex-col gap-[26px]">
      <PageHeader
        title="Campaigns"
        description="Big ideas, brought to life. Keep every collaboration moving."
        actions={
          <Button icon="plus" onClick={openCreate}>
            Create campaign
          </Button>
        }
      />

      {all.length > 0 && (
        <div className="grid grid-cols-2 gap-6 rounded-card border border-line bg-surface p-[22px] lg:grid-cols-4">
          <StatCard
            variant="inline"
            icon="megaphone"
            label="Live campaigns"
            value={live.length}
            note={live.length ? `Across ${brands} ${brands === 1 ? "brand" : "brands"}` : `${active.length} active in total`}
          />
          <StatCard
            variant="inline"
            icon="users"
            label="Creator assignments"
            value={creators}
            note="On live campaigns"
          />
          <StatCard
            variant="inline"
            icon="clapperboard"
            label="Posts this period"
            value={target ? `${posts} / ${target}` : "–"}
            note={target ? `${Math.round((posts / target) * 100)}% of live campaign targets` : "No targets set yet"}
          />
          <StatCard
            variant="inline"
            icon="alert"
            label="Behind target"
            value={behind}
            note={behind ? "Creators to chase this period" : "Everyone is on pace"}
          />
        </div>
      )}

      <BehindTargetList />

      <div className="flex flex-col gap-5">
        <Tabs
          label="Campaign status"
          value={tab}
          onChange={setTab}
          tabs={(Object.keys(TAB_LABELS) as Tab[]).map((value) => ({
            value,
            label: TAB_LABELS[value],
            count: campaigns.data ? all.filter(TAB_FILTERS[value]).length : undefined,
          }))}
        />
        {all.length > 0 && (
          <SearchField label="Search campaigns" placeholder="Search campaigns..." value={search} onChange={setSearch} />
        )}

        {actionError && <Alert>{actionError}</Alert>}
        {campaigns.isPending && <p className="text-[13px] text-ink-muted">Loading campaigns…</p>}
        {campaigns.isError && <Alert>{campaigns.error.message}</Alert>}

        {campaigns.data && shown.length === 0 && (
          <div className="rounded-card border border-dashed border-line-strong bg-surface px-6 py-12 text-center">
            <p className="font-medium text-ink">
              {needle ? `No campaigns match “${search.trim()}”` : tab === "archived" ? "No archived campaigns" : "No campaigns here yet"}
            </p>
            <p className="mt-1 text-[13px] text-ink-muted">
              {tab === "archived"
                ? "Campaigns you archive appear here and can be restored."
                : "Create a campaign, then assign creators and set their posting targets."}
            </p>
            {all.length === 0 && (
              <Button className="mt-4" icon="plus" onClick={openCreate}>
                Create your first campaign
              </Button>
            )}
          </div>
        )}

        {shown.length > 0 && (
          <>
            <ul className="grid gap-5 sm:grid-cols-2 xl:grid-cols-3">
              {shown.map((campaign) => (
                <CampaignCard
                  key={campaign.id}
                  campaign={campaign}
                  busy={busyId === campaign.id}
                  onEdit={() => {
                    setEditing(campaign);
                    setFormOpen(true);
                  }}
                  onArchiveToggle={() =>
                    campaign.status === "archived" ? restore.mutate(campaign.id) : archive.mutate(campaign.id)
                  }
                  onDelete={() => setDeleting(campaign)}
                />
              ))}
            </ul>
            <p className="text-xs text-ink-muted">
              Showing {shown.length} of {all.filter(TAB_FILTERS[tab]).length} campaigns
            </p>
          </>
        )}
      </div>

      <CampaignFormDialog open={formOpen} campaign={editing} onClose={() => setFormOpen(false)} />

      <ConfirmDialog
        open={deleting !== undefined}
        title="Delete campaign?"
        confirmLabel="Delete campaign"
        danger
        pending={remove.isPending}
        error={remove.error?.message}
        onCancel={() => {
          remove.reset();
          setDeleting(undefined);
        }}
        onConfirm={() =>
          deleting &&
          remove.mutate(deleting.id, {
            onSuccess: () => setDeleting(undefined),
          })
        }
      >
        <p>
          <span className="font-medium text-ink">{deleting?.name}</span> and its tracking data will be permanently
          deleted. To keep it for your records, archive it instead.
        </p>
      </ConfirmDialog>
    </div>
  );
}
