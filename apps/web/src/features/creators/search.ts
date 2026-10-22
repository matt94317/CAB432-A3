import type { Creator } from "@/api/queries/creators";

// Same matching as the API's ?search=: name, handle or niche, case-insensitive.
export function matchesSearch(creator: Pick<Creator, "name" | "handle" | "niche">, search: string): boolean {
  const needle = search.trim().replace(/^@/, "").toLowerCase();
  if (!needle) return true;
  return (
    creator.name.toLowerCase().includes(needle) ||
    creator.handle.includes(needle) ||
    (creator.niche?.toLowerCase().includes(needle) ?? false)
  );
}
