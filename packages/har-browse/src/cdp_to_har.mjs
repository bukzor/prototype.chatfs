#!/usr/bin/env node
/**
 * Read CDP `{method, params}` JSONL from stdin (the shape emitted by
 * `har-browse`), hand it to `chrome-har.harFromMessages`, and write a
 * HAR 1.2 document to stdout.
 *
 * Response bodies ride on `Network.responseReceived.params.response.body`
 * (with `.encoding = "base64"` when applicable); chrome-har picks them
 * up when `includeTextFromResponseBody: true`.
 */
import { createInterface } from "node:readline";
import { harFromMessages } from "chrome-har";

const messages = [];
const rl = createInterface({ input: process.stdin, crlfDelay: Infinity });
for await (const line of rl) {
  if (!line.trim()) continue;
  messages.push(JSON.parse(line));
}

const har = await harFromMessages(messages, {
  includeTextFromResponseBody: true,
});
process.stdout.write(JSON.stringify(har, null, 2) + "\n");
