import type { Post } from "@/api/queries/posts";
import Badge from "@/components/ui/Badge";
import Button from "@/components/ui/Button";
import { formatCount, formatDateTime, formatExact } from "@/lib/format";

interface PostTableProps {
  posts: Post[];
  editable: boolean;
  /** What to show as each post's link text; defaults to the creator's @handle. */
  label?: (post: Post) => string;
  onMove: (post: Post) => void;
  onRemove: (post: Post) => void;
}

const METRICS = [
  { key: "views", label: "Views" },
  { key: "likes", label: "Likes" },
  { key: "comments", label: "Comments" },
  { key: "shares", label: "Shares" },
] as const;

// Posts with views, likes, comments and shares (US-17). Scrolls sideways on small screens.
export default function PostTable({ posts, editable, label, onMove, onRemove }: PostTableProps) {
  return (
    <div className="overflow-x-auto rounded-xl border border-gray-200 bg-white shadow-sm">
      <table className="w-full min-w-[40rem] text-left text-sm">
        <thead className="border-b border-gray-200 bg-gray-50 text-xs font-medium text-gray-500">
          <tr>
            <th scope="col" className="px-4 py-2.5">
              Post
            </th>
            {METRICS.map((m) => (
              <th key={m.key} scope="col" className="px-3 py-2.5 text-right">
                {m.label}
              </th>
            ))}
            {editable && (
              <th scope="col" className="px-4 py-2.5">
                <span className="sr-only">Actions</span>
              </th>
            )}
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-100">
          {posts.map((post) => (
            <tr key={post.id} className="align-top">
              <td className="max-w-xs px-4 py-3">
                <div className="flex flex-wrap items-center gap-2">
                  <a
                    href={post.url}
                    target="_blank"
                    rel="noreferrer"
                    className="font-medium text-gray-900 hover:text-brand"
                  >
                    {label ? label(post) : `@${post.creator.handle}`}
                  </a>
                  {post.match_source === "manual" && <Badge>Manual</Badge>}
                </div>
                <p className="mt-0.5 text-xs text-gray-500">
                  {formatDateTime(post.posted_at)}
                  {post.last_synced_at === null && " · not synced"}
                </p>
                {post.caption && (
                  <p className="mt-1 line-clamp-2 text-xs text-gray-600" title={post.caption}>
                    {post.caption}
                  </p>
                )}
              </td>
              {METRICS.map((m) => (
                <td
                  key={m.key}
                  className="px-3 py-3 text-right tabular-nums text-gray-900"
                  title={formatExact(post[m.key])}
                >
                  {formatCount(post[m.key])}
                </td>
              ))}
              {editable && (
                <td className="whitespace-nowrap px-4 py-3 text-right">
                  <Button variant="link" onClick={() => onMove(post)}>
                    Move
                  </Button>
                  <Button variant="link" className="ml-3 !text-red-600" onClick={() => onRemove(post)}>
                    Remove
                  </Button>
                </td>
              )}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
