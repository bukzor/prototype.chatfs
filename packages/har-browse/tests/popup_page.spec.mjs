/**
 * Capture must wire CDP sessions for pages opened *after* the initial
 * page — `context.on("page", ...)` is the per-page registrar.
 *
 * Test: open a second page via `context.newPage()`, fetch a known URL
 * from it, assert the captured stream contains that fetch's RR.
 */
import { test, expect } from "./fixtures.mjs";
import { startServer } from "./_common/server.mjs";

test("popup pages are wired and produce capture events", async ({
  startCapture,
}) => {
  const server = await startServer();
  try {
    const session = await startCapture({
      url: `http://127.0.0.1:${server.port}/`,
    });

    // Second page opened programmatically. With the on-page listener
    // removed, no CDP session is attached and its events vanish.
    const popup = await session.context.newPage();
    await popup.goto(`http://127.0.0.1:${server.port}/`);
    await popup.evaluate(() =>
      fetch("/payload?id=from-popup&delay=0").then((r) => r.text()),
    );

    await session.page.click("#capture-done");

    const messages = [];
    for await (const msg of session.events) messages.push(msg);

    const popupResponse = messages.find(
      (m) =>
        m.method === "Network.responseReceived" &&
        (m.params?.response?.url ?? "").includes("id=from-popup"),
    );
    expect(popupResponse, "popup fetch captured").toBeTruthy();
  } finally {
    await server.close();
  }
});
