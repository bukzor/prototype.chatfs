/**
 * `startCapture` must attach CDP listeners BEFORE `page.goto(url)`, or
 * the initial document's `Network.requestWillBeSent` / `responseReceived`
 * events are lost and the captured stream has no entry for the root
 * navigation.
 *
 * The bug also disables the overlay (addInitScript runs too late for
 * the current page), so an end-via-#capture-done flow hangs. This test
 * ends the stream by closing the context — that path catches the
 * captured-RR loss without depending on the overlay.
 */
import { test, expect } from "./fixtures.mjs";
import { drainMessages } from "./_common/testing.mjs";

test("initial navigation RR is captured", async ({ startCapture, payloadServer }) => {
  test.setTimeout(10_000);

  const session = await startCapture({ url: `${payloadServer.url}/` });

  await session.page.waitForLoadState("networkidle");
  // End the stream via context close (independent of the overlay).
  await session.context.close();

  const messages = await drainMessages(session);

  // Equality (not includes) — assert the root URL specifically.
  const rootRR = messages.find(
    (m) =>
      m.method === "Network.responseReceived" &&
      m.params?.response?.url === `${payloadServer.url}/`,
  );
  expect(rootRR, "initial nav RR captured").toBeTruthy();
});
