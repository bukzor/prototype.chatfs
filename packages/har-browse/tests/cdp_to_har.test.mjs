/**
 * `cdp-to-har` CLI: feeds a known {method, params} JSONL stream into the
 * CLI and asserts the emitted HAR includes the response body text — the
 * only signal that `includeTextFromResponseBody: true` is wired up.
 */
import { spawn } from "node:child_process";
import { dirname, join } from "node:path";
import { test } from "node:test";
import { fileURLToPath } from "node:url";
import assert from "node:assert/strict";

const __dirname = dirname(fileURLToPath(import.meta.url));
const BIN = join(__dirname, "..", "src", "cdp_to_har.mjs");

/** Minimal CDP sequence that produces one HAR entry with a JSON body. */
function fixture() {
  return [
    { method: "Page.frameStartedLoading", params: { frameId: "F1" } },
    {
      method: "Network.requestWillBeSent",
      params: {
        frameId: "F1",
        requestId: "R1",
        loaderId: "L1",
        request: {
          url: "http://example.com/api",
          method: "GET",
          headers: {},
        },
        timestamp: 1000,
        wallTime: 1700000000,
        initiator: { type: "other" },
        type: "Fetch",
      },
    },
    {
      method: "Network.responseReceived",
      params: {
        frameId: "F1",
        requestId: "R1",
        loaderId: "L1",
        timestamp: 1001,
        type: "Fetch",
        response: {
          url: "http://example.com/api",
          status: 200,
          statusText: "OK",
          headers: { "content-type": "application/json" },
          mimeType: "application/json",
          protocol: "http/1.1",
          connectionId: 1,
          encodedDataLength: 100,
          body: '{"hello":"world"}',
        },
      },
    },
    {
      method: "Network.loadingFinished",
      params: { requestId: "R1", timestamp: 1002, encodedDataLength: 100 },
    },
  ];
}

/**
 * Run `node BIN` with stdin = one line per item (object → JSON, string →
 * literal); return { code, stdout, stderr }. Empty strings produce blank
 * lines, the regime the blank-line tolerance test exercises.
 */
function runCdpToHar(items) {
  return new Promise((resolve, reject) => {
    const proc = spawn("node", [BIN]);
    let stdout = "";
    let stderr = "";
    proc.stdout.on("data", (c) => (stdout += c));
    proc.stderr.on("data", (c) => (stderr += c));
    proc.on("error", reject);
    proc.on("close", (code) => resolve({ code, stdout, stderr }));
    for (const item of items) {
      const line = typeof item === "string" ? item : JSON.stringify(item);
      proc.stdin.write(line + "\n");
    }
    proc.stdin.end();
  });
}

test("cdp-to-har includes response body text in HAR entries", async () => {
  const { code, stdout, stderr } = await runCdpToHar(fixture());
  assert.equal(code, 0, `non-zero exit; stderr: ${stderr}`);
  const har = JSON.parse(stdout);
  const entry = har.log.entries.find((e) =>
    e.request.url.endsWith("/api"),
  );
  assert.ok(entry, "api entry present in HAR");
  assert.equal(entry.response.content.text, '{"hello":"world"}');
});

test("cdp-to-har tolerates blank lines in JSONL input", async () => {
  // Trailing newlines / stray blank lines from shells & redirects must
  // not crash the parser. Inject a blank line between two valid records
  // and a trailing one.
  const [first, ...rest] = fixture();
  const { code, stdout, stderr } = await runCdpToHar([first, "", ...rest, ""]);
  assert.equal(code, 0, `non-zero exit; stderr: ${stderr}`);
  const har = JSON.parse(stdout);
  assert.ok(har.log.entries.length >= 1, "har entries non-empty");
});
