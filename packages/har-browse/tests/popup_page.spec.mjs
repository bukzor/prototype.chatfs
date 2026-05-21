/**
 * Capture must wire CDP sessions for pages opened *after* the initial
 * page — `context.on("page", ...)` is the per-page registrar.
 *
 * Test: open a second page via `context.newPage()`, fetch a known URL
 * from it, assert the captured stream contains that fetch's RR.
 */
import { test, expect } from "./fixtures.mjs";
import { drainMessages, findRR } from "./_common/testing.mjs";

test("popup pages are wired and produce capture events", async ({
  startCapture,
  payloadServer,
}) => {
  const session = await startCapture({ url: `${payloadServer.url}/` });

  // Second page opened programmatically. With the on-page listener
  // removed, no CDP session is attached and its events vanish.
  const popup = await session.context.newPage();
  await popup.goto(`${payloadServer.url}/`);
  await popup.evaluate(() =>
    fetch("/payload?id=from-popup&delay=0").then((r) => r.text()),
  );

  await session.page.click("#capture-done");

  const messages = await drainMessages(session);

  const popupResponse = findRR(messages, "id=from-popup");
  expect(popupResponse, "popup fetch captured").toBeTruthy();
});
