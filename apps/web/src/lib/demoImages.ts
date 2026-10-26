// Demo photos for demo data (scripts/seed.py with TIKTOK_MODE=mock), so people and
// campaigns look like the design. Hookd stores no images, and a real creator must
// never get a stranger's face, so this is off unless built with VITE_DEMO_IMAGES=true.
// Photos are the Hookd Figma design's demo photography, named after who or what
// they show there.

const enabled = import.meta.env.VITE_DEMO_IMAGES === "true";

const byName = (files: Record<string, string>) =>
  Object.fromEntries(Object.entries(files).map(([path, url]) => [path.split("/").pop()!.replace(".jpg", ""), url]));

const avatars = byName(
  import.meta.glob<string>("../assets/demo/avatars/*.jpg", { eager: true, query: "?url", import: "default" }),
);
const covers = byName(
  import.meta.glob<string>("../assets/demo/covers/*.jpg", { eager: true, query: "?url", import: "default" }),
);

// The seeded demo people and brands get a photo that fits; anyone else a stable pick
const AVATAR_FOR: Record<string, string> = {
  avamakesthings: "sofia-rivera",
  liamlifts: "move-your-own-way-runner",
  priyaeats: "morning-ritual-creator",
  jordanblakeugc: "james-wilson",
  "mia.rossi": "ella-brooks",
  noahstudies: "leo-chen-desk",
  zarastyles: "maya-johnson",
  "ethanpark.tech": "leo-chen",
  "demo@hookd.test": "avery-morgan",
  "load@hookd.test": "avery-morgan",
};
const COVER_FOR: Record<string, string> = {
  "lumi skin": "everyday-elevated",
  "stride co": "move-your-own-way",
  notely: "laptop-creator",
  blendr: "morning-ritual-creator",
  "bean there": "the-morning-ritual",
  "hookd load test": "slow-living-stories",
};

function pick(pool: Record<string, string>, key: string): string {
  const urls = Object.entries(pool)
    .filter(([name]) => name !== "avery-morgan")
    .map(([, url]) => url);
  let hash = 0;
  for (const char of key) hash = (hash * 31 + char.charCodeAt(0)) | 0;
  return urls[Math.abs(hash) % urls.length];
}

/** A photo for a creator (by handle) or the signed-in manager (by email). */
export function demoAvatar(key: string): string | undefined {
  if (!enabled) return undefined;
  return avatars[AVATAR_FOR[key]] ?? pick(avatars, key);
}

/** A cover photo for a campaign: by brand for the seeded ones, else by campaign id. */
export function demoCover(brand: string, campaignId: string): string | undefined {
  if (!enabled) return undefined;
  return covers[COVER_FOR[brand.toLowerCase()]] ?? pick(covers, campaignId);
}
