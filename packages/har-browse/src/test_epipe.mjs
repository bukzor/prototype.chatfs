#!/usr/bin/env node
/**
 * Verify the stdout-EPIPE guard in `har_browse.mjs` pattern:
 * - Downstream consumer closes its stdin (e.g. `head -n 1`, or jq with
 *   `limit`) before the producer finishes.
 * - Producer should exit quickly and quietly — no Node `Error: write EPIPE`
 *   stack trace on stderr.
 *
 * We test the pattern (not the browser-driving binary, which is hard to
 * run headlessly without human interaction) by running a small child
 * that replicates the guard: an error handler on stdout + a loop that
 * breaks when the flag is set.
 */
import { spawn } from "node:child_process";

const producerScript = `
  let stdoutClosed = false;
  process.stdout.on("error", (err) => {
    if (err.code === "EPIPE") stdoutClosed = true;
    else throw err;
  });
  (async () => {
    for (let i = 0; i < 10000; i++) {
      if (stdoutClosed) process.exit(0);
      process.stdout.write(JSON.stringify({ i }) + "\\n");
      // Yield occasionally so the EPIPE can propagate.
      if (i % 50 === 0) await new Promise((r) => setImmediate(r));
    }
  })();
`;

const producer = spawn("node", ["-e", producerScript], {
  stdio: ["ignore", "pipe", "pipe"],
});
const consumer = spawn("sed", ["-n", "1,1p"], {
  stdio: [producer.stdout, "pipe", "inherit"],
});

let consumerOut = "";
consumer.stdout.on("data", (d) => (consumerOut += d.toString()));

let producerErr = "";
producer.stderr.on("data", (d) => (producerErr += d.toString()));

const producerExit = new Promise((resolve) =>
  producer.on("exit", (code, signal) => resolve({ code, signal })),
);
const consumerExit = new Promise((resolve) =>
  consumer.on("exit", (code, signal) => resolve({ code, signal })),
);

const timeout = new Promise((_, reject) =>
  setTimeout(() => reject(new Error("timeout: producer did not exit")), 5000),
);

const [pRes] = await Promise.all([
  Promise.race([producerExit, timeout]),
  consumerExit,
]);

console.log("consumer out: " + JSON.stringify(consumerOut.trim()));
console.log("producer exit: " + JSON.stringify(pRes));
console.log(
  "producer stderr: " +
    JSON.stringify(producerErr.length ? producerErr.slice(0, 200) : ""),
);

const stderrClean =
  !producerErr.includes("EPIPE") && !producerErr.includes("Unhandled");
const firstLineReceived = /^\{"i":0\}$/.test(consumerOut.trim());
const producerExitedCleanly = pRes.code === 0;

const pass = stderrClean && firstLineReceived && producerExitedCleanly;
console.log(pass ? "PASS" : "FAIL");
if (!pass) process.exit(1);
