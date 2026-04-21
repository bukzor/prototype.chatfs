import assert from "node:assert/strict";
import { homedir } from "node:os";
import { join } from "node:path";
import { mkdirSync } from "node:fs";

const ROOT = join(
  process.env.XDG_CACHE_HOME || join(homedir(), ".cache"),
  "har-browse",
);

/**
 * Absolute path to a directory inside the har-browse XDG cache, ensured
 * to exist. Namespace separates unrelated caches. Key is either:
 *
 *   - a string: used directly as a path segment, or
 *   - an object: hive-style `k=v/` segments in the object's insertion
 *     order
 */
export function cachePath(namespace, key) {
  const segments =
    typeof key === "string"
      ? key
      : Object.entries(key)
          .map(([k, v]) => {
            assert(
              !k.includes("="),
              `cache key may not contain '=': ${JSON.stringify(k)}`,
            );
            assert(
              !k.includes("\0"),
              `cache key may not contain NUL: ${JSON.stringify(k)}`,
            );
            return `${escape(k)}=${escape(v)}`;
          })
          .join("/");
  const path = join(ROOT, namespace, segments);
  mkdirSync(path, { recursive: true });
  return path;
}

// ensure a string is filesystem-path semantic-free
function escape(v) {
  const s = String(v);
  assert(
    !s.includes("\0"),
    `filesystem paths may not contain NUL: ${JSON.stringify(s)}`,
  );
  return s.replaceAll("/", "\\");
}
