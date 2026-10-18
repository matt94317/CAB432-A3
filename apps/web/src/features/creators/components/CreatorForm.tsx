import { type FormEvent, useState } from "react";
import type { Creator, CreatorCreate } from "@/api/queries/creators";
import Alert from "@/components/ui/Alert";
import Button from "@/components/ui/Button";
import TextField from "@/components/ui/TextField";

interface CreatorFormProps {
  creator?: Creator;
  submitLabel: string;
  pending: boolean;
  error?: string | null;
  onSubmit: (values: CreatorCreate) => void;
  onCancel: () => void;
}

// Add/edit creator form (US-07, US-08). Blank optional fields are sent as null so
// editing can clear them.
export default function CreatorForm({ creator, submitLabel, pending, error, onSubmit, onCancel }: CreatorFormProps) {
  const [name, setName] = useState(creator?.name ?? "");
  const [handle, setHandle] = useState(creator ? `@${creator.handle}` : "");
  const [niche, setNiche] = useState(creator?.niche ?? "");
  const [email, setEmail] = useState(creator?.email ?? "");
  const [phone, setPhone] = useState(creator?.phone ?? "");
  const [checkError, setCheckError] = useState<string | null>(null);

  function handleSubmit(event: FormEvent) {
    event.preventDefault();
    if (!name.trim() || !handle.trim()) return setCheckError("Enter the creator's name and TikTok handle.");
    setCheckError(null);
    onSubmit({
      name: name.trim(),
      handle: handle.trim(),
      niche: niche.trim() || null,
      email: email.trim() || null,
      phone: phone.trim() || null,
    });
  }

  const shownError = checkError ?? error;

  return (
    <form onSubmit={handleSubmit} className="flex flex-col gap-4" noValidate>
      {shownError && <Alert>{shownError}</Alert>}
      <TextField label="Name" required autoFocus value={name} onChange={(e) => setName(e.target.value)} />
      <TextField
        label="TikTok handle"
        required
        placeholder="@handle"
        hint="With or without the @. You can also paste their profile link."
        autoCapitalize="none"
        autoCorrect="off"
        spellCheck={false}
        value={handle}
        onChange={(e) => setHandle(e.target.value)}
      />
      <TextField
        label="Niche"
        placeholder="Skincare, fitness, food…"
        maxLength={80}
        value={niche}
        onChange={(e) => setNiche(e.target.value)}
      />
      <div className="grid gap-4 sm:grid-cols-2">
        <TextField label="Email" type="email" autoComplete="off" value={email} onChange={(e) => setEmail(e.target.value)} />
        <TextField label="Phone" type="tel" autoComplete="off" value={phone} onChange={(e) => setPhone(e.target.value)} />
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
