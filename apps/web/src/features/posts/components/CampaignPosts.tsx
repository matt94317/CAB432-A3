import { useState } from "react";
import { useAssignments } from "@/api/queries/assignments";
import type { Campaign } from "@/api/queries/campaigns";
import { type Post, type SyncRun, useCampaignPosts, useRemovePost, useSyncCampaign } from "@/api/queries/posts";
import Alert from "@/components/ui/Alert";
import Button from "@/components/ui/Button";
import ConfirmDialog from "@/components/ui/ConfirmDialog";
import LastSyncedBadge from "@/features/dashboard/components/LastSyncedBadge";
import AddPostDialog from "./AddPostDialog";
import MovePostDialog from "./MovePostDialog";
import PostTable from "./PostTable";

// A campaign's posts: sync now, last synced, add by link, move and remove (US-13 to US-18).
export default function CampaignPosts({ campaign }: { campaign: Campaign }) {
  const posts = useCampaignPosts(campaign.id);
  const assignments = useAssignments(campaign.id);
  const sync = useSyncCampaign(campaign.id);
  const remove = useRemovePost();
  const [adding, setAdding] = useState(false);
  const [moving, setMoving] = useState<Post | undefined>();
  const [removing, setRemoving] = useState<Post | undefined>();

  const editable = campaign.status === "active";
  const hasCreators = (assignments.data?.length ?? 0) > 0;

  return (
    <section className="mt-8">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex flex-wrap items-baseline gap-x-3">
          <h2 className="text-lg font-semibold text-gray-900">Posts</h2>
          {assignments.data && <LastSyncedBadge assignments={assignments.data} />}
        </div>
        {editable && hasCreators && (
          <div className="flex gap-2">
            <Button variant="secondary" onClick={() => sync.mutate()} loading={sync.isPending}>
              Sync now
            </Button>
            <Button variant="secondary" onClick={() => setAdding(true)}>
              Add post
            </Button>
          </div>
        )}
      </div>

      <div className="mt-3 flex flex-col gap-3">
        {sync.error && <Alert>{sync.error.message}</Alert>}
        {sync.data && <SyncSummary run={sync.data} campaign={campaign} />}
        {posts.isPending && <p className="text-sm text-gray-500">Loading posts…</p>}
        {posts.isError && <Alert>{posts.error.message}</Alert>}

        {posts.data?.length === 0 && (
          <div className="rounded-xl border border-dashed border-gray-300 bg-white px-6 py-10 text-center">
            <p className="font-medium text-gray-900">No posts yet</p>
            <p className="mt-1 text-sm text-gray-500">
              {hasCreators
                ? "Posts using the campaign's hashtags are pulled in automatically. Sync now to check straight away."
                : "Assign creators, and their posts with the campaign's hashtags will show here."}
            </p>
          </div>
        )}

        {posts.data && posts.data.length > 0 && (
          <PostTable posts={posts.data} editable={editable} onMove={setMoving} onRemove={setRemoving} />
        )}
      </div>

      <AddPostDialog open={adding} campaignId={campaign.id} onClose={() => setAdding(false)} />
      <MovePostDialog post={moving} onClose={() => setMoving(undefined)} />
      <ConfirmDialog
        open={removing !== undefined}
        title="Remove post?"
        confirmLabel="Remove post"
        danger
        pending={remove.isPending}
        error={remove.error?.message}
        onCancel={() => {
          remove.reset();
          setRemoving(undefined);
        }}
        onConfirm={() => removing && remove.mutate(removing.id, { onSuccess: () => setRemoving(undefined) })}
      >
        <p>
          This post by <span className="font-medium text-gray-900">@{removing?.creator.handle}</span> will stop counting
          toward {campaign.name}. Sync won't add it back; you can add it again by link.
        </p>
      </ConfirmDialog>
    </section>
  );
}

function SyncSummary({ run, campaign }: { run: SyncRun; campaign: Campaign }) {
  const failed = run.failed ?? [];
  let message: string;
  if (run.mode === "queued") {
    message = `Sync queued for ${run.creators} ${run.creators === 1 ? "creator" : "creators"}. Posts will update shortly.`;
  } else if (run.creators === 0 && failed.length === 0) {
    message =
      campaign.phase === "upcoming"
        ? "Nothing to sync yet: the campaign hasn't started."
        : "Nothing to sync: this campaign's posts are outside the sync window.";
  } else {
    const changes = [
      `${run.added ?? 0} new`,
      `${run.updated ?? 0} updated`,
      ...((run.removed ?? 0) > 0 ? [`${run.removed} no longer matching`] : []),
    ];
    message = `Synced ${run.creators} ${run.creators === 1 ? "creator" : "creators"}: ${changes.join(", ")}.`;
  }

  return (
    <>
      <Alert tone="success">{message}</Alert>
      {failed.length > 0 && (
        <Alert>
          Couldn't sync {failed.map((f) => `@${f.handle}`).join(", ")}: {failed[0].error}
        </Alert>
      )}
    </>
  );
}
