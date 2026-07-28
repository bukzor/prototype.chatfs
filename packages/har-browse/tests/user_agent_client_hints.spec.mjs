/**
 * A captured request carries the browser's `Sec-CH-UA*` headers, and
 * the UA carries the tool-identifying suffix. Both at once is the
 * point: they are in tension, and the naive way to get the second
 * destroys the first.
 *
 * `Network.setUserAgentOverride` with no `userAgentMetadata` makes
 * Chromium send *no* client hints at all. Puppeteer's network manager
 * issues exactly that call to every session it attaches, unbidden, so
 * the stripping predates any branding we do (hence
 * `networkEnabled: false` in the host, plus an override carrying
 * metadata read from the browser itself).
 *
 * A UA string claiming Chrome with zero client hints is a combination
 * no real browser produces -- an `unblocked-sessions` violation, and
 * verified live to draw a bot-detection denial from Google's
 * attestation. It is also a capture-fidelity defect in its own right:
 * the recorded requests lack headers the live app sends.
 *
 * `requestWillBeSentExtraInfo` is the oracle, not `requestWillBeSent`:
 * the latter carries renderer-provisional headers, the former what
 * actually went onto the wire. Loopback is a secure context, so the
 * fixture server sees the same hints a real site would.
 */
import { test, expect } from "./fixtures.mjs";
import { startCapture, WINDOWLESS_ARGS } from "../src/host_puppeteer.mjs";
import { cachePath } from "../src/cache.mjs";
// `playwright-core` only for the pinned browser's path -- the same
// lookup `host_puppeteer.mjs` does, not a Playwright launch.
import { chromium } from "playwright-core";
import puppeteer from "puppeteer-core";
import { mkdtempSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import pkg from "../package.json" with { type: "json" };

/**
 * Parse a `Sec-CH-UA`-style structured header into its entries.
 * Deliberately strict -- a mangled list should fail here rather than
 * silently reduce to fewer entries.
 *
 * @param {string} header
 * @returns {Array<{brand: string, version: string}>}
 */
function parseBrandList(header) {
  return header.split(", ").map((entry) => {
    const m = /^"(.*)";v="(.*)"$/.exec(entry);
    if (!m) throw new Error(`unparseable brand entry: ${JSON.stringify(entry)}`);
    return { brand: m[1], version: m[2] };
  });
}

/**
 * The browser's own brand list, read from a browser we have not
 * touched. An independent oracle on purpose: deriving the expectation
 * from `userAgentMetadata()` would make the assertion circular, and
 * hard-coding it would fail on every Chromium bump for no reason.
 *
 * It must be the *same* browser the host launches, which is why it
 * borrows the host's own `WINDOWLESS_ARGS` rather than approximating
 * them. Chromium's `--headless` is what makes this easy to get wrong:
 * Playwright in that mode runs a different executable entirely
 * (`chromium_headless_shell`, betrayed by its un-reduced version) and
 * reports a three-entry list led by `"HeadlessChrome"`. Our windowless
 * mode is a display backend, not that mode, and agrees with headful on
 * every property here.
 *
 * @returns {Promise<Array<{brand: string, version: string}>>}
 */
async function unbrandedBrands() {
  const dir = mkdtempSync(join(tmpdir(), "ua-oracle-"));
  const browser = await puppeteer.launch({
    executablePath: process.env.HAR_BROWSE_BROWSER ?? chromium.executablePath(),
    userDataDir: dir,
    headless: false,
    networkEnabled: false,
    args: WINDOWLESS_ARGS,
  });
  try {
    const page = await browser.newPage();
    // Secure context required; `file:` is one and costs no server.
    await page.goto("file:");
    return await page.evaluate(
      () => /** @type {any} */ (navigator).userAgentData.brands,
    );
  } finally {
    await browser.close();
    rmSync(dir, { recursive: true, force: true });
  }
}

test("captured requests carry client hints and a branded User-Agent", async ({
  payloadServer,
}) => {
  test.setTimeout(60_000);

  const browserBrands = await unbrandedBrands();
  const profileDir = cachePath("profile", `ua-hints-test-${process.pid}`);
  /** @type {import("../src/capture.mjs").CDPEvent[]} */
  const messages = [];
  try {
    const session = await startCapture({
      url: `${payloadServer.url}/client-hints`,
      profileDir,
      windowless: true,
    });
    const collected = (async () => {
      for await (const message of session.events) messages.push(message);
    })();
    await session.page.waitForFunction(
      () => document.getElementById("capture-done") !== null,
    );
    await session.close();
    await collected;
  } finally {
    rmSync(profileDir, { recursive: true, force: true });
  }

  const wire = messages.filter(
    (m) => m.method === "Network.requestWillBeSentExtraInfo",
  );
  expect(wire.length, "the capture recorded on-the-wire headers").toBeGreaterThan(0);

  /** @type {Array<Record<string, string>>} */
  const wireHeaders = wire.map(({ params }) =>
    Object.fromEntries(
      Object.entries(params.headers).map(([h, v]) => [h.toLowerCase(), String(v)]),
    ),
  );

  for (const headers of wireHeaders) {
    // Exact, in both regimes: the three low-entropy hints always, plus
    // the full-version list on requests that follow the `Accept-CH`
    // negotiation and nothing else either way.
    const hints = Object.keys(headers).filter((h) => h.startsWith("sec-ch-ua")).sort();
    const negotiated = hints.includes("sec-ch-ua-full-version-list");
    expect(hints, "exactly the hints we expect, no more").toEqual(
      negotiated
        ? ["sec-ch-ua", "sec-ch-ua-full-version-list", "sec-ch-ua-mobile", "sec-ch-ua-platform"]
        : ["sec-ch-ua", "sec-ch-ua-mobile", "sec-ch-ua-platform"],
    );

    // The brand list is the only disclosure a client-hints-only site can
    // see -- the UA's comment is invisible to it. Assert the parsed
    // list, not a substring: what matters is that we added exactly one
    // entry, at the end, and left the browser's own list intact ahead of
    // it. A `toContain` passes just as happily on a list we mangled.
    const brands = parseBrandList(headers["sec-ch-ua"]);
    expect(brands.at(-1), "our brand is appended, major version only").toEqual({
      brand: "har-browse",
      version: "1",
    });
    expect(
      brands.filter((b) => b.brand === "har-browse"),
      "exactly once",
    ).toHaveLength(1);
    expect(
      brands.slice(0, -1),
      "the browser's own brands survive ahead of ours",
    ).toEqual(browserBrands);
    expect(
      browserBrands.map((b) => b.brand),
      "including the real engine -- we added, not replaced",
    ).toContain("Chromium");
  }

  // `Sec-CH-UA-Full-Version-List` is only sent where a site negotiated
  // it, which `/client-hints` does. The two lists must agree: a token in
  // one and not the other is an inconsistency more conspicuous than the
  // disclosure it carries.
  const negotiatedRequests = wireHeaders.filter(
    (h) => h["sec-ch-ua-full-version-list"],
  );
  expect(
    negotiatedRequests.length,
    "the Accept-CH negotiation produced a full-version list",
  ).toBeGreaterThan(0);
  for (const headers of negotiatedRequests) {
    const full = parseBrandList(headers["sec-ch-ua-full-version-list"]);
    expect(full.at(-1), "the full list carries our exact version").toEqual({
      brand: "har-browse",
      version: pkg.version,
    });
    expect(
      full.map((b) => b.brand),
      "and names the same brands, in the same order, as the short list",
    ).toEqual(parseBrandList(headers["sec-ch-ua"]).map((b) => b.brand));
  }

  const userAgents = new Set(
    messages
      .filter((m) => m.method === "Network.requestWillBeSent")
      .map((m) => m.params.request.headers["User-Agent"])
      .filter(Boolean),
  );
  expect(userAgents.size, "one UA across the capture").toBe(1);
  const userAgent = [...userAgents][0];
  expect(userAgent, "the UA identifies the tool and how to reach us").toMatch(
    /har-browse\/\d[\d.]*; \+https?:\/\//,
  );
  // Anything trailing the browser's last product is what Google's
  // aistudio gate refuses -- measured, not guessed (design.kb/040-design.kb/self-identification.kb/
  // and the header comment on brandUserAgent). Identification lives in
  // the platform comment precisely so this stays true.
  expect(userAgent, "nothing trails the browser's product list").toMatch(
    /Safari\/[\d.]+$/,
  );
  // The capture is headful by construction, so this can be exact.
  // While `--headless` existed the suite ran headless and this
  // assertion had to tolerate `HeadlessChrome/` -- meaning the suite
  // validated a User-Agent that would have drawn a challenge in
  // production, and could not have caught one that did.
  expect(userAgent, "announces a real browser, not an automated one").toMatch(
    / Chrome\/[\d.]+ Safari/,
  );
  expect(userAgent, "and says nothing about being headless").not.toContain(
    "Headless",
  );
});
