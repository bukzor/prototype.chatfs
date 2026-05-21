/**
 * `response.encoding = "base64"` must only be set when CDP reports
 * `base64Encoded: true`. Setting it unconditionally (or always to a
 * fixed value) corrupts text responses: downstream HAR consumers
 * decode the raw text as base64 and produce garbled output.
 *
 * Network-independent: the toy server serves JSON and HTML — both
 * arrive as text from CDP and must NOT carry `encoding: "base64"`.
 */
import { test, expect } from "./fixtures.mjs";
import { drainMessages, findRR } from "./_common/testing.mjs";

test("text responses are not tagged base64 in capture stream", async ({
  startCapture,
  payloadServer,
}) => {
  const session = await startCapture({ url: `${payloadServer.url}/` });

  await session.page.evaluate(() =>
    fetch("/payload?id=enc-test&delay=0").then((r) => r.text()),
  );
  await session.page.click("#capture-done");

  const messages = await drainMessages(session);

  // The /payload response is JSON (textual). Its captured RR must
  // have `body` populated AND `encoding` unset/non-"base64". With the
  // bug, every RR carries encoding="base64" regardless of CDP's
  // base64Encoded flag, which would mistag this text body.
  const payloadRR = findRR(messages, "/payload");
  expect(payloadRR, "payload RR captured").toBeTruthy();
  expect(payloadRR.params.response.body, "payload body present").toBeTruthy();
  expect(
    payloadRR.params.response.encoding,
    "text body must not be tagged base64",
  ).not.toBe("base64");

  // Verify the body is genuinely the JSON we sent (not a base64
  // string that happens to also decode).
  const parsed = JSON.parse(payloadRR.params.response.body);
  expect(parsed.id).toBe("enc-test");
});
