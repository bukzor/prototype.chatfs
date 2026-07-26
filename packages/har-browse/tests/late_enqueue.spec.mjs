/**
 * Anything the passthrough tries to enqueue after the events stream has
 * ended lands in a closed queue -- the event is unrecoverable by then,
 * so the failure must at least be loud: one stderr line naming each
 * dropped event, instead of silence. Same silent-loss shape the drain
 * work closes at the cut, here at the pipe's exit.
 */
import { test, expect } from "./fixtures.mjs";
import { drainMessages } from "./_common/testing.mjs";

test("post-end CDP events are reported on stderr, not silently dropped", async ({
  startCapture,
  payloadServer,
}) => {
  const session = await startCapture({ url: `${payloadServer.url}/` });

  /** @type {string[]} */
  const stderrWrites = [];
  const origWrite = process.stderr.write.bind(process.stderr);
  process.stderr.write = /** @type {typeof process.stderr.write} */ (
    (chunk, ...rest) => {
      stderrWrites.push(String(chunk));
      return origWrite(chunk, .../** @type {[any]} */ (rest));
    }
  );
  try {
    await session.page.click("#capture-done");
    await drainMessages(session);
    await session.done;

    // The CDP session is still attached (close() not called yet), so a
    // fresh page request lands events on the now-ended stream.
    await session.page.evaluate(() => {
      fetch("/payload?id=late").catch(() => {});
    });

    await expect
      .poll(() => stderrWrites.join(""), {
        message: "late event reported on stderr",
        timeout: 5000,
      })
      .toContain("after stream end");
  } finally {
    process.stderr.write = origWrite;
  }
});
