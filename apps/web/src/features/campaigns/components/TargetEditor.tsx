import { type FormEvent, useState } from "react";
import { type Assignment, type TargetPeriod, useUpdateTarget } from "@/api/queries/assignments";
import Alert from "@/components/ui/Alert";
import Button from "@/components/ui/Button";
import Modal from "@/components/ui/Modal";
import TargetFields, { TARGET_POSTS_ERROR, parseTargetPosts } from "./TargetFields";

interface TargetEditorProps {
  campaignId: string;
  /** The creator's assignment to edit; the dialog is closed while this is undefined. */
  assignment?: Assignment;
  onClose: () => void;
}

// Change a creator's target in one campaign when the deal changes (US-11).
export default function TargetEditor({ campaignId, assignment, onClose }: TargetEditorProps) {
  return (
    <Modal open={assignment !== undefined} title="Change target" onClose={onClose}>
      {assignment && <TargetForm key={assignment.id} campaignId={campaignId} assignment={assignment} onClose={onClose} />}
    </Modal>
  );
}

function TargetForm({ campaignId, assignment, onClose }: { campaignId: string; assignment: Assignment; onClose: () => void }) {
  const update = useUpdateTarget(campaignId);
  const [posts, setPosts] = useState(String(assignment.target_posts));
  const [period, setPeriod] = useState<TargetPeriod>(assignment.target_period);
  const [checkError, setCheckError] = useState<string | null>(null);

  function handleSubmit(event: FormEvent) {
    event.preventDefault();
    const targetPosts = parseTargetPosts(posts);
    if (targetPosts === null) return setCheckError(TARGET_POSTS_ERROR);
    setCheckError(null);
    if (targetPosts === assignment.target_posts && period === assignment.target_period) return onClose();
    update.mutate(
      { creatorId: assignment.creator.id, changes: { target_posts: targetPosts, target_period: period } },
      { onSuccess: onClose },
    );
  }

  const shownError = checkError ?? update.error?.message;

  return (
    <form onSubmit={handleSubmit} className="flex flex-col gap-4" noValidate>
      <p className="text-sm text-gray-600">
        New target for <span className="font-medium text-gray-900">{assignment.creator.name}</span> on this campaign
        only.
      </p>
      {shownError && <Alert>{shownError}</Alert>}
      <TargetFields posts={posts} period={period} onPostsChange={setPosts} onPeriodChange={setPeriod} autoFocus />
      <div className="mt-2 flex flex-col-reverse gap-2 sm:flex-row sm:justify-end">
        <Button type="button" variant="secondary" onClick={onClose} disabled={update.isPending}>
          Cancel
        </Button>
        <Button type="submit" loading={update.isPending}>
          Save target
        </Button>
      </div>
    </form>
  );
}
