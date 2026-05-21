/**
 * `track()` on the page-listener's `wireSession` ensures close()'s
 * inFlight drain awaits popup CDP attachment before emitting "end".
 *
 * Deterministic-race construction: monkey-patch `context.newCDPSession`
 * AFTER the initial page's wireSession has already attached, so the
 * delay only affects popup wireSessions. The popup's events flow
 * through wireSession's CDP handlers, which only activate after
 * `Network.enable` acks. With `track`, close()'s allSettled awaits the
 * (slow) wireSession before emit('end'), so the popup RR lands in the
 * queue before the iterator closes. Without `track`, emit('end') fires
 * immediately and the popup RR is dropped on the floor.
 */
import { test, expect } from "./fixtures.mjs";
import { drainMessages, findRR } from "./_common/testing.mjs";

const PROBE_DELAY_MS = 500;

test("popup wireSession is awaited at close (slow CDP attach)", async ({
  startCapture,
  payloadServer,
}) => {
  test.setTimeout(15_000);

  const session = await startCapture({ url: `${payloadServer.url}/` });

  // Patch newCDPSession so popup wireSessions complete `Network.enable`
  // (events start flowing) but then sleep on `Runtime.enable` before
  // wireSession returns. The initial page's wireSession already ran
  // inside startCapture before we got here — only popup wireSessions
  // hit this slow path. We delay AFTER Network.enable so the popup's
  // /payload events ARE delivered to our session; the race is then
  // whether emit('end') waits for the (slow) wireSession to finish
  // — which is exactly what `track()` ensures.
  const origNewCDPSession = session.context.newCDPSession.bind(
    session.context,
  );
  session.context.newCDPSession = async (p) => {
    const s = await origNewCDPSession(p);
    const origSend = s.send.bind(s);
    s.send = async (/** @type {string} */ method, /** @type {any} */ params) => {
      if (method === "Runtime.enable") {
        await new Promise((r) => setTimeout(r, PROBE_DELAY_MS));
      }
      return origSend(method, params);
    };
    return s;
  };

  // Open a popup whose /payload events arrive AFTER the click. The
  // 300ms fetch delay ensures loadingFinished fires well after Done
  // resolves. With track(), allSettled awaits the slow wireSession
  // (PROBE_DELAY_MS) so the popup's RR reaches the queue. Without
  // track, allSettled completes near-instantly post-click and the
  // popup RR arrives after emit('end'), missing the iterator.
  const POPUP_FETCH_DELAY_MS = 300;
  const popupWork = (async () => {
    const popup = await session.context.newPage();
    await popup.goto(`${payloadServer.url}/`);
    await popup.evaluate(
      async ({ d }) => {
        await fetch(`/payload?id=race-popup&delay=${d}`).then((r) => r.text());
      },
      { d: POPUP_FETCH_DELAY_MS },
    );
  })();

  // Wait for the popup's wireSession to enter inFlight (page event +
  // page-listener handler runs) but click before its body-fetch
  // completes. Keep the click before POPUP_FETCH_DELAY_MS — the gap
  // between click and popup-body-arrival is the window the track()
  // wrapper protects.
  await new Promise((r) => setTimeout(r, 50));
  await Promise.all([popupWork, session.page.click("#capture-done")]);

  const messages = await drainMessages(session);

  const popupRR = findRR(messages, "id=race-popup");
  expect(popupRR, "popup /payload RR captured under slow wireSession").toBeTruthy();
});
