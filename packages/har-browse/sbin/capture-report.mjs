#!/usr/bin/env node
// @ts-check
// Summarize a capture stream: what was requested, what failed, and
// whether the session looked like a real browser on the wire.
//
//   tools/capture-report.mjs capture.jsonl [--url SUBSTRING]
//   har-browse ... | tools/capture-report.mjs
//
// Reads `{method, params}` JSONL (this package's capture format). The
// per-host status table is the fastest way to spot a provider refusing
// one endpoint while serving the rest -- the shape of an abuse gate,
// as opposed to an auth failure (which refuses everything).
//
// `--url` prints full detail (status, request body, response body) for
// every request whose URL contains the substring, which is how you read
// an RPC error out of a capture without hand-rolling a parser again.
import { createReadStream } from "node:fs";
import { createInterface } from "node:readline";
import { parseArgs } from "node:util";

const { values, positionals } = parseArgs({
  options: { url: { type: "string" }, headers: { type: "boolean" } },
  allowPositionals: true,
});

const input = positionals[0] ? createReadStream(positionals[0]) : process.stdin;

/** @type {Map<string, any>} */
const requests = new Map();
/** @type {Array<{status: number, url: string, requestId: string, body?: string}>} */
const responses = [];
/** @type {Map<string, number>} */
const methodCounts = new Map();
let wireRequests = 0;
let wireHinted = 0;
/** @type {Set<string>} */
const userAgents = new Set();
/** @type {string[]} */
const hintSample = [];

for await (const line of createInterface({ input, crlfDelay: Infinity })) {
  if (!line.trim()) continue;
  /** @type {{method: string, params: any}} */
  let event;
  try {
    event = JSON.parse(line);
  } catch {
    continue;
  }
  const { method, params } = event;
  methodCounts.set(method, (methodCounts.get(method) ?? 0) + 1);

  if (method === "Network.requestWillBeSent") {
    requests.set(params.requestId, params.request);
    const ua = params.request?.headers?.["User-Agent"];
    if (ua) userAgents.add(ua);
  } else if (method === "Network.requestWillBeSentExtraInfo") {
    // ExtraInfo carries the headers that actually went onto the wire;
    // requestWillBeSent carries renderer-provisional ones. Client hints
    // and cookies are only visible here.
    wireRequests += 1;
    const hints = Object.keys(params.headers ?? {}).filter((h) =>
      h.toLowerCase().startsWith("sec-ch-ua"),
    );
    if (hints.length) {
      wireHinted += 1;
      if (!hintSample.length) {
        for (const h of hints.sort()) hintSample.push(`${h}: ${params.headers[h]}`);
      }
    }
  } else if (method === "Network.responseReceived") {
    responses.push({
      status: params.response?.status,
      url: params.response?.url ?? "",
      requestId: params.requestId,
      body: params.response?.body,
    });
  }
}

const events = [...methodCounts.values()].reduce((a, b) => a + b, 0);
console.log(`events ${events}   responses ${responses.length}`);

console.log(`\nUser-Agent (${userAgents.size}):`);
for (const ua of userAgents) console.log(`  ${ua}`);

console.log(
  `\nclient hints: ${wireHinted}/${wireRequests} wire requests` +
    (wireHinted ? "" : "   <-- STRIPPED: no request looked like a real browser"),
);
for (const h of hintSample) console.log(`  ${h}`);

/** @type {Map<string, Map<number, number>>} */
const byHost = new Map();
for (const { status, url } of responses) {
  let host = "(unparseable)";
  try {
    host = new URL(url).host;
  } catch {}
  const statuses = byHost.get(host) ?? new Map();
  statuses.set(status, (statuses.get(status) ?? 0) + 1);
  byHost.set(host, statuses);
}
console.log("\nresponses by host:");
for (const [host, statuses] of [...byHost].sort()) {
  const summary = [...statuses]
    .sort()
    .map(([s, n]) => `${s}x${n}`)
    .join(" ");
  const bad = [...statuses.keys()].some((s) => s >= 400);
  console.log(`  ${bad ? "!" : " "} ${host.padEnd(46)} ${summary}`);
}

const failures = responses.filter((r) => r.status >= 400);
if (failures.length) {
  console.log(`\nfailures (${failures.length}):`);
  for (const f of failures) {
    console.log(`  ${f.status}  ${f.url}`);
    if (f.body) console.log(`        ${f.body.slice(0, 300).replace(/\n/g, " ")}`);
  }
}

if (values.url) {
  const needle = values.url;
  console.log(`\n--- requests matching ${JSON.stringify(needle)}:`);
  for (const r of responses) {
    if (!r.url.includes(needle)) continue;
    const request = requests.get(r.requestId);
    const postData = request?.postData;
    // A CORS preflight carries no body; calling it out avoids reading
    // its 200 as a success of the request it precedes.
    console.log(
      `  ${r.status}  ${postData ? "" : "(no request body -- preflight?) "}${r.url.slice(0, 120)}`,
    );
    if (values.headers && request?.headers) {
      for (const [k, v] of Object.entries(request.headers)) {
        console.log(`     > ${k}: ${String(v).slice(0, 120)}`);
      }
    }
    if (postData) console.log(`     sent: ${postData.slice(0, 240)}`);
    if (r.body) console.log(`     recv: ${r.body.slice(0, 240).replace(/\n/g, " ")}`);
  }
}
