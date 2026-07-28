#!/usr/bin/env node
// @ts-check
// What does each way of hiding the window cost us on the wire?
//
//   ./headless-changes-the-agent.mjs
//
// The instrument behind the sibling `headless-changes-the-agent.md`.
// Every row launches the same pinned Chromium and reads the properties
// a site can see, so the table answers one question: which of these is
// still the browser we ship?
//
// `WINDOWLESS_ARGS` is imported rather than restated, so the row
// labelled "windowless" is the configuration the host actually uses and
// cannot drift from it.
//
// Costs four browser launches and a few seconds. Two of them open a
// visible window -- that is the point of the comparison.
import puppeteer from "puppeteer-core";
import { chromium as pwChromium } from "playwright-core";
import { chromium } from "../../../src/playwright.mjs";
import { WINDOWLESS_ARGS } from "../../../src/host_puppeteer.mjs";
import { mkdtempSync } from "node:fs";
import { tmpdir } from "node:os";

/** Read everything a site could compare against a real browser. */
const PROBE = () => ({
  ua: navigator.userAgent,
  brands: /** @type {any} */ (navigator)
    .userAgentData.brands.map((b) => `"${b.brand}";v="${b.version}"`)
    .join(", "),
  screen: `${screen.width}x${screen.height}`,
  viewport: `${innerWidth}x${innerHeight}`,
  webgl: (() => {
    const gl = document.createElement("canvas").getContext("webgl");
    const ext = gl?.getExtension("WEBGL_debug_renderer_info");
    return ext ? String(gl?.getParameter(ext.UNMASKED_RENDERER_WEBGL)) : "n/a";
  })(),
});

/** @param {import("puppeteer-core").Page | import("playwright-core").Page} page */
async function probe(page) {
  const info = await page.evaluate(PROBE);
  const raf = await page.evaluate(
    () =>
      new Promise((resolve) => {
        const t = setTimeout(() => resolve("NO"), 2000);
        requestAnimationFrame(() => {
          clearTimeout(t);
          resolve("yes");
        });
      }),
  );
  return { ...info, raf };
}

/** @param {{headless?: boolean, args?: string[]}} opts */
async function viaPuppeteer({ headless = false, args = [] }) {
  const browser = await puppeteer.launch({
    executablePath: pwChromium.executablePath(),
    userDataDir: mkdtempSync(`${tmpdir()}/hcta-`),
    headless,
    networkEnabled: false,
    defaultViewport: null,
    args,
  });
  try {
    const page = await browser.newPage();
    await page.goto("file:");
    return await probe(page);
  } finally {
    await browser.close();
  }
}

/** @param {boolean} headless */
async function viaPlaywright(headless) {
  const context = await chromium.launchPersistentContext(
    mkdtempSync(`${tmpdir()}/hcta-pw-`),
    { headless },
  );
  try {
    const page = await context.newPage();
    await page.goto("file:");
    return await probe(page);
  } finally {
    await context.close();
  }
}

const ROWS = [
  ["puppeteer headful (control)", () => viaPuppeteer({})],
  ["puppeteer, Chromium --headless", () => viaPuppeteer({ headless: true })],
  ["playwright --headless", () => viaPlaywright(true)],
  ["windowless (what we ship)", () => viaPuppeteer({ args: WINDOWLESS_ARGS })],
];

for (const [label, run] of ROWS) {
  const r = await run();
  console.log(label);
  console.log(`   UA        ${r.ua}`);
  console.log(`   CH        ${r.brands}`);
  console.log(`   screen    ${r.screen}      viewport ${r.viewport}`);
  console.log(`   raf       ${r.raf}`);
  console.log(`   webgl     ${r.webgl}\n`);
}
