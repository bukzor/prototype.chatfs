// Colocated unit tests for ./cache.mjs.
//
// XDG_CACHE_HOME is set synchronously *before* importing the module so
// the module-level `ROOT` resolves into a per-test temp dir.

import { mkdtempSync, rmSync, existsSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";

const TEST_ROOT = mkdtempSync(join(tmpdir(), "har-browse-cache-test-"));
process.env.XDG_CACHE_HOME = TEST_ROOT;

const { cachePath } = await import("./cache.mjs");

const { after, test } = await import("node:test");
const assert = (await import("node:assert/strict")).default;

after(() => rmSync(TEST_ROOT, { recursive: true, force: true }));

test("cachePath with string key returns ROOT/namespace/key and creates the dir", () => {
  const result = cachePath("ns", "subdir");
  assert.equal(result, join(TEST_ROOT, "har-browse", "ns", "subdir"));
  assert.equal(existsSync(result), true);
});

test("cachePath with hive key joins as k=v segments", () => {
  const result = cachePath("ns", { a: "1", b: "2" });
  assert.equal(result, join(TEST_ROOT, "har-browse", "ns", "a=1", "b=2"));
  assert.equal(existsSync(result), true);
});

test("hive cache-key value with '/' must be escaped so it stays one path segment", () => {
  const result = cachePath("ns-slash", { k: "a/b" });
  // The '/' in the value must NOT be promoted to a path separator;
  // `k=a/b` would create two dirs (`k=a` and `b`) and silently collide
  // with other keys. The escape replaces '/' with '\\'.
  assert.equal(result, join(TEST_ROOT, "har-browse", "ns-slash", "k=a\\b"));
  assert.equal(existsSync(result), true);
});

test("cachePath rejects '=' in hive key (would parse ambiguously)", () => {
  assert.throws(
    () => cachePath("ns-eq", { "a=b": "v" }),
    /cache key may not contain '='/,
  );
});

test("cachePath rejects NUL in hive key", () => {
  assert.throws(
    () => cachePath("ns-nul", { "a\0b": "v" }),
    /cache key may not contain NUL/,
  );
});

test("cachePath rejects NUL in hive value", () => {
  assert.throws(
    () => cachePath("ns-nul-val", { k: "a\0b" }),
    /filesystem paths may not contain NUL/,
  );
});
