// Mirrors the API's normalisation: "#LumiGlow, summer24" -> ["lumiglow", "summer24"].
// The API is still the source of truth; this is for the live preview and quick checks.

const VALID = /^[\p{L}\p{N}_]{1,100}$/u;

export function parseHashtags(text: string): { tags: string[]; invalid: string[] } {
  const tags = new Set<string>();
  const invalid: string[] = [];
  for (const raw of text.split(/[\s,]+/)) {
    const tag = raw.replace(/^#+/, "").toLowerCase();
    if (!tag) continue;
    if (VALID.test(tag)) tags.add(tag);
    else invalid.push(raw);
  }
  return { tags: [...tags], invalid };
}

export function formatHashtags(tags: string[]): string {
  return tags.map((tag) => `#${tag}`).join(" ");
}
