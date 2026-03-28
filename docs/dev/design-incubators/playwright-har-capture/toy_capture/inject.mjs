import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const injectHTML = readFileSync(join(__dirname, "inject.html"), "utf-8");
const injectCSS = readFileSync(join(__dirname, "inject.css"), "utf-8");

/** Register persistent overlay injection on a Playwright page. */
export async function injectOverlay(page) {
  await page.addInitScript(({ html, css }) => {
    function inject() {
      if (document.getElementById("capture-overlay")) return;
      const style = document.createElement("style");
      style.textContent = css;
      document.head.appendChild(style);
      document.body.insertAdjacentHTML("beforeend", html);
      document.getElementById("capture-done").addEventListener(
        "click",
        (e) => {
          e.target.dataset.clicked = "true";
        },
        { once: true },
      );
    }
    if (document.readyState === "loading") {
      document.addEventListener("DOMContentLoaded", inject);
    } else {
      inject();
    }
  }, { html: injectHTML, css: injectCSS });
}
