import { type FormEvent, useState } from "react";
import { useCreatorCampaigns } from "@/api/queries/creators";
import { type Post, useMovePost } from "@/api/queries/posts";
import Alert from "@/components/ui/Alert";
import Button from "@/components/ui/Button";
import Modal from "@/components/ui/Modal";
import SelectField from "@/components/ui/SelectField";

interface MovePostDialogProps {
  /** The post to move; the dialog is closed while this is undefined. */
  post?: Post;
  onClose: () => void;
}

// Move a post to another campaign the same creator is on (US-16).
export default function MovePostDialog({ post, onClose }: MovePostDialogProps) {
  return (
    <Modal open={post !== undefined} title="Move post" onClose={onClose}>
      {post && <MovePostForm key={post.id} post={post} onClose={onClose} />}
    </Modal>
  );
}

function MovePostForm({ post, onClose }: { post: Post; onClose: () => void }) {
  const campaigns = useCreatorCampaigns(post.creator.id);
  const move = useMovePost();
  const destinations = (campaigns.data ?? []).filter(
    (c) => c.campaign_id !== post.campaign_id && c.status === "active",
  );
  const [campaignId, setCampaignId] = useState("");
  const chosen = campaignId || destinations[0]?.campaign_id || "";

  function handleSubmit(event: FormEvent) {
    event.preventDefault();
    if (chosen) move.mutate({ postId: post.id, campaignId: chosen }, { onSuccess: onClose });
  }

  if (campaigns.isPending) return <p className="text-sm text-gray-500">Loading campaigns…</p>;
  if (campaigns.isError) return <Alert>{campaigns.error.message}</Alert>;

  if (destinations.length === 0) {
    return (
      <div className="flex flex-col gap-4 text-sm text-gray-600">
        <p>
          {post.creator.name} isn't on any other active campaign. Assign them to the right campaign first, or remove
          this post instead.
        </p>
        <div className="flex justify-end">
          <Button variant="secondary" onClick={onClose}>
            Close
          </Button>
        </div>
      </div>
    );
  }

  return (
    <form onSubmit={handleSubmit} className="flex flex-col gap-4">
      <p className="text-sm text-gray-600">
        Count this post by <span className="font-medium text-gray-900">@{post.creator.handle}</span> toward another of
        their campaigns. Sync won't move it back.
      </p>
      {move.error && <Alert>{move.error.message}</Alert>}
      <SelectField
        label="Campaign"
        options={destinations.map((c) => ({ value: c.campaign_id, label: `${c.name} (${c.brand})` }))}
        value={chosen}
        onChange={(e) => setCampaignId(e.target.value)}
      />
      <div className="mt-2 flex flex-col-reverse gap-2 sm:flex-row sm:justify-end">
        <Button type="button" variant="secondary" onClick={onClose} disabled={move.isPending}>
          Cancel
        </Button>
        <Button type="submit" loading={move.isPending}>
          Move post
        </Button>
      </div>
    </form>
  );
}
