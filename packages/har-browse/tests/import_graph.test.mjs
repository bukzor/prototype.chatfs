/**
 * The production capture path must not carry Playwright: it is a
 * devDependency for the test suite only. Walks the static import graph
 * from the CLI entrypoint and asserts no playwright specifier appears.
 * `host_puppeteer.mjs`'s dynamic `import("playwright-core")` (browser
 * -executable resolution, dev environments) is intentionally out of
 * scope: static declarations are what would make playwright
 * load-bearing middleware.
 */
import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const ENTRY = resolve(__dirname, "..", "src", "har_browse.mjs");

/** @param {string} file @returns {string[]} */
function staticImports(file) {
  const src = readFileSync(file, "utf-8");
  return [
    ...src.matchAll(/^import\s[^;]*?from\s+"([^"]+)"|^import\s+"([^"]+)"/gm),
  ].map((m) => m[1] ?? m[2]);
}

/** @param {string} entry */
function walkBareSpecifiers(entry) {
  const seen = new Set();
  const queue = [entry];
  const bare = new Set();
  while (queue.length) {
    const file = /** @type {string} */ (queue.pop());
    if (seen.has(file)) continue;
    seen.add(file);
    for (const spec of staticImports(file)) {
      if (spec.startsWith(".")) {
        if (spec.endsWith(".mjs")) queue.push(resolve(dirname(file), spec));
      } else if (!spec.startsWith("node:")) {
        bare.add(spec);
      }
    }
  }
  return bare;
}

test("production import graph (har_browse.mjs) is playwright-free", () => {
  const bare = walkBareSpecifiers(ENTRY);
  const playwrightish = [...bare].filter((s) => s.includes("playwright"));
  assert.deepEqual(
    playwrightish,
    [],
    `playwright leaked into the production graph via: ${playwrightish}`,
  );
  // Sanity that the walker still sees real imports at all -- guards the
  // regex against rotting into a vacuous pass.
  assert.ok(
    bare.has("puppeteer-core"),
    `expected puppeteer-core among bare imports, saw: ${[...bare]}`,
  );
});
