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

/** @type {Awaited<ReturnType<typeof spawnToyServer>> | undefined} */
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

test("har-browse | head -n 1 exits cleanly", { timeout: 25000 }, async () => {
  // sh-built pipeline so the OS pipe is direct between har-browse and
  // head — no Node mediation that could keep the pipe alive after head
  // exits.
  //
  // `timeout(1)` is the outer guard: by default it runs the command in
  // a fresh process group and signals the whole group when the timer
  // fires, so a misbehaving har-browse (e.g. one that never emits a
  // newline) tears down with Chromium rather than leaving an orphan
  // window for the user to close manually. SIGTERM only — Chromium
  // handles it cleanly; SIGKILL would forfeit the cleanup we want.
  //
  // `--headless` is the CLI's windowless mode: no visible surface, but
  // the same browser and the same User-Agent (see `startCapture`'s
  // `windowless`). Not Chromium's headless mode, which this package
  // does not use anywhere.
  //
  // Budget: 4.30/4.31/4.38s over three standalone headed runs on
  // Crostini. The old 5s guard was the cause of this test's
  // intermittent failures, and Chromium's headless was never the cure --
  // it measured 4.6-4.7s, *slower*, so 5s was marginal either way. 15s
  // is ~3.5x the measured cost, which is right for a guard whose job is
  // catching an infinite hang: a tight budget buys nothing here and
  // costs flakes.
  const bin = join(__dirname, "..", "src", "har_browse.mjs");
  const cmd = `node ${JSON.stringify(bin)} --headless --profile ${profileName} http://127.0.0.1:${port}/ | head -n 1`;
  const { stdout, stderr } = await exec(
    "timeout",
    ["15s", "sh", "-c", cmd],
    { timeout: 20000 },
  );

  const parsed = JSON.parse(stdout.trim());
  assert.ok(Object.keys(parsed).length > 0, "first line parses as non-empty JSON");
  assert.doesNotMatch(stderr, /Error: write EPIPE/);
  assert.doesNotMatch(stderr, /Unhandled 'error' event/);
});
