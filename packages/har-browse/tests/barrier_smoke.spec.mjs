/**
 * BARRIER snapshot-defer invariant.
 *
 * Page fires N parallel `/payload?id=K&delay=D` fetches, awaits them,
 * then calls `window.harBrowseMark("BARRIER:end")`. The capture
 * pipeline must defer emitting the BARRIER bindingCalled until every
 * body-fetch pending at BARRIER's CDP arrival has settled — so all
 * `/payload` `Network.responseReceived` events land at strictly
 * earlier JSONL indices than BARRIER.
 */
import { createServer } from "node:http";
import { test, expect } from "./fixtures.mjs";

const N = 10;
const DELAY_MS = 20;

test("BARRIER: pending /payload responses precede BARRIER in stream", async ({
  startCapture,
}) => {
  const server = createServer(async (req, res) => {
    const url = new URL(req.url, `http://${req.headers.host}`);
    if (url.pathname === "/payload") {
      const id = url.searchParams.get("id") ?? "";
      const delay = Number(url.searchParams.get("delay") ?? 0);
      if (delay > 0) await new Promise((r) => setTimeout(r, delay));
      res.writeHead(200, { "content-type": "application/json" });
      res.end(JSON.stringify({ id }));
      return;
    }
    res.writeHead(200, { "content-type": "text/html" });
    res.end("<!doctype html><html><body>barrier smoke</body></html>");
  });
  await new Promise((r) => server.listen(0, "127.0.0.1", r));
  const { port } = server.address();
  try {
    const session = await startCapture({ url: `http://127.0.0.1:${port}/` });

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
  } finally {
    await new Promise((r) => server.close(r));
  }
});
