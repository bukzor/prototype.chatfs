// Colocated unit tests for ./user-agent.mjs.
//
// XDG_CACHE_HOME is set synchronously *before* importing the module,
// so cache.mjs's `ROOT` lands inside a per-run temp dir. We then seed
// a known UA at the path cachedUserAgent will look at — no browser
// launch.

import { mkdtempSync, rmSync, writeFileSync, readFileSync, existsSync } from "node:fs";
import { tmpdir, platform, arch } from "node:os";
import { join } from "node:path";
import { after, test } from "node:test";
import assert from "node:assert/strict";

const TEST_ROOT = mkdtempSync(join(tmpdir(), "har-browse-ua-test-"));
process.env.XDG_CACHE_HOME = TEST_ROOT;

const { cachePath } = await import("./cache.mjs");
const { registry } = await import(
  "playwright-core/lib/server/registry/index"
);
const { userAgent } = await import("./user-agent.mjs");
const pkg = JSON.parse(
  readFileSync(new URL("../package.json", import.meta.url), "utf-8"),
);

const SUFFIX = `${pkg.name}/${pkg.version} (+${pkg.homepage})`;
/** @type {import('playwright').BrowserType} */
const fakeChromium = /** @type {any} */ ({ name: () => "chromium" });

after(() => rmSync(TEST_ROOT, { recursive: true, force: true }));

/** Path the production cachedUserAgent will read for these inputs. */
function expectedCacheFile({ headless }) {
  const { revision } = registry.findExecutable("chromium");
  const dir = cachePath("browser", {
    browser: "chromium",
    revision,
    platform: platform(),
    arch: arch(),
    headless: String(headless),
  });
  return join(dir, "user-agent");
}

test("userAgent appends `<name>/<version> (+<homepage>)` SUFFIX to the cached UA", async () => {
  writeFileSync(expectedCacheFile({ headless: true }), "MockChrome/1.0");
  const ua = await userAgent(fakeChromium, true);
  assert.equal(ua, `MockChrome/1.0 ${SUFFIX}`);
});

test("cachedUserAgent cache key includes Chromium revision", async () => {
  // Seed at the path keyed with the CURRENT revision. If user-agent.mjs
  // drops `revision` from its cache key, lookup will land at a DIFFERENT
  // path (missing the `revision=...` segment) — cache miss, then a real
  // browser launch which we don't want. Use a UA distinct from any
  // possible real Chromium UA so equality is decisive.
  writeFileSync(
    expectedCacheFile({ headless: false }),
    "SeededByRevisionTest/9.9",
  );
  const ua = await userAgent(fakeChromium, false);
  assert.equal(ua, `SeededByRevisionTest/9.9 ${SUFFIX}`);

  // Sanity: cache file the production code reads from is the same one
  // we wrote to. If the cache key drops a hive entry, the lookup path
  // is shorter — confirm presence of the `revision=` segment.
  const path = expectedCacheFile({ headless: false });
  assert.ok(path.includes("revision="), `expected revision in path: ${path}`);
  assert.equal(existsSync(path), true);
});

test("cachedUserAgent cache key includes headless mode", async () => {
  // Distinct seeds at headless=true vs headless=false. If the key drops
  // `headless`, both reads land at the same file and the second value
  // wins — both calls would return the same UA.
  writeFileSync(expectedCacheFile({ headless: true }), "HeadlessSeed/1.0");
  writeFileSync(expectedCacheFile({ headless: false }), "HeadfulSeed/1.0");
  const uaHeadless = await userAgent(fakeChromium, true);
  const uaHeadful = await userAgent(fakeChromium, false);
  assert.equal(uaHeadless, `HeadlessSeed/1.0 ${SUFFIX}`);
  assert.equal(uaHeadful, `HeadfulSeed/1.0 ${SUFFIX}`);
});
