import { type FormEvent, useState } from "react";
import type { Campaign, CampaignCreate } from "@/api/queries/campaigns";
import Alert from "@/components/ui/Alert";
import Button from "@/components/ui/Button";
import TextField from "@/components/ui/TextField";
import { addDays, toIsoDate } from "@/lib/format";
import { formatHashtags, parseHashtags } from "../hashtags";

interface CampaignFormProps {
  campaign?: Campaign;
  submitLabel: string;
  pending: boolean;
  error?: string | null;
  onSubmit: (values: CampaignCreate) => void;
  onCancel: () => void;
}

// Create/edit campaign form (US-03, US-04).
export default function CampaignForm({ campaign, submitLabel, pending, error, onSubmit, onCancel }: CampaignFormProps) {
  const today = new Date();
  const [name, setName] = useState(campaign?.name ?? "");
  const [brand, setBrand] = useState(campaign?.brand ?? "");
  const [startDate, setStartDate] = useState(campaign?.start_date ?? toIsoDate(today));
  const [endDate, setEndDate] = useState(campaign?.end_date ?? toIsoDate(addDays(today, 30)));
  const [hashtagText, setHashtagText] = useState(campaign ? formatHashtags(campaign.tracking_hashtags) : "");
  const [checkError, setCheckError] = useState<string | null>(null);

  const { tags, invalid } = parseHashtags(hashtagText);

  function handleSubmit(event: FormEvent) {
    event.preventDefault();
    if (!name.trim() || !brand.trim()) return setCheckError("Enter a campaign name and brand.");
    if (endDate < startDate) return setCheckError("The end date must be on or after the start date.");
    if (invalid.length > 0) return setCheckError(`Not a valid hashtag: ${invalid.join(", ")}`);
    if (tags.length === 0) return setCheckError("Add at least one tracking hashtag.");
    setCheckError(null);
    onSubmit({ name: name.trim(), brand: brand.trim(), start_date: startDate, end_date: endDate, tracking_hashtags: tags });
  }

  const shownError = checkError ?? error;

  return (
    <form onSubmit={handleSubmit} className="flex flex-col gap-4" noValidate>
      {shownError && <Alert>{shownError}</Alert>}
      <TextField label="Campaign name" required autoFocus value={name} onChange={(e) => setName(e.target.value)} />
      <TextField label="Brand" required value={brand} onChange={(e) => setBrand(e.target.value)} />
      <div className="grid gap-4 sm:grid-cols-2">
        <TextField label="Start date" type="date" required value={startDate} onChange={(e) => setStartDate(e.target.value)} />
        <TextField
          label="End date"
          type="date"
          required
          min={startDate}
          value={endDate}
          onChange={(e) => setEndDate(e.target.value)}
        />
      </div>
      <div>
        <TextField
          label="Tracking hashtags"
          required
          placeholder="#LumiGlow #summer24"
          hint="Posts using any of these hashtags count toward this campaign. Separate with spaces or commas."
          value={hashtagText}
          onChange={(e) => setHashtagText(e.target.value)}
        />
        {tags.length > 0 && (
          <ul className="mt-2 flex flex-wrap gap-1.5" aria-label="Hashtags that will be tracked">
            {tags.map((tag) => (
              <li key={tag} className="rounded-full bg-gray-100 px-2 py-0.5 text-xs text-gray-700">
                #{tag}
              </li>
            ))}
          </ul>
        )}
      </div>
      <div className="mt-2 flex flex-col-reverse gap-2 sm:flex-row sm:justify-end">
        <Button type="button" variant="secondary" onClick={onCancel} disabled={pending}>
          Cancel
        </Button>
        <Button type="submit" loading={pending}>
          {submitLabel}
        </Button>
      </div>
    </form>
  );
}
