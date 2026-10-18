import type { TargetPeriod } from "@/api/queries/assignments";
import SelectField from "@/components/ui/SelectField";
import TextField from "@/components/ui/TextField";
import { MAX_TARGET_POSTS, TARGET_PERIODS } from "@/lib/targets";

interface TargetFieldsProps {
  posts: string;
  period: TargetPeriod;
  onPostsChange: (posts: string) => void;
  onPeriodChange: (period: TargetPeriod) => void;
  autoFocus?: boolean;
}

// "[3] posts [per week]": the target inputs shared by assigning and editing.
export default function TargetFields({ posts, period, onPostsChange, onPeriodChange, autoFocus }: TargetFieldsProps) {
  return (
    <div className="grid grid-cols-2 gap-3">
      <TextField
        label="Target posts"
        type="number"
        inputMode="numeric"
        min={1}
        max={MAX_TARGET_POSTS}
        required
        autoFocus={autoFocus}
        value={posts}
        onChange={(e) => onPostsChange(e.target.value)}
      />
      <SelectField
        label="Period"
        options={TARGET_PERIODS}
        value={period}
        onChange={(e) => onPeriodChange(e.target.value as TargetPeriod)}
      />
    </div>
  );
}

/** The target as a whole number in range, or null if it isn't valid. */
export function parseTargetPosts(text: string): number | null {
  const posts = Number(text);
  return Number.isInteger(posts) && posts >= 1 && posts <= MAX_TARGET_POSTS ? posts : null;
}

export const TARGET_POSTS_ERROR = `Enter a target between 1 and ${MAX_TARGET_POSTS} posts.`;
