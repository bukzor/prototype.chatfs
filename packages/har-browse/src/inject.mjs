import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const injectHTML = readFileSync(join(__dirname, "inject.html"), "utf-8");
const injectCSS = readFileSync(join(__dirname, "inject.css"), "utf-8");

/**
 * Register persistent overlay injection on a Playwright page.
 *
 * @param {import('playwright').Page} page
 * @param {{ howto?: string }} [opts]
 */
export async function injectOverlay(page, { howto } = {}) {
  await page.addInitScript(
    ({ html, css, howto }) => {
      function inject() {
        if (document.getElementById("capture-overlay")) return;
        const style = document.createElement("style");
        style.textContent = css;
        document.head.appendChild(style);
        // Sites enforcing `require-trusted-types-for 'script'` (e.g.
        // aistudio.google.com) reject a raw-string insertAdjacentHTML,
        // throwing and silently aborting the rest of inject() -- the
        // style lands (textContent isn't a guarded sink) but the
        // overlay never does. `html` is fixed, locally-authored markup
        // (no attacker/page-controlled input), so a pass-through policy
        // is safe here.
        // `@types/trusted-types` isn't in the dependency tree and this
        // is the only Trusted Types touch-point, so cast narrowly here
        // rather than add ambient global types for one call site.
        const trustedTypes = /** @type {any} */ (window).trustedTypes;
        const trustedHtml = trustedTypes
            ?.createPolicy("har-browse-inject", {
              createHTML: (/** @type {string} */ s) => s,
            })
            .createHTML(html) ?? html;
        document.body.insertAdjacentHTML("beforeend", trustedHtml);
        const howtoEl = document.getElementById("capture-howto");
        if (howto) {
          document.getElementById("capture-howto-content").textContent = howto;
        } else {
          howtoEl.hidden = true;
        }
        const overlay = document.getElementById("capture-overlay");
        const handle = document.getElementById("capture-drag-handle");
        let dragging = false,
          dx = 0,
          dy = 0;
        handle.addEventListener("mousedown", (e) => {
          dragging = true;
          const rect = overlay.getBoundingClientRect();
          dx = e.clientX - rect.left;
          dy = e.clientY - rect.top;
          overlay.style.left = rect.left + "px";
          overlay.style.top = rect.top + "px";
          overlay.style.right = "auto";
        });
        document.addEventListener("mousemove", (e) => {
          if (!dragging) return;
          overlay.style.left = e.clientX - dx + "px";
          overlay.style.top = e.clientY - dy + "px";
        });
        document.addEventListener("mouseup", () => {
          dragging = false;
        });

        document.getElementById("capture-done").addEventListener(
          "click",
          (e) => {
            /** @type {HTMLElement} */ (e.target).dataset.clicked = "true";
          },
          { once: true },
        );
      }
      if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", inject);
      } else {
        inject();
      }
    },
    { html: injectHTML, css: injectCSS, howto },
  );
}
