import { useEffect, useState } from "react";
import type { Assignment } from "@/api/queries/assignments";
import { formatDateTime, formatRelative } from "@/lib/format";

// Shows when data was last synced (US-18). A campaign is only as fresh as its
// least recently synced creator, so that's the time shown.
export default function LastSyncedBadge({ assignments }: { assignments: Assignment[] }) {
  const now = useNow();
  if (assignments.length === 0) return null;

  const times = assignments.map((a) => a.creator.last_synced_at);
  const synced = times.filter((t): t is string => t !== null).sort();
  const neverSynced = times.length - synced.length;

  if (synced.length === 0) return <span className="text-sm text-gray-500">Not synced yet</span>;

  const oldest = synced[0];
  return (
    <span className="text-sm text-gray-500" title={`Oldest sync: ${formatDateTime(oldest)}`}>
      Synced {formatRelative(oldest, now)}
      {neverSynced > 0 && ` · ${neverSynced} not synced yet`}
    </span>
  );
}

// Re-render every minute so "5 minutes ago" stays true
function useNow(): Date {
  const [now, setNow] = useState(() => new Date());
  useEffect(() => {
    const id = setInterval(() => setNow(new Date()), 60_000);
    return () => clearInterval(id);
  }, []);
  return now;
}
