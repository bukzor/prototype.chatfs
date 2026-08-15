#!/usr/bin/env node
// @ts-check
// Re-measurement instrument for wayland-window-control-is-compositor-owned.md.
// Each trial is a live, human-observed pass: watch the window and report
// what you actually saw (or typed) -- there is no automated pass/fail,
// CDP itself lies about some of these (position acks success but the
// window never moves).
//
//   ./probe-window-control.mjs
//
// Visual trials paint a full-viewport page naming the expected state
// ("HIDDEN-FAILED-if-visible" / "REVEALED-OK"); the focus trial shows an
// auto-focused input box with a live readout of anything typed into it.
import puppeteer from "puppeteer-core";
import { chromium as pwChromium } from "playwright-core";
import { mkdtempSync } from "node:fs";
import { tmpdir } from "node:os";

const HOLD_MS = 4000;
const FOCUS_HOLD_MS = 15000;
const log = (msg) => console.log(`[${new Date().toISOString()}] ${msg}`);

function colorPage(trial, phase, bg) {
  return (
    "data:text/html," +
    encodeURIComponent(
      `<title>${trial}-${phase}</title><body style="margin:0;background:${bg};font:50px sans-serif">${phase} (trial: ${trial})</body>`,
    )
  );
}

function focusPage(label) {
  return (
    "data:text/html," +
    encodeURIComponent(
      `<title>${label}</title><body style="margin:0;background:#222;color:#0f0;font:24px monospace;padding:20px">
        <div>${label} -- keep typing elsewhere (this chat / your terminal), do NOT click this window.</div>
        <div>if your keystrokes land here instead, focus was stolen.</div>
        <input id="in" autofocus style="font-size:24px;width:90%;margin-top:20px">
        <div id="log" style="margin-top:20px;white-space:pre-wrap"></div>
        <script>
          document.getElementById('in').addEventListener('input', e => {
            document.getElementById('log').textContent = 'captured: ' + JSON.stringify(e.target.value);
          });
        </script>`,
    )
  );
}

async function countdown(n = 3) {
  for (let i = n; i >= 1; i--) {
    log(`starting in ${i}...`);
    await new Promise((r) => setTimeout(r, 1000));
  }
}

async function launch(extraArgs = [], extraOpts = {}) {
  return puppeteer.launch({
    executablePath: pwChromium.executablePath(),
    userDataDir: mkdtempSync(`${tmpdir()}/pwwc-`),
    headless: false,
    networkEnabled: false,
    defaultViewport: null,
    ignoreDefaultArgs: ["--enable-automation"],
    args: extraArgs,
    ...extraOpts,
  });
}

/** Don't await: some window-state changes never ack in this environment. */
function fireAndForget(session, windowId, bounds, label) {
  session
    .send(/** @type {any} */ ("Browser.setWindowBounds"), { windowId, bounds })
    .then(() => log(`  (ack: ${label})`))
    .catch((e) => log(`  (never acked / rejected: ${label}: ${e.message})`));
}

// --- Trial: position (--window-position flag + CDP setWindowBounds) ---
async function trialPosition() {
  log("=== trial: position (off-screen, then on-screen) ===");
  const browser = await launch(["--window-position=-32000,-32000"]);
  try {
    const pg = (await browser.pages())[0] ?? (await browser.newPage());
    const session = await pg.createCDPSession();
    const { windowId } = await session.send(/** @type {any} */ ("Browser.getWindowForTarget"), {});
    await session
      .send(/** @type {any} */ ("Browser.setWindowBounds"), {
        windowId,
        bounds: { left: -32000, top: -32000, windowState: "normal" },
      })
      .catch((e) => log(`  (setWindowBounds off-screen rejected: ${e.message})`));

    await pg.goto(colorPage("position", "HIDDEN-FAILED-if-visible", "crimson"));
    log(`  holding ${HOLD_MS}ms -- watch now (expect: nothing, window off-screen)`);
    await new Promise((r) => setTimeout(r, HOLD_MS));

    await session
      .send(/** @type {any} */ ("Browser.setWindowBounds"), {
        windowId,
        bounds: { left: 200, top: 200, windowState: "normal" },
      })
      .catch((e) => log(`  (setWindowBounds on-screen rejected: ${e.message})`));
    await pg.goto(colorPage("position", "REVEALED-OK", "seagreen"));
    await pg.bringToFront();
    log(`  holding ${HOLD_MS}ms -- watch now (phase: revealed)`);
    await new Promise((r) => setTimeout(r, HOLD_MS));
  } finally {
    await browser.close().catch(() => {});
  }
}

// --- Trial: minimize (fire-and-forget CDP minimize, then un-minimize) ---
async function trialMinimize() {
  log("=== trial: minimize (fire-and-forget) ===");
  const browser = await launch();
  try {
    const pg = (await browser.pages())[0] ?? (await browser.newPage());
    const session = await pg.createCDPSession();
    const { windowId } = await session.send(/** @type {any} */ ("Browser.getWindowForTarget"), {});

    fireAndForget(session, windowId, { windowState: "minimized" }, "minimize");
    await pg.goto(colorPage("minimize", "HIDDEN-FAILED-if-visible", "crimson"));
    log(`  holding ${HOLD_MS}ms -- watch now (phase: hidden / should be minimized)`);
    await new Promise((r) => setTimeout(r, HOLD_MS));

    fireAndForget(session, windowId, { windowState: "normal" }, "restore");
    await pg.goto(colorPage("minimize", "REVEALED-OK", "seagreen"));
    await pg.bringToFront();
    log(`  holding ${HOLD_MS}ms -- watch now (phase: revealed -- expect this to FAIL, per xdg-shell spec)`);
    await new Promise((r) => setTimeout(r, HOLD_MS));
  } finally {
    await browser.close().catch(() => {});
  }
}

// --- Trial: focus-steal (Target.createTarget background:true + --no-startup-window) ---
async function trialFocus() {
  log("=== trial: focus-steal (createTarget background:true, --no-startup-window) ===");
  const browser = await launch(["--no-startup-window"], { waitForInitialPage: false });
  try {
    await new Promise((r) => setTimeout(r, 1500));
    const created = new Promise((resolve) =>
      browser.once("targetcreated", async (t) => resolve(await t.page())),
    );
    const session = await browser.target().createCDPSession();
    await session.send(/** @type {any} */ ("Target.createTarget"), {
      url: focusPage("focus-steal"),
      newWindow: true,
      background: true,
    });
    const page = /** @type {any} */ (await created);
    if (!page) throw new Error("targetcreated fired but .page() was null");

    log(`  holding ${FOCUS_HOLD_MS}ms -- type elsewhere now (this chat / your terminal), don't touch the new window`);
    await new Promise((r) => setTimeout(r, FOCUS_HOLD_MS));

    const captured = await page
      .$eval("#in", /** @param {any} el */ (el) => el.value)
      .catch((e) => `<eval failed, browser/frame likely already torn down: ${e.message}>`);
    log(`  RESULT captured.value = ${JSON.stringify(captured)}`);
  } finally {
    await browser.close().catch(() => {});
  }
}

await countdown();
await trialPosition();
await trialMinimize();
await trialFocus();
log("all trials done");
