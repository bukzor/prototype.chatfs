#!/usr/bin/env node
import { parseArgs } from "node:util";
import { readFileSync } from "node:fs";
import { homedir } from "node:os";
import { join } from "node:path";
import { captureHar } from "./capture.mjs";

const { values, positionals } = parseArgs({
  options: {
    har: { type: "string", default: "out.har" },
    howto: { type: "string" },
    profile: { type: "string", default: "default_profile" },
  },
  allowPositionals: true,
});
const url = positionals[0] || "http://127.0.0.1:8000";

const howto = values.howto
  ? readFileSync(values.howto, "utf-8")
  : undefined;

const cacheHome = process.env.XDG_CACHE_HOME || join(homedir(), ".cache");
const profileDir = join(cacheHome, "har-browse", "profile", values.profile);

console.error(
  "Launching browser. Click 'Done Capturing' when finished, or close the window to cancel.",
);

const { outcome } = await captureHar({
  url,
  harPath: values.har,
  profileDir,
  howto,
});

if (outcome === "cancel") {
  console.error("Cancelled by user.");
  process.exit(2);
}

console.error(`HAR written to ${values.har}`);
