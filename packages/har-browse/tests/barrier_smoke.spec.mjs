/**
 * BARRIER snapshot-defer invariant + {1..K} no-gaps invariant.
 *
 * Page fires N parallel `/payload?id=K&delay=D` fetches, awaits them,
 * then calls `window.harBrowseMark("BARRIER:end")`. The capture
 * pipeline must defer emitting the BARRIER bindingCalled until every
 * body-fetch pending at BARRIER's CDP arrival has settled — so all
 * `/payload` `Network.responseReceived` events land at strictly
 * earlier JSONL indices than BARRIER. Additionally, the set of `n`
 * values stamped into captured /payload bodies must equal {1..served}.
 */
import { test, expect } from "./fixtures.mjs";
import { startServer } from "./_common/server.mjs";
import { assertNoGaps } from "./_common/testing.mjs";

const N = 10;
const DELAY_MS = 20;

test("BARRIER: pending /payload responses precede BARRIER in stream", async ({
  startCapture,
}) => {
  const server = await startServer();
  try {
    const session = await startCapture({
      url: `http://127.0.0.1:${server.port}/`,
    });

    await session.page.evaluate(
      async ({ n, delay }) => {
        await Promise.all(
          Array.from({ length: n }, (_, i) =>
            fetch(`/payload?id=${i}&delay=${delay}`).then((r) => r.text()),
          ),
        );
        window.harBrowseMark("BARRIER:end");
      },
      { n: N, delay: DELAY_MS },
    );

    await session.page.click("#capture-done");

    const messages = [];
    for await (const msg of session.events) messages.push(msg);

    const barrierIdx = messages.findIndex(
      (m) =>
        m.method === "Runtime.bindingCalled" &&
        m.params?.name === "harBrowseMark" &&
        m.params?.payload === "BARRIER:end",
    );
    expect(barrierIdx, "BARRIER bindingCalled emitted").toBeGreaterThanOrEqual(
      0,
    );

    const payloadIndices = messages
      .map((m, i) =>
        m.method === "Network.responseReceived" &&
        (m.params?.response?.url ?? "").includes("/payload")
          ? i
          : -1,
      )
      .filter((i) => i >= 0);

    expect(payloadIndices.length, "all /payload responses captured").toBe(N);
    for (const idx of payloadIndices) {
      expect(idx, "/payload response precedes BARRIER").toBeLessThan(
        barrierIdx,
      );
    }

    // Every emitted method matches `Foo.bar` shape — the emit-override's
    // `.` filter keeps internal EventEmitter events (close, error,
    // playwright internals) out of the CDP stream.
    for (const m of messages) {
      expect(m.method, `method '${m.method}' is CDP-shaped`).toMatch(
        /^[A-Za-z]+\.[A-Za-z]+/,
      );
    }

    assertNoGaps({ events: messages, requestLog: server.requestLog });
  } finally {
    await server.close();
  }
});

test("non-anchored 'BARRIER:' substring isn't deferred", async ({
  startCapture,
}) => {
  // `params.payload?.startsWith?.("BARRIER:")` is anchored. Bindings
  // whose payload merely *contains* "BARRIER:" mid-string (e.g. a debug
  // marker) must emit at their natural CDP position, not behind the
  // in-flight body drain. A non-anchored predicate would mistakenly
  // defer them.
  //
  // Construct the in-flight regime: await N parallel fetches so all
  // their loadingFinished events have arrived (their body-fetches sit
  // in `inFlight`), then immediately issue the non-anchored binding.
  // Under correct startsWith semantics, the binding emits at its
  // natural CDP position — i.e., before the RRs whose body-fetches
  // haven't resolved yet. Under includes semantics, the binding is
  // deferred until every in-flight body-fetch settles, landing after
  // all the RRs.
  const N = 10;
  const server = await startServer();
  try {
    const session = await startCapture({
      url: `http://127.0.0.1:${server.port}/`,
    });

    await session.page.evaluate(
      async ({ n }) => {
        await Promise.all(
          Array.from({ length: n }, (_, i) =>
            fetch(`/payload?id=${i}&delay=20`).then((r) => r.text()),
          ),
        );
        window.harBrowseMark("debug-BARRIER:foo");
      },
      { n: N },
    );

    await session.page.click("#capture-done");

    const messages = [];
    for await (const msg of session.events) messages.push(msg);

    const bindingIdx = messages.findIndex(
      (m) =>
        m.method === "Runtime.bindingCalled" &&
        m.params?.payload === "debug-BARRIER:foo",
    );
    const lastPayloadRRIdx = messages.reduce(
      (acc, m, i) =>
        m.method === "Network.responseReceived" &&
        (m.params?.response?.url ?? "").includes("/payload")
          ? i
          : acc,
      -1,
    );
    expect(bindingIdx, "non-anchored binding emitted").toBeGreaterThanOrEqual(0);
    expect(lastPayloadRRIdx, "/payload RRs present").toBeGreaterThanOrEqual(0);
    expect(
      bindingIdx,
      "non-anchored binding not deferred behind RRs",
    ).toBeLessThan(lastPayloadRRIdx);
  } finally {
    await server.close();
  }
});
