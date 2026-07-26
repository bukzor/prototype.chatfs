---
why:
  - three-subsystem-pipeline
  - tap-point
  - record-format
  - marks
  - capture-cut-completeness
  - in-flow-termination
  - site-agnostic-capture
---

# har-browse — CDP Capture Script

The primary learning target. A one-shot script that streams a Chrome
DevTools Protocol event trace from a spawned, human-driven browser.

The production host is `puppeteer-core` on a spawned Chromium
(`src/host_puppeteer.mjs`), per the 2026-07-23 frontier ratification
(`../070-future-work.kb/capture-implementation-frontier.kb/`): a small
CDP library beats both a hand-rolled client (owned lines) and a full
automation framework (middleware footprint) for a tap whose page
automation goes unused — the human drives. Playwright remains a
devDependency only, driving the test suite through its own shell
(`src/host_playwright.mjs`); both shells serve the venue-agnostic
capture core (`src/capture.mjs`) through its `CaptureHost` seam, and
`tests/import_graph.test.mjs` holds the production path
playwright-free.

## Interface

```
har-browse [URL] [--profile NAME] [--howto PATH] [--keep-origin-storage] [--headless] > events.jsonl
```

Defaults: URL `http://127.0.0.1:8000`, `--profile default_profile`.

Profile directory:
`${XDG_CACHE_HOME:-$HOME/.cache}/har-browse/profile/${profile}`.
State (cookies, localStorage, service workers) persists across runs, so
real-site logins only need to be completed once per profile.

Browser executable: `$HAR_BROWSE_BROWSER` if set, else Playwright's
pinned Chromium (shared with the test suite, so captures and tests run
one browser revision).

## Output

JSONL on stdout. One line per CDP event, shaped `{method, params}` — the
wire format `chrome-har` and other CDP-consuming tools expect. Response
bodies are attached at `Network.responseReceived.params.response.body`
(with `.encoding = "base64"` when applicable).

A bonafide HAR document is one downstream pipeline step away:
`har-browse | node -e 'harFromMessages(...)' > capture.har`. No HAR
reconstruction logic lives in this repo.

## Behavior

1. Launch visible Chromium with a persistent `userDataDir`
   (headful by default — human-in-the-loop)
2. Attach a CDP session per page; enable Network + Page domains; brand
   the session's User-Agent (`ToolName/Version (+URL)` suffix)
3. Register persistent overlay injection (survives navigations via
   new-document init script)
4. If `--howto` provided, overlay includes a collapsible instructions panel
5. Clear the target origin's IndexedDB/Cache Storage (unless
   `--keep-origin-storage`), then navigate via raw `Page.navigate` —
   returns as soon as navigation starts, so any site works, including
   SPAs holding SSE/websockets
6. Human interacts with the site freely (login, navigate, scroll, etc.)
7. Terminate on one of two signals:
   - Human clicks "Done Capturing" → drain in-flight body fetches, close
     browser, exit 0
   - Human closes the browser window → same drain + exit sequence

The injected button must persist across page navigations (login redirects,
multi-page flows). Real use cases involve 2FA, captcha, and multi-step login
before reaching the target content.

## Responsibilities

- Browser lifecycle (per-profile `userDataDir`, CDP attach per page, close)
- Blanket CDP event passthrough in chrome-har-compatible shape
- Body attachment: hold `Network.responseReceived` per requestId, fetch
  body via `Network.getResponseBody` on `loadingFinished`, stash onto
  `params.response.body`, then emit in order
- Persistent UI overlay across navigations (the target page is not ours)

## Platform notes (Crostini)

- **`defaultViewport: null`** — a fixed viewport override doesn't match
  the physical window size on Crostini, pushing fixed-position elements
  off-screen; `null` uses the real window size.
- **Stealth pair** — `ignoreDefaultArgs: ["--enable-automation"]` plus
  `--disable-blink-features=AutomationControlled`: no automation
  infobar, `navigator.webdriver === false` (empirically required to
  clear Cloudflare Turnstile on cold logins).
- The test shell (`src/playwright.mjs`) additionally strips
  Playwright's SwiftShader default, which breaks Wayland fractional
  scaling under Sommelier.

## Reusable output

The browser lifecycle and CDP passthrough patterns transfer directly to real
BB1 capture scripts targeting external providers.
