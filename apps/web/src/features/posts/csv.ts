import type { Post } from "@/api/queries/posts";

// Export posts as a CSV file the browser downloads.
const COLUMNS: [header: string, value: (post: Post, campaign: string) => string | number][] = [
  ["Posted", (p) => p.posted_at],
  ["Creator", (p) => p.creator.name],
  ["Handle", (p) => `@${p.creator.handle}`],
  ["Campaign", (_, campaign) => campaign],
  ["Caption", (p) => p.caption],
  ["Views", (p) => p.views],
  ["Likes", (p) => p.likes],
  ["Comments", (p) => p.comments],
  ["Shares", (p) => p.shares],
  ["Source", (p) => (p.match_source === "manual" ? "Added manually" : "Matched by hashtag")],
  ["Link", (p) => p.url],
];

function cell(value: string | number): string {
  const text = String(value);
  return /[",\n]/.test(text) ? `"${text.replaceAll('"', '""')}"` : text;
}

export function downloadPostsCsv(posts: Post[], campaignName: (post: Post) => string, filename: string) {
  const rows = [
    COLUMNS.map(([header]) => header).join(","),
    ...posts.map((post) => COLUMNS.map(([, value]) => cell(value(post, campaignName(post)))).join(",")),
  ];
  const url = URL.createObjectURL(new Blob([rows.join("\n")], { type: "text/csv;charset=utf-8" }));
  const link = Object.assign(document.createElement("a"), { href: url, download: filename });
  link.click();
  URL.revokeObjectURL(url);
}
