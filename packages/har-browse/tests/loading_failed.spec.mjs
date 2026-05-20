/**
 * Network.loadingFailed: when a request errors out (e.g. fetch to a
 * closed port), capture must enqueue the loadingFailed event so
 * downstream HAR builders can mark the entry as failed.
 */
import { test, expect } from "./fixtures.mjs";
import { startServer } from "./_common/server.mjs";

test("Network.loadingFailed emitted for failed fetch", async ({
  startCapture,
  toyServer,
}) => {
  const session = await startCapture({ url: toyServer.url });

  // Trigger a network failure: fetch a closed local port. The browser
  // emits Network.loadingFailed; capture must forward it.
  await session.page.evaluate(() =>
    fetch("http://127.0.0.1:1/", { mode: "no-cors" }).catch(() => {}),
  );

  await session.page.click("#capture-done");

  const messages = [];
  for await (const msg of session.events) messages.push(msg);

  const failed = messages.filter(
    (m) => m.method === "Network.loadingFailed",
  );
  expect(failed.length, "at least one loadingFailed event").toBeGreaterThan(0);
});

test("RR flushed for mid-body abort (responseReceived precedes loadingFailed)", async ({
  startCapture,
}) => {
  // Request gets headers then the server destroys the socket mid-body.
  // CDP fires: responseReceived (headers stashed in `awaitingBody`)
  // then loadingFailed. `onLoadingFailed` must flush the stashed RR
  // before enqueueing the LFail so HAR builders see a response entry.
  const server = await startServer();
  try {
    const session = await startCapture({
      url: `http://127.0.0.1:${server.port}/`,
    });

    await session.page.evaluate(() =>
      fetch("/abort-after-headers").catch(() => {}),
    );

    await session.page.click("#capture-done");

    const messages = [];
    for await (const msg of session.events) messages.push(msg);

    const rrIdx = messages.findIndex(
      (m) =>
        m.method === "Network.responseReceived" &&
        (m.params?.response?.url ?? "").includes("/abort-after-headers"),
    );
    const lfailIdx = messages.findIndex(
      (m) => m.method === "Network.loadingFailed",
    );
    expect(lfailIdx, "loadingFailed present").toBeGreaterThanOrEqual(0);
    expect(rrIdx, "stashed RR flushed").toBeGreaterThanOrEqual(0);
    expect(rrIdx, "RR precedes LFail").toBeLessThan(lfailIdx);
  } finally {
    await server.close();
  }
});
