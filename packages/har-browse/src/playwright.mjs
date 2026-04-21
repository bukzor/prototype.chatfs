// Local-idiom wrapper on `playwright`. Inside this package, import
// `{ chromium } from "./playwright.mjs"` instead of `"playwright"`; the
// wrapper threads a branded User-Agent that matches the launch mode,
// applies our tell-hiding args, and sets Crostini-friendly defaults.
//
// Caller-supplied opts win: scalars override our defaults; arrays
// (`ignoreDefaultArgs`, `args`) have caller entries appended.
import * as playwright from "playwright";
import { userAgent } from "./user-agent.mjs";

export const chromium = {
  async launchPersistentContext(profileDir, opts = {}) {
    const headless = opts.headless ?? true;
    return playwright.chromium.launchPersistentContext(profileDir, {
      ...opts,
      headless,
      userAgent:
        opts.userAgent ?? (await userAgent(playwright.chromium, headless)),
      // Playwright defaults to a 1280x720 viewport override, which doesn't
      // match the physical window size on Crostini — fixed-position
      // elements render off-screen. `null` uses the actual window size.
      viewport: opts.viewport ?? null,
      ignoreDefaultArgs: [
        // Playwright defaults to SwiftShader (software GL) which breaks
        // Wayland fractional scaling on Crostini — text stretches, mouse
        // events offset from visuals. Removing it lets Chromium use
        // hardware GL via Sommelier.
        "--enable-unsafe-swiftshader",
        // Suppresses the "Chrome is being controlled by automated test
        // software" infobar and related automation-mode UI tells (password
        // manager / translate suppression). The automation itself is
        // CDP-driven and independent of this flag.
        "--enable-automation",
        ...(opts.ignoreDefaultArgs ?? []),
      ],
      args: [
        // Hides navigator.webdriver at the blink level. Empirically
        // required (in addition to --enable-automation stripping) to clear
        // Cloudflare Turnstile on cold logins.
        "--disable-blink-features=AutomationControlled",
        ...(opts.args ?? []),
      ],
    });
  },
};
