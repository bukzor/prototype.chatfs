import { test as base, expect } from "@playwright/test";
import { spawn } from "node:child_process";
import { mkdtempSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { startCapture as _startCapture } from "../src/capture.mjs";

const __dirname = dirname(fileURLToPath(import.meta.url));

export const test = base.extend({
  // One toy http.server per worker; ports separated by workerIndex.
  toyServer: [
    async ({}, use, workerInfo) => {
      const port = 9000 + workerInfo.workerIndex;
      const proc = spawn(
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
      let ready = false;
      for (let i = 0; i < 50; i++) {
        try {
          if ((await fetch(`http://127.0.0.1:${port}/`)).ok) {
            ready = true;
            break;
          }
        } catch {
          // not yet listening
        }
        await new Promise((r) => setTimeout(r, 100));
      }
      if (!ready) throw new Error(`toy server failed to start on :${port}`);
      try {
        await use({ port, url: `http://127.0.0.1:${port}` });
      } finally {
        proc.kill();
      }
    },
    { scope: "worker" },
  ],

  // Factory: tests call `await startCapture({ url, ... })`. Cleanup
  // (session.close + profile dir rm) happens after the test body.
  startCapture: async ({}, use) => {
    const sessions = [];
    const profileDirs = [];
    const factory = async (opts) => {
      const profileDir = mkdtempSync(join(tmpdir(), "har-browse-test-"));
      profileDirs.push(profileDir);
      const session = await _startCapture({
        profileDir,
        headless: true,
        ...opts,
      });
      sessions.push(session);
      return session;
    };
    try {
      await use(factory);
    } finally {
      for (const s of sessions) {
        try {
          await s.close();
        } catch {
          // best-effort cleanup
        }
      }
      for (const d of profileDirs) {
        rmSync(d, { recursive: true, force: true });
      }
    }
  },
});

export { expect };
