#!/usr/bin/env node
/**
 * `har-browse <url> | head -n 1` exits cleanly: no EPIPE stack,
 * no orphan Chromium.
 */
import { execFile, spawn } from "node:child_process";
import { rmSync } from "node:fs";
import { homedir } from "node:os";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { promisify } from "node:util";

const exec = promisify(execFile);
const __dirname = dirname(fileURLToPath(import.meta.url));
const port = 8767;
const profileName = `epipe-test-${process.pid}`;
// Don't override XDG_CACHE_HOME for the bin — playwright uses it to
// locate its bundled Chromium. Unique profile name + directed cleanup.
const profileDir = join(
  process.env.XDG_CACHE_HOME || join(homedir(), ".cache"),
  "har-browse",
  "profile",
  profileName,
);

const server = spawn(
  "python3",
  [
    "-m",
    "http.server",
    String(port),
    "--directory",
    join(__dirname, "..", "toy_server"),
  ],
  { stdio: "ignore" },
);

for (let i = 0; i < 50; i++) {
  try {
    if ((await fetch(`http://127.0.0.1:${port}/`)).ok) break;
  } catch {
    // server not yet listening; retry
  }
  await new Promise((r) => setTimeout(r, 100));
}

try {
  // sh-built pipeline so the OS pipe is direct between har-browse and
  // head — no Node mediation that could keep the pipe alive after head
  // exits.
  const bin = join(__dirname, "har_browse.mjs");
  const cmd = `node ${JSON.stringify(bin)} --profile ${profileName} http://127.0.0.1:${port}/ | head -n 1`;
  const { stdout, stderr } = await exec("sh", ["-c", cmd], { timeout: 30000 });

  const parsed = JSON.parse(stdout.trim());
  console.log("json keys: " + JSON.stringify(Object.keys(parsed)));

  if (
    stderr.includes("Error: write EPIPE") ||
    stderr.includes("Unhandled 'error' event")
  ) {
    console.log("stderr:\n" + stderr);
    console.log("FAIL");
    process.exit(1);
  }
  console.log("PASS");
} finally {
  server.kill();
  rmSync(profileDir, { recursive: true, force: true });
}
