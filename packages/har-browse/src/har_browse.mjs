#!/usr/bin/env node
import { parseArgs } from "node:util";
import { readFileSync } from "node:fs";
import { captureEvents } from "./capture.mjs";
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

for await (const ev of captureEvents({ url, profileDir, howto })) {
  process.stdout.write(JSON.stringify(ev) + "\n");
}
