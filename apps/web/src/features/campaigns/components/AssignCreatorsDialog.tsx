import { type FormEvent, useState } from "react";
import { Link } from "react-router-dom";
import { type TargetPeriod, useAssignCreators } from "@/api/queries/assignments";
import { useCreators } from "@/api/queries/creators";
import Alert from "@/components/ui/Alert";
import Button from "@/components/ui/Button";
import Modal from "@/components/ui/Modal";
import { matchesSearch } from "@/features/creators/search";
import TargetFields, { TARGET_POSTS_ERROR, parseTargetPosts } from "./TargetFields";

interface AssignCreatorsDialogProps {
  open: boolean;
  campaignId: string;
  /** Creators already on the campaign; they aren't offered again. */
  assignedIds: Set<string>;
  onClose: () => void;
}

// Pick roster creators for a campaign and give them a starting target (US-09, US-10).
export default function AssignCreatorsDialog({ open, campaignId, assignedIds, onClose }: AssignCreatorsDialogProps) {
  return (
    <Modal open={open} title="Assign creators" onClose={onClose}>
      {/* Fresh selection each time it opens */}
      {open && <AssignCreatorsForm campaignId={campaignId} assignedIds={assignedIds} onClose={onClose} />}
    </Modal>
  );
}

function AssignCreatorsForm({ campaignId, assignedIds, onClose }: Omit<AssignCreatorsDialogProps, "open">) {
  const creators = useCreators();
  const assign = useAssignCreators(campaignId);
  const [search, setSearch] = useState("");
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [posts, setPosts] = useState("3");
  const [period, setPeriod] = useState<TargetPeriod>("week");
  const [checkError, setCheckError] = useState<string | null>(null);

  const available = creators.data?.filter((c) => !assignedIds.has(c.id)) ?? [];
  const shown = available.filter((c) => matchesSearch(c, search));

  function toggle(id: string) {
    setSelected((current) => {
      const next = new Set(current);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  }

  function handleSubmit(event: FormEvent) {
    event.preventDefault();
    const targetPosts = parseTargetPosts(posts);
    if (selected.size === 0) return setCheckError("Choose at least one creator.");
    if (targetPosts === null) return setCheckError(TARGET_POSTS_ERROR);
    setCheckError(null);
    assign.mutate(
      { creator_ids: [...selected], target_posts: targetPosts, target_period: period },
      { onSuccess: onClose },
    );
  }

  if (creators.isPending) return <p className="text-sm text-ink-muted">Loading your roster…</p>;
  if (creators.isError) return <Alert>{creators.error.message}</Alert>;

  if (available.length === 0) {
    return (
      <div className="flex flex-col gap-4 text-sm text-ink-muted">
        <p>
          {creators.data.length === 0
            ? "Your roster is empty. Add creators first, then assign them here."
            : "Everyone in your roster is already on this campaign."}
        </p>
        <div className="flex flex-col-reverse gap-2 sm:flex-row sm:justify-end">
          <Button variant="secondary" onClick={onClose}>
            Close
          </Button>
          <Link
            to="/creators"
            className="rounded-lg bg-brand px-4 py-2.5 text-center text-sm font-medium text-white hover:opacity-90"
          >
            Go to creators
          </Link>
        </div>
      </div>
    );
  }

  const shownError = checkError ?? assign.error?.message;

  return (
    <form onSubmit={handleSubmit} className="flex flex-col gap-4" noValidate>
      {shownError && <Alert>{shownError}</Alert>}

      <fieldset className="flex flex-col gap-2">
        <legend className="text-sm font-medium text-ink">Creators</legend>
        {available.length > 6 && (
          <input
            type="search"
            aria-label="Search creators"
            placeholder="Search by name, handle or niche"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="mt-1.5 rounded-lg border border-line px-3 py-2 text-sm outline-none focus:border-brand focus:ring-2 focus:ring-brand/20"
          />
        )}
        <ul className="mt-1.5 max-h-64 divide-y divide-line overflow-y-auto rounded-lg border border-line">
          {shown.map((creator) => (
            <li key={creator.id}>
              <label className="flex cursor-pointer items-center gap-3 px-3 py-2.5 hover:bg-canvas">
                <input
                  type="checkbox"
                  className="size-4 accent-brand"
                  checked={selected.has(creator.id)}
                  onChange={() => toggle(creator.id)}
                />
                <span className="min-w-0">
                  <span className="block truncate text-sm font-medium text-ink">{creator.name}</span>
                  <span className="block truncate text-xs text-ink-muted">
                    @{creator.handle}
                    {creator.niche && ` · ${creator.niche}`}
                  </span>
                </span>
              </label>
            </li>
          ))}
          {shown.length === 0 && <li className="px-3 py-2.5 text-sm text-ink-muted">No creators match.</li>}
        </ul>
      </fieldset>

      <div>
        <TargetFields posts={posts} period={period} onPostsChange={setPosts} onPeriodChange={setPeriod} />
        <p className="mt-1.5 text-xs text-ink-muted">Everyone starts on this target. You can change each creator's later.</p>
      </div>

      <div className="mt-2 flex flex-col-reverse gap-2 sm:flex-row sm:justify-end">
        <Button type="button" variant="secondary" onClick={onClose} disabled={assign.isPending}>
          Cancel
        </Button>
        <Button type="submit" loading={assign.isPending}>
          {selected.size > 1 ? `Assign ${selected.size} creators` : "Assign creator"}
        </Button>
      </div>
    </form>
  );
}
