import { createHash } from "node:crypto";
import { homedir } from "node:os";
import { join, dirname } from "node:path";
import { mkdirSync } from "node:fs";

const ROOT = join(
  process.env.XDG_CACHE_HOME || join(homedir(), ".cache"),
  "har-browse",
);

/**
 * Absolute path inside the har-browse XDG cache root. Ensures the parent
 * directory exists. Namespace separates unrelated caches (user-agent
 * strings, persistent profiles, etc.).
 */
export function cachePath(namespace, key) {
  const path = join(ROOT, namespace, key);
  mkdirSync(dirname(path), { recursive: true });
  return path;
}

/** Stable, filesystem-safe key from any JSON-serializable input. */
export function hashKey(obj) {
  return createHash("sha256")
    .update(JSON.stringify(obj))
    .digest("hex")
    .slice(0, 16);
}
