/**
 * Ordering invariant: the event-iterator queue must be subscribed
 * *before* CDP attach. `wireSession()` enables Page/Runtime, which
 * replay existing state via events (e.g. `Runtime.executionContextCreated`
 * for the about:blank initial frame). If `on(emitter, "event", …)` is
 * called after those enables, the replay events fire to an emitter with
 * no listener and are silently lost — `on()` does not retroactively
 * capture past emits.
 */
import { test, expect } from "./fixtures.mjs";

test("queue captures CDP replay events fired during enable awaits", async ({
  startCapture,
  toyServer,
}) => {
  const session = await startCapture({ url: toyServer.url });
  await session.page.waitForLoadState("load");
  await session.page.click("#capture-done");

  const messages = [];
  for await (const msg of session.events) messages.push(msg);

  // CDP reports about:blank's opaque origin as "://". With the queue
  // subscribed before CDP attach, Runtime.enable replays the initial
  // about:blank execution contexts and they land in the stream.
  const initialBlankContexts = messages.filter(
    (m) =>
      m.method === "Runtime.executionContextCreated" &&
      m.params?.context?.origin === "://",
  );
  expect(
    initialBlankContexts.length,
    "initial about:blank execution contexts captured from Runtime.enable replay",
  ).toBeGreaterThanOrEqual(1);
});
