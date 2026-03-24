import { chromium } from "playwright";
import { parseArgs } from "node:util";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const injectHTML = readFileSync(join(__dirname, "inject.html"), "utf-8");
const injectCSS = readFileSync(join(__dirname, "inject.css"), "utf-8");

const { values } = parseArgs({
  options: {
    url: { type: "string" },
    har: { type: "string" },
    headful: { type: "boolean", default: false },
  },
});

if (!values.url || !values.har) {
  console.error("Usage: toy_capture --url <url> --har <path> [--headful]");
  process.exit(1);
}

const browser = await chromium.launch({ headless: !values.headful });
const context = await browser.newContext({
  recordHar: { path: values.har, mode: "full" },
});
const page = await context.newPage();

await page.goto(values.url, { waitUntil: "networkidle" });
console.error("Page loaded.");

// Inject capture UI into the page
await page.evaluate(({ html, css }) => {
  const style = document.createElement("style");
  style.textContent = css;
  document.head.appendChild(style);
  document.body.insertAdjacentHTML("beforeend", html);
  document.getElementById("capture-done").addEventListener(
    "click", (e) => { e.target.dataset.clicked = "true"; }, { once: true },
  );
}, { html: injectHTML, css: injectCSS });
console.error("Waiting for human to click 'Done Capturing'...");

// Wait for the human to click — no timeout
await page.waitForFunction(
  () => document.getElementById("capture-done")?.dataset.clicked === "true",
  { timeout: 0 },
);

await context.close();
await browser.close();

console.error(`HAR written to ${values.har}`);
