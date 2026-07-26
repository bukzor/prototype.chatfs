#!/usr/bin/env node
import { parseArgs } from "node:util";
import { readFileSync } from "node:fs";
import { startCapture } from "./host_puppeteer.mjs";
import { cachePath } from "./cache.mjs";

const { values, positionals } = parseArgs({
  options: {
    howto: { type: "string" },
    profile: { type: "string", default: "default_profile" },
    // Clearing is the default: a provider that hydrates from its own
    // persisted cache produces a capture with none of the payload in
    // it, and that failure is silent. `--keep-origin-storage` opts out
    // for the cases where the local state is the point -- inspecting
    // what an app persisted, or preserving a locally-held draft.
    "keep-origin-storage": { type: "boolean", default: false },
    // For tests and automation. A headless run has no Done button to
    // click, so it ends only when the caller closes the pipe or kills
    // it.
    headless: { type: "boolean", default: false },
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
process.stdout.on("error", (/** @type {NodeJS.ErrnoException} */ err) => {
  if (err.code === "EPIPE") stdoutClosed = true;
  else throw err;
});

const session = await startCapture({
  url,
  profileDir,
  howto,
  clearOriginStorage: !values["keep-origin-storage"],
  headless: values.headless,
});
try {
  for await (const ev of session.events) {
    if (stdoutClosed) break;
    process.stdout.write(JSON.stringify(ev) + "\n");
  }
} finally {
  await session.close();
}
