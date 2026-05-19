import { spawn } from "node:child_process";

/**
 * Spawn `python3 -m http.server` on `port`, serving `directory`,
 * then poll until it answers a GET on `/`. Caller owns the lifetime
 * (kill the returned process when done).
 *
 * @param {object} args
 * @param {number} args.port
 * @param {string} args.directory - absolute path to serve
 * @param {number} [args.tries=50]
 * @param {number} [args.delayMs=100]
 * @returns {Promise<import("node:child_process").ChildProcess>}
 */
export async function spawnToyServer({ port, directory, tries = 50, delayMs = 100 }) {
  const proc = spawn(
    "python3",
    ["-m", "http.server", String(port), "--directory", directory],
    { stdio: "ignore" },
  );
  for (let i = 0; i < tries; i++) {
    try {
      if ((await fetch(`http://127.0.0.1:${port}/`)).ok) return proc;
    } catch {
      // not yet listening
    }
    await new Promise((r) => setTimeout(r, delayMs));
  }
  proc.kill();
  throw new Error(`toy server failed to start on :${port}`);
}
