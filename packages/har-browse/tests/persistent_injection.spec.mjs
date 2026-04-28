/**
 * Verify the "Done Capturing" button survives page navigations.
 * Drives Playwright through 3 navigations against the toy server,
 * clicks the button, and checks the HAR has api/conversation entries.
 */
import { readFileSync } from "node:fs";
import { test, expect } from "./fixtures.mjs";
import { injectOverlay } from "../src/inject.mjs";

test("Done Capturing button survives navigations", async (
  { browser, toyServer },
  testInfo,
) => {
  const harPath = testInfo.outputPath("test.har");
  const context = await browser.newContext({
    recordHar: { path: harPath, mode: "full" },
  });
  try {
    const page = await context.newPage();
    await injectOverlay(page);

    await page.goto(toyServer.url, { waitUntil: "networkidle" });
    expect(await page.locator("#capture-done").count()).toBe(1);

    await page.goto(`${toyServer.url}/index.html`, { waitUntil: "networkidle" });
    expect(await page.locator("#capture-done").count()).toBe(1);

    await page.goto(`${toyServer.url}/`, { waitUntil: "networkidle" });
    expect(await page.locator("#capture-done").count()).toBe(1);

    await page.click("#capture-done");
    expect(
      await page.evaluate(
        () => document.getElementById("capture-done")?.dataset.clicked,
      ),
    ).toBe("true");

    await page.waitForFunction(
      () => document.getElementById("capture-done")?.dataset.clicked === "true",
      { timeout: 5000 },
    );
  } finally {
    await context.close();
  }

  const har = JSON.parse(readFileSync(harPath, "utf-8"));
  const apiEntries = har.log.entries.filter((e) =>
    e.request.url.includes("/api/conversation"),
  );
  expect(apiEntries.length).toBeGreaterThanOrEqual(1);
});
