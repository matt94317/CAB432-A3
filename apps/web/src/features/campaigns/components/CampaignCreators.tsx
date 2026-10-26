import { useState } from "react";
import { Link } from "react-router-dom";
import { type Assignment, useAssignments, useUnassignCreator } from "@/api/queries/assignments";
import type { Campaign } from "@/api/queries/campaigns";
import { useCampaignDashboard } from "@/api/queries/dashboard";
import Alert from "@/components/ui/Alert";
import Avatar from "@/components/ui/Avatar";
import { demoAvatar } from "@/lib/demoImages";
import Badge from "@/components/ui/Badge";
import Button from "@/components/ui/Button";
import ConfirmDialog from "@/components/ui/ConfirmDialog";
import Icon from "@/components/ui/Icon";
import Menu from "@/components/ui/Menu";
import PeriodProgress from "@/features/dashboard/components/PeriodProgress";
import ProgressStatusBadge from "@/features/dashboard/components/ProgressStatusBadge";
import { formatRelative } from "@/lib/format";
import { formatTarget } from "@/lib/targets";
import AssignCreatorsDialog from "./AssignCreatorsDialog";
import TargetEditor from "./TargetEditor";

// Creators on a campaign: posts vs target this period, behind first (US-19, US-22), and
// assign, change target, remove (US-09 to US-12).
export default function CampaignCreators({ campaign }: { campaign: Campaign }) {
  const assignments = useAssignments(campaign.id);
  const dashboard = useCampaignDashboard(campaign.id);
  const unassign = useUnassignCreator(campaign.id);
  const [assigning, setAssigning] = useState(false);
  const [editing, setEditing] = useState<Assignment | undefined>();
  const [removing, setRemoving] = useState<Assignment | undefined>();

  const editable = campaign.status === "active";
  const progress = new Map(dashboard.data?.creators.map((row) => [row.creator.id, row]));
  // Dashboard order (behind first); assignments not in it yet (just added) go last
  const order = new Map(dashboard.data?.creators.map((row, i) => [row.creator.id, i]));
  const rows = [...(assignments.data ?? [])].sort(
    (a, b) => (order.get(a.creator.id) ?? Infinity) - (order.get(b.creator.id) ?? Infinity),
  );
  const behind = dashboard.data?.behind_count ?? 0;

  return (
    <section className="overflow-hidden rounded-card border border-line bg-surface">
      <div className="flex flex-wrap items-center justify-between gap-3 px-5 py-4">
        <div className="flex flex-wrap items-center gap-3">
          <h2 className="text-base text-ink">Creators</h2>
          {behind > 0 && <Badge tone="warning">{behind} behind target</Badge>}
        </div>
        {editable && rows.length > 0 && (
          <Button variant="secondary" size="sm" icon="plus" onClick={() => setAssigning(true)}>
            Assign creators
          </Button>
        )}
      </div>

      {assignments.isPending && <p className="px-5 pb-5 text-[13px] text-ink-muted">Loading creators…</p>}
      {assignments.isError && (
        <div className="px-5 pb-5">
          <Alert>{assignments.error.message}</Alert>
        </div>
      )}

      {assignments.data?.length === 0 && (
        <div className="border-t border-line px-6 py-12 text-center">
          <p className="font-medium text-ink">No creators assigned yet</p>
          <p className="mt-1 text-[13px] text-ink-muted">
            {editable
              ? "Assign creators from your roster and set how many posts each should publish per week or month."
              : "Restore this campaign to assign creators."}
          </p>
          {editable && (
            <Button className="mt-4" icon="plus" onClick={() => setAssigning(true)}>
              Assign creators
            </Button>
          )}
        </div>
      )}

      {rows.length > 0 && (
        <>
          <div className="hidden h-11 items-center gap-4 bg-sunken px-5 text-[9px] font-semibold tracking-wide text-ink-muted sm:flex">
            <span className="flex-1">CREATOR</span>
            <span className="w-44">THIS PERIOD</span>
            <span className="w-28 text-right">STATUS</span>
            {editable && <span className="w-[26px]" />}
          </div>
          <ul className="divide-y divide-line border-t border-line sm:border-t-0">
            {rows.map((assignment) => {
              const row = progress.get(assignment.creator.id);
              return (
                <li key={assignment.id} className="flex flex-wrap items-center gap-x-4 gap-y-2 px-5 py-[13px]">
                  <div className="flex min-w-0 flex-1 items-center gap-2.5">
                    <Avatar name={assignment.creator.name} size="sm" src={demoAvatar(assignment.creator.handle)} />
                    <div className="min-w-0">
                      <Link
                        to={`/creators/${assignment.creator.id}`}
                        className="block truncate text-xs font-medium text-ink hover:text-brand"
                      >
                        {assignment.creator.name}
                      </Link>
                      <p className="truncate text-[10px] text-ink-muted">
                        @{assignment.creator.handle}
                        {" · "}
                        {assignment.creator.last_synced_at
                          ? `synced ${formatRelative(assignment.creator.last_synced_at)}`
                          : "not synced yet"}
                      </p>
                    </div>
                  </div>
                  {row ? (
                    <>
                      <PeriodProgress progress={row} />
                      <div className="sm:w-28 sm:text-right">
                        <ProgressStatusBadge status={row.status} />
                      </div>
                    </>
                  ) : (
                    <span className="text-[11px] text-ink-muted sm:w-[17rem]">
                      {formatTarget(assignment.target_posts, assignment.target_period)}
                    </span>
                  )}
                  {editable && (
                    <Menu
                      label={`Actions for ${assignment.creator.name}`}
                      triggerClassName="flex size-[26px] items-center justify-center rounded-full text-ink-muted hover:bg-canvas hover:text-ink"
                      trigger={<Icon name="ellipsis" className="size-4" />}
                      items={[
                        { label: "Change target", onSelect: () => setEditing(assignment) },
                        { label: "Remove from campaign", onSelect: () => setRemoving(assignment), danger: true },
                      ]}
                    />
                  )}
                </li>
              );
            })}
          </ul>
        </>
      )}

      <AssignCreatorsDialog
        open={assigning}
        campaignId={campaign.id}
        assignedIds={new Set(rows.map((a) => a.creator.id))}
        onClose={() => setAssigning(false)}
      />
      <TargetEditor campaignId={campaign.id} assignment={editing} onClose={() => setEditing(undefined)} />
      <ConfirmDialog
        open={removing !== undefined}
        title="Remove from campaign?"
        confirmLabel="Remove from campaign"
        danger
        pending={unassign.isPending}
        error={unassign.error?.message}
        onCancel={() => {
          unassign.reset();
          setRemoving(undefined);
        }}
        onConfirm={() =>
          removing && unassign.mutate(removing.creator.id, { onSuccess: () => setRemoving(undefined) })
        }
      >
        <p>
          <span className="font-medium text-ink">{removing?.creator.name}</span> will be taken off{" "}
          {campaign.name}, and their posts in it will no longer be tracked. They stay in your roster.
        </p>
      </ConfirmDialog>
    </section>
  );
}
