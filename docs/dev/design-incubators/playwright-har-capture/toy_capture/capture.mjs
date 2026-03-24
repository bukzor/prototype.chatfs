import { chromium } from "playwright";
import { parseArgs } from "node:util";

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

await context.close();
await browser.close();

console.error(`HAR written to ${values.har}`);
