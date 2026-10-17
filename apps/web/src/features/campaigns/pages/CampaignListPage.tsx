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
import CampaignCard from "../components/CampaignCard";
import CampaignFormDialog from "../components/CampaignFormDialog";

const TABS = [
  { value: "active", label: "Active" },
  { value: "archived", label: "Archived" },
] as const;

type Tab = (typeof TABS)[number]["value"];

// All campaigns with status and progress (US-03 to US-06).
export default function CampaignListPage() {
  const [tab, setTab] = useState<Tab>("active");
  const campaigns = useCampaigns(tab);
  const archive = useArchiveCampaign();
  const restore = useRestoreCampaign();
  const remove = useDeleteCampaign();

  const [formOpen, setFormOpen] = useState(false);
  const [editing, setEditing] = useState<Campaign | undefined>();
  const [deleting, setDeleting] = useState<CampaignListItem | undefined>();

  const busyId = (archive.isPending && archive.variables) || (restore.isPending && restore.variables) || undefined;
  const actionError = archive.error?.message ?? restore.error?.message;

  function openCreate() {
    setEditing(undefined);
    setFormOpen(true);
  }

  return (
    <div className="px-4 py-6 sm:px-6">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold text-gray-900">Campaigns</h1>
          <p className="mt-1 text-sm text-gray-500">Every campaign, its dates and tracking hashtags.</p>
        </div>
        <Button onClick={openCreate}>New campaign</Button>
      </div>

      <div className="mt-6 flex gap-1 border-b border-gray-200" role="tablist" aria-label="Campaign status">
        {TABS.map((t) => (
          <button
            key={t.value}
            role="tab"
            aria-selected={tab === t.value}
            onClick={() => setTab(t.value)}
            className={`-mb-px border-b-2 px-3 py-2 text-sm font-medium ${
              tab === t.value ? "border-brand text-gray-900" : "border-transparent text-gray-500 hover:text-gray-900"
            }`}
          >
            {t.label}
          </button>
        ))}
      </div>

      <div className="mt-6">
        {actionError && (
          <div className="mb-4">
            <Alert>{actionError}</Alert>
          </div>
        )}
        {campaigns.isPending && <p className="text-sm text-gray-500">Loading campaigns…</p>}
        {campaigns.isError && <Alert>{campaigns.error.message}</Alert>}
        {campaigns.data?.length === 0 && (
          <div className="rounded-xl border border-dashed border-gray-300 bg-white px-6 py-12 text-center">
            <p className="font-medium text-gray-900">
              {tab === "active" ? "No campaigns yet" : "No archived campaigns"}
            </p>
            <p className="mt-1 text-sm text-gray-500">
              {tab === "active"
                ? "Create a campaign, then assign creators and set their posting targets."
                : "Campaigns you archive appear here and can be restored."}
            </p>
            {tab === "active" && (
              <Button className="mt-4" onClick={openCreate}>
                Create your first campaign
              </Button>
            )}
          </div>
        )}
        {campaigns.data && campaigns.data.length > 0 && (
          <ul className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {campaigns.data.map((campaign) => (
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
          <span className="font-medium text-gray-900">{deleting?.name}</span> and its tracking data will be
          permanently deleted. To keep it for your records, archive it instead.
        </p>
      </ConfirmDialog>
    </div>
  );
}
