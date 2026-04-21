import { readFileSync, writeFileSync, existsSync } from "node:fs";
import { arch, platform } from "node:os";
import { join } from "node:path";
// `registry` gives us the installed Chromium's executablePath and
// revision without having to launch the browser (cachedUserAgent needs
// `revision` in its cache key). Reachable on purpose — this subpath is
// declared in playwright-core's package.json `exports` map.
import { registry } from "playwright-core/lib/server/registry/index";
import pkg from "../package.json" with { type: "json" };
import { cachePath } from "./cache.mjs";

// Self-identifying User-Agent suffix, following the standard
// `ToolName/Version (+ContactURL)` convention, so operators can identify
// this tool's traffic and reach the maintainer.
const SUFFIX = `${pkg.name}/${pkg.version} (+${pkg.homepage})`;

/**
 * Probe the default User-Agent for `browserType` in the given launch mode,
 * by reading CDP's Browser.getVersion on a throwaway browser.
 *
 * @param {import("playwright").BrowserType} browserType
 * @param {boolean} headless  the mode the *calling* context will launch in
 */
export async function fetchUserAgent(browserType, headless) {
  const launchOpts = {
    headless: headless,
    executablePath: registry
      .findExecutable(browserType.name())
      .executablePath(),
  };
  const browser = await browserType.launch(launchOpts);
  try {
    const page = await browser.newPage();
    const session = await page.context().newCDPSession(page);
    const { userAgent } = await session.send("Browser.getVersion");
    return userAgent;
  } finally {
    await browser.close();
  }
}

/**
 * Disk-memoized fetchUserAgent. Returns the raw default UA.
 *
 * @param {import("playwright").BrowserType} browserType
 * @param {boolean} headless  the mode the *calling* context will launch in
 */
export async function cachedUserAgent(browserType, headless) {
  const browser = browserType.name();
  const { revision } = registry.findExecutable(browser);
  const cacheDir = cachePath("browser", {
    browser,
    revision,
    platform: platform(),
    arch: arch(),
    headless: String(headless),
  });
  const cacheFile = join(cacheDir, "user-agent");

  if (existsSync(cacheFile)) {
    return readFileSync(cacheFile, "utf-8").trim();
  }
  const ua = await fetchUserAgent(browserType, headless);
  writeFileSync(cacheFile, ua);
  return ua;
}

/**
 * Return cachedUserAgent with SUFFIX appended, suitable for use as a
 * request-header value.
 *
 * @param {import("playwright").BrowserType} browserType
 * @param {boolean} headless  the mode the *calling* context will launch in
 */
export async function userAgent(browserType, headless) {
  return `${await cachedUserAgent(browserType, headless)} ${SUFFIX}`;
}
