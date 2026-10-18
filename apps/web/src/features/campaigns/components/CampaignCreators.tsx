import { useState } from "react";
import { Link } from "react-router-dom";
import { type Assignment, useAssignments, useUnassignCreator } from "@/api/queries/assignments";
import type { Campaign } from "@/api/queries/campaigns";
import Alert from "@/components/ui/Alert";
import Button from "@/components/ui/Button";
import ConfirmDialog from "@/components/ui/ConfirmDialog";
import { formatRelative } from "@/lib/format";
import { formatTarget } from "@/lib/targets";
import AssignCreatorsDialog from "./AssignCreatorsDialog";
import TargetEditor from "./TargetEditor";

// Creators on a campaign with their targets: assign, change target, remove (US-09 to US-12).
export default function CampaignCreators({ campaign }: { campaign: Campaign }) {
  const assignments = useAssignments(campaign.id);
  const unassign = useUnassignCreator(campaign.id);
  const [assigning, setAssigning] = useState(false);
  const [editing, setEditing] = useState<Assignment | undefined>();
  const [removing, setRemoving] = useState<Assignment | undefined>();

  const editable = campaign.status === "active";
  const rows = assignments.data ?? [];

  return (
    <section className="mt-8">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h2 className="text-lg font-semibold text-gray-900">Creators</h2>
        {editable && rows.length > 0 && (
          <Button variant="secondary" onClick={() => setAssigning(true)}>
            Assign creators
          </Button>
        )}
      </div>

      {assignments.isPending && <p className="mt-3 text-sm text-gray-500">Loading creators…</p>}
      {assignments.isError && (
        <div className="mt-3">
          <Alert>{assignments.error.message}</Alert>
        </div>
      )}

      {assignments.data?.length === 0 && (
        <div className="mt-3 rounded-xl border border-dashed border-gray-300 bg-white px-6 py-12 text-center">
          <p className="font-medium text-gray-900">No creators assigned yet</p>
          <p className="mt-1 text-sm text-gray-500">
            {editable
              ? "Assign creators from your roster and set how many posts each should publish per week or month."
              : "Restore this campaign to assign creators."}
          </p>
          {editable && (
            <Button className="mt-4" onClick={() => setAssigning(true)}>
              Assign creators
            </Button>
          )}
        </div>
      )}

      {rows.length > 0 && (
        <ul className="mt-3 divide-y divide-gray-100 overflow-hidden rounded-xl border border-gray-200 bg-white shadow-sm">
          {rows.map((assignment) => (
            <li key={assignment.id} className="flex flex-wrap items-center gap-x-4 gap-y-2 px-4 py-3">
              <div className="min-w-0 flex-1">
                <Link
                  to={`/creators/${assignment.creator.id}`}
                  className="block truncate font-medium text-gray-900 hover:text-brand"
                >
                  {assignment.creator.name}
                </Link>
                <p className="truncate text-sm text-gray-500">
                  @{assignment.creator.handle}
                  {assignment.creator.niche && ` · ${assignment.creator.niche}`}
                </p>
                <p className="text-xs text-gray-400">
                  {assignment.creator.last_synced_at
                    ? `Synced ${formatRelative(assignment.creator.last_synced_at)}`
                    : "Not synced yet"}
                </p>
              </div>
              <span className="text-sm text-gray-700">
                {formatTarget(assignment.target_posts, assignment.target_period)}
              </span>
              {editable && (
                <div className="flex gap-4">
                  <Button variant="link" onClick={() => setEditing(assignment)}>
                    Change target
                  </Button>
                  <Button variant="link" className="!text-red-600" onClick={() => setRemoving(assignment)}>
                    Remove
                  </Button>
                </div>
              )}
            </li>
          ))}
        </ul>
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
          <span className="font-medium text-gray-900">{removing?.creator.name}</span> will be taken off{" "}
          {campaign.name}, and their posts in it will no longer be tracked. They stay in your roster.
        </p>
      </ConfirmDialog>
    </section>
  );
}
