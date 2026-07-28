/**
 * The `har-browse` CLI clears origin storage by default, and
 * `--keep-origin-storage` opts out. This is a policy decision, not an
 * implementation detail: without the default, a capture of a provider
 * that hydrates from its own persisted cache is silently empty of the
 * payload it was taken for (verified live against claude.ai
 * 2026-07-26, devlog 2026-07-26-002).
 *
 * The oracle is the fixture server's requestLog -- whether the payload
 * fetch actually happened -- so the CLI's stdout is irrelevant here and
 * the runs are killed on a timer rather than by a human clicking Done.
 */
import { execFile } from "node:child_process";
import { rmSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { test, expect } from "./fixtures.mjs";
import { cachePath } from "../src/cache.mjs";
import { startCapture } from "../src/host_playwright.mjs";

const __dirname = dirname(fileURLToPath(import.meta.url));
const CLI = join(__dirname, "..", "src", "har_browse.mjs");

/**
 * Run the CLI against `url` until a timer kills it. `--headless` here
 * is the CLI's windowless mode -- a display backend, not Chromium's
 * headless *mode*, which would rewrite the User-Agent. It is also the
 * only way this test can work: without a surface there is no Done
 * button, so the run ends exactly when the timer kills it.
 *
 * @param {string[]} args
 */
function runCli(args) {
  return new Promise((resolve) => {
    execFile("timeout", ["-s", "TERM", "15s", "node", CLI, "--headless", ...args], () =>
      resolve(undefined),
    );
  });
}

/** @param {{requestLog: Array<{pathname: string, search: string}>}} server */
const hydrateFetches = (server) =>
  server.requestLog.filter((r) => r.search.includes("id=hydrate")).length;

test("CLI clears origin storage by default; --keep-origin-storage opts out", async ({
  payloadServer,
}) => {
  test.setTimeout(90_000);

  const profileName = `cli-clear-default-test-${process.pid}`;
  const profileDir = cachePath("profile", profileName);
  const url = `${payloadServer.url}/hydrate`;

  try {
    // Populate the profile's IndexedDB via the library (explicitly not
    // clearing) so the CLI runs below start from the hydrating state
    // that makes this test meaningful. This is the Playwright host, so
    // `headless` here is Chromium's mode -- fine, because all this run
    // has to do is leave bytes in IndexedDB, and nothing downstream
    // reads the User-Agent it used.
    const seed = await startCapture({ url, profileDir, headless: true });
    await seed.page.waitForFunction(
      () =>
        /^(fetched|hydrated):/.test(
          document.getElementById("content")?.textContent ?? "",
        ),
      null,
      { timeout: 15_000 },
    );
    await seed.close();
    expect(hydrateFetches(payloadServer), "seed run fetched the payload").toBe(1);

    await runCli(["--profile", profileName, "--keep-origin-storage", url]);
    expect(
      hydrateFetches(payloadServer),
      "--keep-origin-storage leaves the cache alone, so the page hydrates and never refetches",
    ).toBe(1);

    await runCli(["--profile", profileName, url]);
    expect(
      hydrateFetches(payloadServer),
      "the bare CLI clears storage, forcing the payload back onto the network",
    ).toBe(2);
  } finally {
    rmSync(profileDir, { recursive: true, force: true });
  }
});
