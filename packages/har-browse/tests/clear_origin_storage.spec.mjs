/**
 * `startCapture({ clearOriginStorage: true })` must wipe the target
 * origin's app-level storage (IndexedDB + Cache Storage) *before*
 * navigation, so an app that persisted its data cache is forced to
 * re-materialize it as capturable network traffic — while leaving
 * cookies (login state) intact.
 *
 * Live failure mode this models: claude.ai revisits hydrate the
 * conversation from a persisted React Query IndexedDB cache and make
 * zero conversation requests, so the capture is silently empty of
 * payload. See .claude/todo.kb/2026-07-22-001-*.md.
 *
 * The /hydrate fixture (tests/_common/server.mjs) is the miniature:
 * first load fetches /payload?id=hydrate and stores it in IndexedDB;
 * later loads render from the store without fetching.
 */
import { test, expect } from "./fixtures.mjs";
import { startServer } from "./_common/server.mjs";
import { drainMessages, findRR, decodeRRBody } from "./_common/testing.mjs";

/** @param {import("./_common/testing.mjs").CDPMessage[]} messages */
const payloadRWBS = (messages) =>
  messages.filter(
    (m) =>
      m.method === "Network.requestWillBeSent" &&
      (m.params?.request?.url ?? "").includes("id=hydrate"),
  );

/**
 * Which path the /hydrate fixture took on this load: "fetched" (no
 * usable IndexedDB entry) or "hydrated" (rendered from the store).
 *
 * @param {import("playwright").Page} page
 * @returns {Promise<string | undefined>}
 */
async function settledHow(page) {
  await page.waitForFunction(
    () =>
      /^(fetched|hydrated):/.test(
        document.getElementById("content")?.textContent ?? "",
      ),
    null,
    { timeout: 10_000 },
  );
  return page.evaluate(
    () => document.getElementById("content")?.textContent?.split(":")[0],
  );
}

/**
 * Run one capture of /hydrate to completion: wait for the page to
 * settle into "fetched:" or "hydrated:", click Done, drain, close (so
 * the next capture can reopen the same persistent profile).
 *
 * @param {import("./fixtures.mjs").CaptureSession} session
 * @param {"fetched" | "hydrated"} expectedHow
 */
async function runToDone(session, expectedHow) {
  expect(await settledHow(session.page), "fixture took the expected path").toBe(
    expectedHow,
  );
  await session.page.click("#capture-done");
  const messages = await drainMessages(session);
  await session.close();
  return messages;
}

test("fixture control: revisit hydrates from IndexedDB with zero payload traffic", async ({
  startCapture,
  payloadServer,
}, testInfo) => {
  const profileDir = testInfo.outputPath("profile");
  const url = `${payloadServer.url}/hydrate`;

  const first = await startCapture({ url, profileDir });
  const firstMessages = await runToDone(first, "fetched");
  expect(payloadRWBS(firstMessages).length, "first visit fetches").toBe(1);

  const second = await startCapture({ url, profileDir });
  const secondMessages = await runToDone(second, "hydrated");
  expect(
    payloadRWBS(secondMessages).length,
    "revisit makes no payload request — the claude.ai zero-events regime",
  ).toBe(0);
});

test("clearOriginStorage forces a revisit to refetch; payload body is captured", async ({
  startCapture,
  payloadServer,
}, testInfo) => {
  const profileDir = testInfo.outputPath("profile");
  const url = `${payloadServer.url}/hydrate`;

  const first = await startCapture({ url, profileDir });
  await runToDone(first, "fetched");

  const second = await startCapture({ url, profileDir, clearOriginStorage: true });
  const secondMessages = await runToDone(second, "fetched");

  expect(
    payloadRWBS(secondMessages).length,
    "storage cleared pre-goto, so the revisit fetches",
  ).toBe(1);
  const rr = findRR(secondMessages, "id=hydrate");
  expect(rr, "payload response captured on revisit").toBeTruthy();
  const body = JSON.parse(/** @type {string} */ (decodeRRBody(/** @type {any} */ (rr))));
  expect(body.id).toBe("hydrate");
});

test("clearOriginStorage is scoped to the target origin", async ({
  startCapture,
  payloadServer,
}, testInfo) => {
  // Deriving the origin from the live page instead of the target URL
  // is not the harmless no-op it looks like: pre-goto the page sits on
  // about:blank, whose origin serializes to "null", and CDP answers a
  // "null" origin by clearing IndexedDB for *every* origin in the
  // profile. Only a bystander-origin check catches that.
  const bystander = await startServer();
  try {
    const profileDir = testInfo.outputPath("profile");
    const url = `${payloadServer.url}/hydrate`;
    const bystanderUrl = `http://127.0.0.1:${bystander.port}/hydrate`;

    const first = await startCapture({ url, profileDir });
    expect(await settledHow(first.page), "target origin fetches").toBe("fetched");
    await first.page.goto(bystanderUrl);
    expect(await settledHow(first.page), "bystander origin fetches").toBe(
      "fetched",
    );
    await first.page.click("#capture-done");
    await drainMessages(first);
    await first.close();

    const second = await startCapture({ url, profileDir, clearOriginStorage: true });
    expect(await settledHow(second.page), "target origin was cleared").toBe(
      "fetched",
    );
    await second.page.goto(bystanderUrl);
    expect(
      await settledHow(second.page),
      "bystander origin's storage survives",
    ).toBe("hydrated");
  } finally {
    await bystander.close();
  }
});

test("clearOriginStorage preserves cookies (login state)", async ({
  startCapture,
  payloadServer,
}, testInfo) => {
  const profileDir = testInfo.outputPath("profile");
  const url = `${payloadServer.url}/hydrate`;

  const first = await startCapture({ url, profileDir });
  // Persist beyond the browser restart between captures: session
  // cookies (no expires) aren't written to the profile on disk.
  await first.context.addCookies([
    {
      name: "session_cookie",
      value: "keepme",
      url: payloadServer.url,
      expires: Math.floor(Date.now() / 1000) + 3600,
    },
  ]);
  await runToDone(first, "fetched");

  const second = await startCapture({ url, profileDir, clearOriginStorage: true });
  // The clear already ran (inside startCapture, pre-goto); check before
  // runToDone closes the context.
  const cookies = await second.context.cookies(payloadServer.url);
  expect(
    cookies.map(({ name, value }) => ({ name, value })),
    "cookie survives the storage clear",
  ).toContainEqual({ name: "session_cookie", value: "keepme" });
  const secondMessages = await runToDone(second, "fetched");

  // `requestWillBeSent` reports renderer-side headers; cookies are added
  // later by the network service and only show up in the ExtraInfo
  // event, which carries a requestId but no URL.
  const [rwbs] = payloadRWBS(secondMessages);
  const extraInfo = secondMessages.find(
    (m) =>
      m.method === "Network.requestWillBeSentExtraInfo" &&
      m.params?.requestId === rwbs?.params?.requestId,
  );
  expect(
    extraInfo?.params?.headers?.Cookie ?? "",
    "refetched payload request carries the surviving cookie",
  ).toContain("session_cookie=keepme");
});
