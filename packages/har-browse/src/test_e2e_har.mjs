/**
 * End-to-end: startCapture → harFromMessages → HAR 1.2 document.
 *
 * Validates the central post-pivot claim: the JSONL we emit (CDP
 * `{method, params}` with bodies attached at
 * `Network.responseReceived.params.response.body`) is consumed by
 * `chrome-har` unmodified and yields a usable HAR.
 *
 * Uses the toy server so we get known URLs and a known body
 * (`/api/conversation` returns JSON fixture content).
 */
import { spawn } from "node:child_process";
import { mkdtempSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { dirname, join } from "node:path";
import { after, before, test } from "node:test";
import { fileURLToPath } from "node:url";
import assert from "node:assert/strict";
import { harFromMessages } from "chrome-har";
import { startCapture } from "./capture.mjs";

const __dirname = dirname(fileURLToPath(import.meta.url));
const port = 8766;

let profileDir;
let server;

before(async () => {
  profileDir = mkdtempSync(join(tmpdir(), "har-browse-e2e-har-"));
  server = spawn(
    "python3",
    [
      "-m",
      "http.server",
      String(port),
      "--directory",
      join(__dirname, "..", "toy_server"),
    ],
    { stdio: ["ignore", "pipe", "pipe"] },
  );
  for (let i = 0; i < 50; i++) {
    try {
      if ((await fetch(`http://127.0.0.1:${port}/`)).ok) return;
    } catch {
      // server not yet listening; retry
    }
    await new Promise((r) => setTimeout(r, 100));
  }
  throw new Error("toy server failed to start");
});

after(() => {
  server?.kill();
  rmSync(profileDir, { recursive: true, force: true });
});

test("startCapture → chrome-har produces usable HAR", { timeout: 60000 }, async () => {
  const session = await startCapture({
    url: `http://127.0.0.1:${port}`,
    profileDir,
    headless: true,
  });
  let messages;
  try {
    // Fetch the fixture so it lands in the event stream.
    await session.page.evaluate(() =>
      fetch("/api/conversation").then((r) => r.text()),
    );
    await session.page.waitForLoadState("networkidle");
    await session.page.click("#capture-done");

    messages = [];
    for await (const msg of session.events) messages.push(msg);
  } finally {
    await session.close();
  }

  const har = await harFromMessages(messages, {
    includeTextFromResponseBody: true,
  });

  const entries = har.log.entries;
  const pages = har.log.pages;
  const byUrl = (suffix) => entries.find((e) => e.request.url.endsWith(suffix));

  const root = byUrl(`:${port}/`);
  const css = byUrl("/index.css");
  const js = byUrl("/index.js");
  const api = byUrl("/api/conversation");

  assert.ok(root, "root entry present");
  assert.ok(css, "css entry present");
  assert.ok(js, "js entry present");
  assert.ok(api, "api/conversation entry present");
  assert.ok(pages.length >= 1, "at least one page");
  assert.ok(root.timings, "root has timings");
  assert.equal(typeof root.time, "number");

  const apiText = api.response?.content?.text ?? "";
  const apiBody =
    api.response?.content?.encoding === "base64"
      ? Buffer.from(apiText, "base64").toString("utf-8")
      : apiText;
  const apiJson = JSON.parse(apiBody);
  const msgCount = apiJson?.messages ? Object.keys(apiJson.messages).length : 0;
  assert.ok(msgCount >= 1, `api fixture has messages (got ${msgCount})`);
});
