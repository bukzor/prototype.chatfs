#!/usr/bin/env node
import { parseArgs } from "node:util";
import { readFileSync } from "node:fs";
import { startCapture } from "./host_puppeteer.mjs";
import { cachePath } from "./cache.mjs";

const usage = `\
usage: har-browse [URL] [options] > events.jsonl

Launch a persistent-profile Chromium at URL (default
http://127.0.0.1:8000) and stream every CDP event as {method, params}
JSONL to stdout. The run ends when the human clicks the injected "Done
Capturing" button or closes the window.

options:
  --profile NAME         browser profile to use; persists under
                         \${XDG_CACHE_HOME:-~/.cache}/har-browse/profile/NAME
                         so logins survive across runs (default: default_profile)
  --howto PATH           text file shown in the in-page overlay as
                         instructions for the human driving the capture
  --keep-origin-storage  keep the target origin's IndexedDB and Cache
                         Storage; by default they are wiped before
                         navigation so the app must fetch its data over
                         the network, where the capture can see it
  --headless             no visible window; without a Done button the run
                         ends when the consumer closes the pipe or the
                         process dies (for unattended captures)
  -h, --help             show this help
`;

let parsed;
try {
  parsed = parseArgs({
    options: {
      howto: { type: "string" },
      profile: { type: "string", default: "default_profile" },
      // Clearing is the default: a provider that hydrates from its own
      // persisted cache produces a capture with none of the payload in
      // it, and that failure is silent. `--keep-origin-storage` opts out
      // for the cases where the local state is the point -- inspecting
      // what an app persisted, or preserving a locally-held draft.
      "keep-origin-storage": { type: "boolean", default: false },
      // No visible window, same browser -- see `startCapture`'s
      // `windowless`. Not Chromium's `--headless`, which would rewrite
      // the User-Agent. There is no Done button to click without a
      // surface, so the run ends when its consumer closes the pipe or the
      // process dies: for unattended captures and the test suite.
      headless: { type: "boolean", default: false },
      help: { type: "boolean", short: "h", default: false },
    },
    allowPositionals: true,
  });
} catch (err) {
  const { code, message } = /** @type {NodeJS.ErrnoException} */ (err);
  if (code?.startsWith("ERR_PARSE_ARGS")) {
    console.error(`har-browse: ${message}\n\n${usage}`);
    process.exit(2);
  }
  throw err;
}
const { values, positionals } = parsed;
if (values.help) {
  process.stdout.write(usage);
  process.exit(0);
}
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
  windowless: values.headless,
});
try {
  for await (const ev of session.events) {
    if (stdoutClosed) break;
    process.stdout.write(JSON.stringify(ev) + "\n");
  }
} finally {
  await session.close();
}
