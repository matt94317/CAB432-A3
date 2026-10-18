import { useState } from "react";
import { type Creator, useCreators } from "@/api/queries/creators";
import Alert from "@/components/ui/Alert";
import Button from "@/components/ui/Button";
import PageHeader from "@/components/ui/PageHeader";
import SearchField from "@/components/ui/SearchField";
import StatCard from "@/components/ui/StatCard";
import CreatorCard from "../components/CreatorCard";
import CreatorFormDialog from "../components/CreatorFormDialog";
import DeleteCreatorDialog from "../components/DeleteCreatorDialog";
import { matchesSearch } from "../search";

// Creator roster: add, edit, remove and search (US-07, US-08).
export default function CreatorListPage() {
  const creators = useCreators();
  const [search, setSearch] = useState("");
  const [formOpen, setFormOpen] = useState(false);
  const [editing, setEditing] = useState<Creator | undefined>();
  const [deleting, setDeleting] = useState<Creator | undefined>();

  const all = creators.data ?? [];
  const shown = all.filter((c) => matchesSearch(c, search));
  const assigned = all.filter((c) => c.campaign_count > 0).length;
  const niches = new Set(all.map((c) => c.niche?.toLowerCase()).filter(Boolean)).size;

  function openAdd() {
    setEditing(undefined);
    setFormOpen(true);
  }

  return (
    <div className="flex flex-col gap-[26px]">
      <PageHeader
        title="Your creator community"
        description="Good people make great content. Assign creators to campaigns from a campaign's page."
        actions={
          <Button icon="plus" onClick={openAdd}>
            Add creator
          </Button>
        }
      />

      {all.length > 0 && (
        <div className="grid grid-cols-2 gap-6 rounded-card border border-line bg-surface p-[22px] lg:grid-cols-4">
          <StatCard variant="inline" label="Creators" value={all.length} note="In your roster" />
          <StatCard variant="inline" label="On a campaign" value={assigned} note="Assigned at least once" />
          <StatCard variant="inline" label="Free to assign" value={all.length - assigned} note="Not on any campaign" />
          <StatCard variant="inline" label="Niches" value={niches} note="Across your roster" />
        </div>
      )}

      <div className="flex flex-col gap-5">
        {creators.isPending && <p className="text-[13px] text-ink-muted">Loading creators…</p>}
        {creators.isError && <Alert>{creators.error.message}</Alert>}

        {creators.data?.length === 0 && (
          <div className="rounded-card border border-dashed border-line-strong bg-surface px-6 py-12 text-center">
            <p className="font-medium text-ink">No creators yet</p>
            <p className="mt-1 text-[13px] text-ink-muted">
              Add the creators you work with, then assign them to campaigns with posting targets.
            </p>
            <Button className="mt-4" icon="plus" onClick={openAdd}>
              Add your first creator
            </Button>
          </div>
        )}

        {all.length > 0 && (
          <>
            <SearchField
              label="Search creators"
              placeholder="Search by name, handle or niche..."
              value={search}
              onChange={setSearch}
            />
            {shown.length === 0 ? (
              <p className="text-[13px] text-ink-muted">No creators match “{search.trim()}”.</p>
            ) : (
              <>
                <ul className="grid gap-5 sm:grid-cols-2 xl:grid-cols-3">
                  {shown.map((creator) => (
                    <CreatorCard
                      key={creator.id}
                      creator={creator}
                      onEdit={() => {
                        setEditing(creator);
                        setFormOpen(true);
                      }}
                      onRemove={() => setDeleting(creator)}
                    />
                  ))}
                </ul>
                <p className="text-xs text-ink-muted">
                  Showing {shown.length} of {all.length} creators
                </p>
              </>
            )}
          </>
        )}
      </div>

      <CreatorFormDialog open={formOpen} creator={editing} onClose={() => setFormOpen(false)} />
      <DeleteCreatorDialog creator={deleting} onClose={() => setDeleting(undefined)} />
    </div>
  );
}
