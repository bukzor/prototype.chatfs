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
import { startCapture } from "../src/host_puppeteer.mjs";
import { cachePath } from "../src/cache.mjs";
import { rmSync } from "node:fs";

test("captured requests carry client hints and a branded User-Agent", async ({
  payloadServer,
}) => {
  test.setTimeout(60_000);

  const profileDir = cachePath("profile", `ua-hints-test-${process.pid}`);
  /** @type {import("../src/capture.mjs").CDPEvent[]} */
  const messages = [];
  try {
    const session = await startCapture({
      url: `${payloadServer.url}/`,
      profileDir,
      headless: true,
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

  for (const { params } of wire) {
    const hints = Object.keys(params.headers).filter((h) =>
      h.toLowerCase().startsWith("sec-ch-ua"),
    );
    expect(hints.sort(), "every request carries the default client hints").toEqual([
      "sec-ch-ua",
      "sec-ch-ua-mobile",
      "sec-ch-ua-platform",
    ]);
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
  // aistudio gate refuses -- measured, not guessed (sbin/ua-gate-probe.mjs
  // and the header comment on brandUserAgent). Identification lives in
  // the platform comment precisely so this stays true.
  expect(userAgent, "nothing trails the browser's product list").toMatch(
    /Safari\/[\d.]+$/,
  );
});
