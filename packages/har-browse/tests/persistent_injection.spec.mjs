/**
 * Verify the "Done Capturing" button survives page navigations
 * and that double-`injectOverlay` calls don't duplicate the overlay.
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

test("Done click handler is registered { once: true } and removed after first fire", async ({
  browser,
  toyServer,
}) => {
  const context = await browser.newContext();
  try {
    const page = await context.newPage();
    await injectOverlay(page);
    await page.goto(toyServer.url, { waitUntil: "networkidle" });
    const session = await context.newCDPSession(page);
    // Resolve the #capture-done element to a remote-object handle.
    const { result: handle } = await session.send("Runtime.evaluate", {
      expression: `document.getElementById("capture-done")`,
    });
    expect(handle.objectId).toBeTruthy();
    const before = await session.send("DOMDebugger.getEventListeners", {
      objectId: handle.objectId,
    });
    expect(
      before.listeners.filter((l) => l.type === "click").length,
      "exactly one click listener registered before fire",
    ).toBe(1);

    await page.click("#capture-done");
    // The microtask queue may not drain immediately; wait one round.
    await page.waitForFunction(
      () => document.getElementById("capture-done")?.dataset.clicked === "true",
    );

    // Re-resolve the element (objectId may be invalidated by GC across awaits).
    const { result: handle2 } = await session.send("Runtime.evaluate", {
      expression: `document.getElementById("capture-done")`,
    });
    const after = await session.send("DOMDebugger.getEventListeners", {
      objectId: handle2.objectId,
    });
    expect(
      after.listeners.filter((l) => l.type === "click").length,
      "click listener auto-removes after first fire (once: true)",
    ).toBe(0);
  } finally {
    await context.close();
  }
});

test("injectOverlay is idempotent: double-register yields one overlay", async ({
  browser,
  toyServer,
}) => {
  // Two calls to injectOverlay register two init scripts; both fire on
  // every new document. The inject function's `getElementById` early
  // return is the only thing keeping the second invocation from
  // appending a second overlay/button/style.
  const context = await browser.newContext();
  try {
    const page = await context.newPage();
    await injectOverlay(page);
    await injectOverlay(page);
    await page.goto(toyServer.url, { waitUntil: "networkidle" });
    expect(await page.locator("#capture-overlay").count()).toBe(1);
    expect(await page.locator("#capture-done").count()).toBe(1);
  } finally {
    await context.close();
  }
});
