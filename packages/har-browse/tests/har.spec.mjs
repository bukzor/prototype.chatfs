/**
 * End-to-end: startCapture → harFromMessages → HAR 1.2 document.
 *
 * Validates that the JSONL we emit (CDP `{method, params}` with bodies
 * attached at `Network.responseReceived.params.response.body`) is
 * consumed by `chrome-har` unmodified and yields a usable HAR.
 */
import { harFromMessages } from "chrome-har";
import { test, expect } from "./fixtures.mjs";

test("startCapture → chrome-har produces usable HAR", async ({
  startCapture,
  toyServer,
}) => {
  const session = await startCapture({ url: toyServer.url });

  await session.page.evaluate(() =>
    fetch("/api/conversation").then((r) => r.text()),
  );
  await session.page.waitForLoadState("networkidle");
  await session.page.click("#capture-done");

  const messages = [];
  for await (const msg of session.events) messages.push(msg);

  const har = await harFromMessages(messages, {
    includeTextFromResponseBody: true,
  });

  const byUrl = (suffix) =>
    har.log.entries.find((e) => e.request.url.endsWith(suffix));

  const root = byUrl(`:${toyServer.port}/`);
  expect(root, "root entry").toBeTruthy();
  expect(byUrl("/index.css"), "css entry").toBeTruthy();
  expect(byUrl("/index.js"), "js entry").toBeTruthy();

  const api = byUrl("/api/conversation");
  expect(api, "api/conversation entry").toBeTruthy();
  expect(har.log.pages.length).toBeGreaterThanOrEqual(1);
  expect(root.timings).toBeTruthy();
  expect(typeof root.time).toBe("number");

  const apiText = api.response?.content?.text ?? "";
  const apiBody =
    api.response?.content?.encoding === "base64"
      ? Buffer.from(apiText, "base64").toString("utf-8")
      : apiText;
  const apiJson = JSON.parse(apiBody);
  expect(Object.keys(apiJson?.messages ?? {}).length).toBeGreaterThanOrEqual(1);
});
