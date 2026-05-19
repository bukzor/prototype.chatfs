/**
 * `har-browse <url> | head -n 1` exits cleanly: no EPIPE stack,
 * no orphan Chromium.
 */
import { execFile } from "node:child_process";
import { rmSync } from "node:fs";
import { homedir } from "node:os";
import { dirname, join } from "node:path";
import { after, before, test } from "node:test";
import { fileURLToPath } from "node:url";
import { promisify } from "node:util";
import assert from "node:assert/strict";
import { spawnToyServer } from "./_common/toy_server.mjs";

const exec = promisify(execFile);
const __dirname = dirname(fileURLToPath(import.meta.url));
const port = 8767;
const profileName = `epipe-test-${process.pid}`;
const profileDir = join(
  process.env.XDG_CACHE_HOME || join(homedir(), ".cache"),
  "har-browse",
  "profile",
  profileName,
);

let server;

before(async () => {
  server = await spawnToyServer({
    port,
    directory: join(__dirname, "..", "toy_server"),
  });
});

after(() => {
  server?.kill();
  rmSync(profileDir, { recursive: true, force: true });
});

test("har-browse | head -n 1 exits cleanly", { timeout: 60000 }, async () => {
  // sh-built pipeline so the OS pipe is direct between har-browse and
  // head — no Node mediation that could keep the pipe alive after head
  // exits.
  const bin = join(__dirname, "..", "src", "har_browse.mjs");
  const cmd = `node ${JSON.stringify(bin)} --profile ${profileName} http://127.0.0.1:${port}/ | head -n 1`;
  const { stdout, stderr } = await exec("sh", ["-c", cmd], { timeout: 30000 });

  const parsed = JSON.parse(stdout.trim());
  assert.ok(Object.keys(parsed).length > 0, "first line parses as non-empty JSON");
  assert.doesNotMatch(stderr, /Error: write EPIPE/);
  assert.doesNotMatch(stderr, /Unhandled 'error' event/);
});
