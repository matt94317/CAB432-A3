import { useState } from "react";
import { Link } from "react-router-dom";
import { type Creator, useCreators } from "@/api/queries/creators";
import Alert from "@/components/ui/Alert";
import Button from "@/components/ui/Button";
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

  const shown = creators.data?.filter((c) => matchesSearch(c, search)) ?? [];

  function openAdd() {
    setEditing(undefined);
    setFormOpen(true);
  }

  return (
    <div className="px-4 py-6 sm:px-6">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold text-gray-900">Creators</h1>
          <p className="mt-1 text-sm text-gray-500">Your roster. Assign creators to campaigns from a campaign's page.</p>
        </div>
        <Button onClick={openAdd}>Add creator</Button>
      </div>

      <div className="mt-6">
        {creators.isPending && <p className="text-sm text-gray-500">Loading creators…</p>}
        {creators.isError && <Alert>{creators.error.message}</Alert>}

        {creators.data?.length === 0 && (
          <div className="rounded-xl border border-dashed border-gray-300 bg-white px-6 py-12 text-center">
            <p className="font-medium text-gray-900">No creators yet</p>
            <p className="mt-1 text-sm text-gray-500">
              Add the creators you work with, then assign them to campaigns with posting targets.
            </p>
            <Button className="mt-4" onClick={openAdd}>
              Add your first creator
            </Button>
          </div>
        )}

        {creators.data && creators.data.length > 0 && (
          <>
            <input
              type="search"
              aria-label="Search creators"
              placeholder="Search by name, handle or niche"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full rounded-lg border border-gray-300 bg-white px-3 py-2.5 text-sm outline-none focus:border-brand focus:ring-2 focus:ring-brand/20 sm:max-w-sm"
            />
            {shown.length === 0 ? (
              <p className="mt-4 text-sm text-gray-500">No creators match “{search.trim()}”.</p>
            ) : (
              <ul className="mt-4 divide-y divide-gray-100 overflow-hidden rounded-xl border border-gray-200 bg-white shadow-sm">
                {shown.map((creator) => (
                  <li key={creator.id} className="flex flex-wrap items-center gap-x-4 gap-y-2 px-4 py-3">
                    <div className="min-w-0 flex-1">
                      <Link
                        to={`/creators/${creator.id}`}
                        className="block truncate font-medium text-gray-900 hover:text-brand"
                      >
                        {creator.name}
                      </Link>
                      <p className="truncate text-sm text-gray-500">
                        @{creator.handle}
                        {creator.niche && ` · ${creator.niche}`}
                      </p>
                    </div>
                    <span className="text-sm text-gray-500">
                      {creator.campaign_count === 1 ? "1 campaign" : `${creator.campaign_count} campaigns`}
                    </span>
                    <div className="flex gap-4">
                      <Button
                        variant="link"
                        onClick={() => {
                          setEditing(creator);
                          setFormOpen(true);
                        }}
                      >
                        Edit
                      </Button>
                      <Button variant="link" className="!text-red-600" onClick={() => setDeleting(creator)}>
                        Remove
                      </Button>
                    </div>
                  </li>
                ))}
              </ul>
            )}
          </>
        )}
      </div>

      <CreatorFormDialog open={formOpen} creator={editing} onClose={() => setFormOpen(false)} />
      <DeleteCreatorDialog creator={deleting} onClose={() => setDeleting(undefined)} />
    </div>
  );
}
