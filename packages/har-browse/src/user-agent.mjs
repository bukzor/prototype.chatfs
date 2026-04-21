import { chromium } from "playwright";
import { readFileSync, writeFileSync, existsSync } from "node:fs";
import { arch, platform } from "node:os";
import pkg from "../package.json" with { type: "json" };
import { cachePath, hashKey } from "./cache.mjs";

// Tool-identifying suffix appended to every request. Lets a site operator
// distinguish this tool's traffic in their logs and reach the maintainer
// via the repo URL — an honesty layer alongside the blink-features flag
// in capture.mjs.
const SUFFIX = `${pkg.name}/${pkg.version} (+${pkg.homepage})`;

/**
 * Return the User-Agent string to pass to launchPersistentContext:
 * the browser's default UA with the tool-identifying SUFFIX appended.
 *
 * Caches the default UA keyed by (chromium binary, platform, arch) so
 * only the first run per Playwright install pays the extra-browser-launch
 * cost. Playwright upgrades change the binary path → fresh cache entry.
 */
export async function userAgent() {
  const key = hashKey({
    bin: chromium.executablePath(),
    platform: platform(),
    arch: arch(),
  });
  const cacheFile = cachePath("user-agent", key);

  const defaultUA = existsSync(cacheFile)
    ? readFileSync(cacheFile, "utf-8").trim()
    : await fetchAndCache(cacheFile);

  return `${defaultUA} ${SUFFIX}`;
}

async function fetchAndCache(cacheFile) {
  const browser = await chromium.launch({ headless: true });
  try {
    const page = await browser.newPage();
    const session = await page.context().newCDPSession(page);
    const { userAgent } = await session.send("Browser.getVersion");
    writeFileSync(cacheFile, userAgent);
    return userAgent;
  } finally {
    await browser.close();
  }
}
