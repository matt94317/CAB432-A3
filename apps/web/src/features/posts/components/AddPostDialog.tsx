import { type FormEvent, useState } from "react";
import { useCampaigns } from "@/api/queries/campaigns";
import { useAddPost } from "@/api/queries/posts";
import Alert from "@/components/ui/Alert";
import Button from "@/components/ui/Button";
import Modal from "@/components/ui/Modal";
import SelectField from "@/components/ui/SelectField";
import TextField from "@/components/ui/TextField";
import { toIsoDate } from "@/lib/format";

const METRICS = [
  { key: "views", label: "Views" },
  { key: "likes", label: "Likes" },
  { key: "comments", label: "Comments" },
  { key: "shares", label: "Shares" },
] as const;

type Metric = (typeof METRICS)[number]["key"];

interface AddPostDialogProps {
  open: boolean;
  /** Add to this campaign; omit to let the manager pick one. */
  campaignId?: string;
  onClose: () => void;
}

// Manually add a post by link when automatic sync misses one (US-15).
export default function AddPostDialog({ open, campaignId, onClose }: AddPostDialogProps) {
  return (
    <Modal open={open} title="Add a post" onClose={onClose}>
      {open && <AddPostForm campaignId={campaignId} onClose={onClose} />}
    </Modal>
  );
}

function AddPostForm({ campaignId, onClose }: Omit<AddPostDialogProps, "open">) {
  const add = useAddPost();
  const campaigns = useCampaigns("active");
  const [chosenCampaign, setChosenCampaign] = useState("");
  const targetCampaign = campaignId ?? (chosenCampaign || campaigns.data?.[0]?.id || "");
  const [url, setUrl] = useState("");
  const [postedOn, setPostedOn] = useState(toIsoDate(new Date()));
  const [caption, setCaption] = useState("");
  const [metrics, setMetrics] = useState<Record<Metric, string>>({ views: "", likes: "", comments: "", shares: "" });
  const [checkError, setCheckError] = useState<string | null>(null);

  function handleSubmit(event: FormEvent) {
    event.preventDefault();
    if (!targetCampaign) return setCheckError("Create a campaign first, then add posts to it.");
    if (!url.trim()) return setCheckError("Paste the post's TikTok link.");
    const counts = Object.fromEntries(METRICS.map(({ key }) => [key, Number(metrics[key] || 0)])) as Record<
      Metric,
      number
    >;
    if (Object.values(counts).some((n) => !Number.isInteger(n) || n < 0)) {
      return setCheckError("Metrics must be whole numbers, 0 or more.");
    }
    setCheckError(null);
    add.mutate(
      { campaignId: targetCampaign, body: { url: url.trim(), posted_on: postedOn, caption: caption.trim(), ...counts } },
      { onSuccess: onClose },
    );
  }

  const shownError = checkError ?? add.error?.message;

  return (
    <form onSubmit={handleSubmit} className="flex flex-col gap-4" noValidate>
      <p className="text-sm text-ink-muted">
        For a post sync missed, for example when the creator forgot the hashtag. Sync won't move or remove posts you
        add here.
      </p>
      {shownError && <Alert>{shownError}</Alert>}
      {!campaignId && (
        <SelectField
          label="Campaign"
          value={targetCampaign}
          onChange={(e) => setChosenCampaign(e.target.value)}
          options={(campaigns.data ?? []).map((c) => ({ value: c.id, label: `${c.name} (${c.brand})` }))}
        />
      )}
      <TextField
        label="TikTok link"
        type="url"
        required
        autoFocus
        placeholder="https://www.tiktok.com/@handle/video/…"
        hint="The creator is found from the @handle in the link."
        value={url}
        onChange={(e) => setUrl(e.target.value)}
      />
      <TextField
        label="Posted on"
        type="date"
        required
        max={toIsoDate(new Date())}
        value={postedOn}
        onChange={(e) => setPostedOn(e.target.value)}
      />
      <TextField
        label="Caption (optional)"
        placeholder="Paste the caption to keep its hashtags"
        value={caption}
        onChange={(e) => setCaption(e.target.value)}
      />
      <fieldset>
        <legend className="text-sm font-medium text-ink">Metrics (optional)</legend>
        <div className="mt-1.5 grid grid-cols-2 gap-3 sm:grid-cols-4">
          {METRICS.map(({ key, label }) => (
            <TextField
              key={key}
              label={label}
              type="number"
              inputMode="numeric"
              min={0}
              placeholder="0"
              value={metrics[key]}
              onChange={(e) => setMetrics((m) => ({ ...m, [key]: e.target.value }))}
            />
          ))}
        </div>
      </fieldset>
      <div className="mt-2 flex flex-col-reverse gap-2 sm:flex-row sm:justify-end">
        <Button type="button" variant="secondary" onClick={onClose} disabled={add.isPending}>
          Cancel
        </Button>
        <Button type="submit" loading={add.isPending}>
          Add post
        </Button>
      </div>
    </form>
  );
}
