/**
 * End-to-end: startCapture() against the real internet (example.com).
 *
 * Exercises the real-site code path — launchPersistentContext, waitUntil
 * 'commit', the streaming events iterable, the click-driven termination —
 * that persistent_injection.spec.mjs doesn't cover. Requires network.
 */
import { test, expect } from "./fixtures.mjs";

test("startCapture against example.com", async ({ startCapture }) => {
  const session = await startCapture({ url: "https://example.com" });

  // Wait for the page-level fetch to complete before signalling done,
  // so the responseReceived event for example.com has time to flush
  // with its body attached.
  await session.page.waitForLoadState("networkidle");
  await session.page.click("#capture-done");

  const messages = [];
  for await (const msg of session.events) messages.push(msg);

  const responses = messages.filter(
    (m) =>
      m.method === "Network.responseReceived" &&
      m.params.response?.url?.includes("example.com"),
  );
  expect(responses.length).toBeGreaterThanOrEqual(1);

  const r = responses[0];
  const body = r.params.response.body ?? "";
  const text =
    r.params.response.encoding === "base64"
      ? Buffer.from(body, "base64").toString("utf-8")
      : body;
  expect(text).toMatch(/Example Domain/);
});
