#!/usr/bin/env node
/**
 * End-to-end: captureEvents → harFromMessages → HAR 1.2 document.
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
import { fileURLToPath } from "node:url";
import { harFromMessages } from "chrome-har";
import { captureEvents } from "./capture.mjs";

const __dirname = dirname(fileURLToPath(import.meta.url));
const port = 8766;
const profileDir = mkdtempSync(join(tmpdir(), "har-browse-e2e-har-"));

const server = spawn(
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

// Wait for the server to accept connections (poll, don't sleep-and-hope).
for (let i = 0; i < 50; i++) {
  try {
    const r = await fetch(`http://127.0.0.1:${port}/`);
    if (r.ok) break;
  } catch {
    // server not yet listening; retry
  }
  await new Promise((r) => setTimeout(r, 100));
}

try {
  const messages = [];
  for await (const msg of captureEvents({
    url: `http://127.0.0.1:${port}`,
    profileDir,
    headless: true,
    onPageReady: async (page) => {
      // Fetch the fixture so it lands in the event stream.
      await page.evaluate(() =>
        fetch("/api/conversation").then((r) => r.text()),
      );
      await page.waitForLoadState("networkidle");
      await page.click("#capture-done");
    },
  })) {
    messages.push(msg);
  }

  const har = await harFromMessages(messages, {
    includeTextFromResponseBody: true,
  });

  // Shape assertions.
  const entries = har.log.entries;
  const pages = har.log.pages;
  const byUrl = (suffix) => entries.find((e) => e.request.url.endsWith(suffix));

  const root = byUrl(`:${port}/`);
  const css = byUrl("/index.css");
  const js = byUrl("/index.js");
  const api = byUrl("/api/conversation");

  const apiText = api?.response?.content?.text ?? "";
  const apiBody =
    api?.response?.content?.encoding === "base64"
      ? Buffer.from(apiText, "base64").toString("utf-8")
      : apiText;
  let apiJson = null;
  try {
    apiJson = JSON.parse(apiBody);
  } catch (e) {
    console.log("parse-err: " + e.message);
    console.log("sample: " + JSON.stringify(apiBody.slice(0, 120)));
  }

  console.log("entries: " + entries.length);
  console.log("pages: " + pages.length);
  console.log("root: " + !!root);
  console.log("css: " + !!css);
  console.log("js: " + !!js);
  console.log("api: " + !!api + " body-len=" + apiBody.length);
  const msgCount = apiJson?.messages ? Object.keys(apiJson.messages).length : 0;
  console.log("api messages: " + msgCount);

  const pass =
    root &&
    css &&
    js &&
    api &&
    msgCount >= 1 &&
    pages.length >= 1 &&
    root.timings &&
    typeof root.time === "number";

  console.log(pass ? "PASS" : "FAIL");
  if (!pass) process.exit(1);
} finally {
  server.kill();
  rmSync(profileDir, { recursive: true, force: true });
}
