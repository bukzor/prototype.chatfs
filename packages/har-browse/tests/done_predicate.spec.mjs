/**
 * The capture's termination predicate is `Promise.race([waitForFunction,
 * waitForEvent("close")])` — *either* signal must end the stream. If
 * the predicate is reduced to `Promise.all`, a Done-button click alone
 * no longer drains the iterator: the stream hangs until the context
 * also closes. This test exercises the click-only termination path
 * under a tight timeout so the mutation manifests as a fast failure,
 * not a 60-second hang.
 */
import { test, expect } from "./fixtures.mjs";
import { startServer } from "./_common/server.mjs";

test("Done-button click alone drains the events iterator", async ({
  startCapture,
}) => {
  // Tight per-test budget: click → iterator drain → done. With race
  // semantics this finishes within a couple seconds; with all
  // semantics it hangs until 60s playwright timeout.
  test.setTimeout(10_000);

  const server = await startServer();
  try {
    const session = await startCapture({
      url: `http://127.0.0.1:${server.port}/`,
    });

    await session.page.click("#capture-done");

    // Drain the iterator with our own 8s ceiling so the failure is
    // localized (an iterator timeout) rather than a generic test
    // timeout from the outer framework.
    const drain = (async () => {
      const out = [];
      for await (const msg of session.events) out.push(msg);
      return out;
    })();

    const guard = new Promise((_, rej) =>
      setTimeout(() => rej(new Error("iterator did not drain after click")), 8000),
    );

    const messages = await Promise.race([drain, guard]);
    expect(messages.length, "stream produced events").toBeGreaterThan(0);
  } finally {
    await server.close();
  }
});
