#!/usr/bin/env node
import { parseArgs } from "node:util";
import { readFileSync } from "node:fs";
import { startCapture } from "./capture.mjs";
import { cachePath } from "./cache.mjs";

const { values, positionals } = parseArgs({
  options: {
    howto: { type: "string" },
    profile: { type: "string", default: "default_profile" },
  },
  allowPositionals: true,
});
const url = positionals[0] || "http://127.0.0.1:8000";

const howto = values.howto ? readFileSync(values.howto, "utf-8") : undefined;

const profileDir = cachePath("profile", values.profile);

console.error(
  "Launching browser. Click 'Done Capturing' when finished, or close the window to cancel.",
);

// Downstream consumer (head, jq with `limit`, etc.) may close the pipe
// before we're done. Flag EPIPE so the loop can break cleanly and the
// generator's finally can close the browser context.
let stdoutClosed = false;
process.stdout.on("error", (err) => {
  if (err.code === "EPIPE") stdoutClosed = true;
  else throw err;
});

const session = await startCapture({ url, profileDir, howto });
try {
  for await (const ev of session.events) {
    if (stdoutClosed) break;
    process.stdout.write(JSON.stringify(ev) + "\n");
  }
} finally {
  await session.close();
}
