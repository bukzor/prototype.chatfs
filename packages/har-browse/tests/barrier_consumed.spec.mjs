/**
 * BARRIER causal-precedence: page-attested consumed responses
 * appear in the CDP stream strictly before the BARRIER markers
 * that fire after they were consumed.
 *
 * Page-side: each consumed response appends its `body.n` (space-
 * delimited) to a `<div id="consumed">`. BARRIER payloads carry the
 * current div contents — the page's committed list of "responses I
 * have observed." The capture pipeline must defer each BARRIER's
 * bindingCalled emit until every body-fetch in flight at the
 * BARRIER's CDP arrival has settled, so every consumed n's RR lands
 * earlier in the JSONL than the BARRIER that names it.
 *
 * Two flavors:
 *
 *  - Adversarial single. Await only the first 1% of fetches, fire
 *    one BARRIER, close immediately. ~99% of /payload fetches are
 *    still in flight at close, so captured is a strict subset of
 *    served. The invariant is subset-form: every consumed n precedes
 *    BARRIER, without asserting full completeness.
 *
 *  - Reentrant multi-checkpoint. Page-side `.then` chain fires a
 *    BARRIER each time the consumed list crosses a threshold
 *    (100, 250, 500). `await Promise.all` of every fetch precedes
 *    the click, so the regime is quiescent at close: captured ==
 *    served (assertNoGaps applies). Tests the reentrant property —
 *    each of the three BARRIERs has its own snapshot's worth of
 *    consumed responses preceding it, and the BARRIERs themselves
 *    land in FIFO order in the stream.
 *
 * Awaiting all fetches defeats the adversarial flavor: by click time,
 * every LF has arrived, every body-fetch has been triggered, and
 * capture's `done.finally` drains them all — collapsing the test into
 * barrier_smoke's all-form invariant. The reentrant flavor does
 * await-all because its invariant *is* the all-form at each
 * threshold; the novelty is multiple BARRIERs per run.
 */
import { test, expect } from "./fixtures.mjs";
import {
  assertCapturedConsistent,
  assertNoGaps,
  drainMessages,
  parsedPayloadRRs,
} from "./_common/testing.mjs";

const N = 500;
const AWAIT_COUNT = Math.max(1, Math.floor(N * 0.01));
const THRESHOLDS = [100, 250, 500];

/**
 * Two-stage bound: warn (annotation + stderr) if value > warnAt,
 * hard fail via expect() if value > failAt. Use with `failAt = 2 * warnAt`
 * to give a graceful tightening window before the regression becomes a
 * test failure.
 */
function bound({ name, value, warnAt, failAt }, testInfo) {
  if (value > warnAt && value <= failAt) {
    const msg = `${name}=${value} above warn ${warnAt} (fails above ${failAt})`;
    console.warn(`WARN: ${msg}`);
    testInfo.annotations.push({ type: "warning", description: msg });
  }
  expect(value, `${name}=${value} above fail threshold ${failAt}`).toBeLessThanOrEqual(
    failAt,
  );
}

function findBarriers(messages) {
  const out = [];
  for (let i = 0; i < messages.length; i++) {
    const m = messages[i];
    if (
      m.method === "Runtime.bindingCalled" &&
      m.params?.name === "harBrowseMark" &&
      typeof m.params?.payload === "string" &&
      m.params.payload.startsWith("BARRIER:")
    ) {
      const parsed = JSON.parse(m.params.payload.slice("BARRIER:".length));
      out.push({ idx: i, consumed: parsed.consumed });
    }
  }
  return out;
}

/**
 * Every n in `barrier.consumed` must appear as a /payload RR at a
 * JSONL idx strictly less than `barrier.idx`. Names the missing ones.
 */
function assertConsumedPrecede(messages, barrier) {
  const seen = new Set(
    parsedPayloadRRs(messages.slice(0, barrier.idx)).map((rr) => rr.body.n),
  );
  const missing = barrier.consumed.filter((n) => !seen.has(n));
  expect(
    missing,
    `consumed RRs precede BARRIER (idx ${barrier.idx})`,
  ).toEqual([]);
}

test("BARRIER (adversarial single): consumed RRs precede marker", async (
  { startCapture, payloadServer },
  testInfo,
) => {
  const session = await startCapture({ url: `${payloadServer.url}/` });

  await session.page.evaluate(
    async ({ n, awaitCount }) => {
      const div = document.createElement("div");
      div.id = "consumed";
      document.body.appendChild(div);
      const all = [];
      for (let i = 0; i < n; i++) {
        all.push(
          fetch(`/payload?id=${i}`)
            .then((r) => r.json())
            .then(({ n: rn }) => {
              div.appendChild(document.createTextNode(rn + " "));
            }),
        );
      }
      // Wait for the first 1% to settle so the list is non-empty,
      // then snapshot it into BARRIER. The remaining ~99% stay in
      // flight — that's the adversarial condition under test.
      await Promise.all(all.slice(0, awaitCount));
      const consumed = div.textContent
        .trim()
        .split(/\s+/)
        .filter(Boolean)
        .map(Number);
      window.harBrowseMark("BARRIER:" + JSON.stringify({ consumed }));
    },
    { n: N, awaitCount: AWAIT_COUNT },
  );

  await session.page.click("#capture-done");

  const messages = await drainMessages(session);

  const barriers = findBarriers(messages);
  expect(barriers.length, "BARRIER emitted exactly once").toBe(1);
  expect(barriers[0].consumed.length, "consumed not empty").toBeGreaterThan(0);

  assertConsumedPrecede(messages, barriers[0]);

  // Regime witnesses: at BARRIER time the renderer's consumed list
  // and the session's /payload RR count must both be much smaller
  // than N. If either exceeds N/2, the test collapsed into the
  // all-form and the subset invariant wasn't exercised. Warn earlier
  // (at N/4, N/10) to surface regressions before they hard-fail.
  const rrsBefore = messages
    .slice(0, barriers[0].idx)
    .filter(
      (m) =>
        m.method === "Network.responseReceived" &&
        (m.params?.response?.url ?? "").includes("/payload"),
    ).length;
  bound(
    {
      name: "consumed",
      value: barriers[0].consumed.length,
      warnAt: N / 4,
      failAt: N / 2,
    },
    testInfo,
  );
  bound(
    { name: "rrBefore", value: rrsBefore, warnAt: N / 10, failAt: N / 5 },
    testInfo,
  );

  assertCapturedConsistent({ messages, server: payloadServer });
});

test("BARRIER (reentrant): consumed RRs precede each of N markers", async ({
  startCapture,
  payloadServer,
}) => {
  const session = await startCapture({ url: `${payloadServer.url}/` });

  await session.page.evaluate(
    async ({ n, thresholds }) => {
      const div = document.createElement("div");
      div.id = "consumed";
      document.body.appendChild(div);
      await Promise.all(
        Array.from({ length: n }, (_, i) =>
          fetch(`/payload?id=${i}`)
            .then((r) => r.json())
            .then(({ n: rn }) => {
              div.appendChild(document.createTextNode(rn + " "));
              if (thresholds.includes(div.childNodes.length)) {
                const consumed = div.textContent
                  .trim()
                  .split(/\s+/)
                  .filter(Boolean)
                  .map(Number);
                window.harBrowseMark(
                  "BARRIER:" + JSON.stringify({ consumed }),
                );
              }
            }),
        ),
      );
    },
    { n: N, thresholds: THRESHOLDS },
  );

  await session.page.click("#capture-done");

  const messages = await drainMessages(session);

  const barriers = findBarriers(messages);
  expect(barriers.length, "one BARRIER per threshold").toBe(THRESHOLDS.length);
  for (let i = 0; i < THRESHOLDS.length; i++) {
    expect(
      barriers[i].consumed.length,
      `BARRIER #${i} consumed size == threshold ${THRESHOLDS[i]}`,
    ).toBe(THRESHOLDS[i]);
  }

  for (const b of barriers) {
    assertConsumedPrecede(messages, b);
  }

  // Quiescent at close: Promise.all of every fetch settled before
  // click, so capture's done.finally drained every body-fetch.
  // Captured set == served set with no gaps.
  assertNoGaps({ events: messages, requestLog: payloadServer.requestLog });

  assertCapturedConsistent({ messages, server: payloadServer });
});
