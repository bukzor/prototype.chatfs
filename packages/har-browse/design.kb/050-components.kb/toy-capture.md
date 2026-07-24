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

# har-browse — Playwright CDP Capture Script

The primary learning target. A one-shot Playwright script that streams a
Chrome DevTools Protocol event trace.

> [!TODO] Playwright demoted to a dev/test-only dependency
> The production capture path runs on `puppeteer-core` (or its rust-port
> equivalent, chromiumoxide, should that venue win) rather than
> Playwright; Playwright remains only to drive the test suite's
> synthetic pages. Ratified 2026-07-23: a green-field survey
> (`../070-future-work.kb/capture-implementation-frontier.kb/`) found
> Playwright dominated on both owned-code and total-footprint axes by
> simpler production taps — its page-automation machinery earns its
> keep here mainly by being fought into behaving like a protocol tap.
> Tracked in `.claude/todo.kb/2026-07-23-002-*`; gated on that todo's
> host-seam precondition (an implementation step on
> `2026-07-23-000-*`) and timed by the `2026-07-23-001-*` venue spike.

## Interface

```
har-browse [URL] [--profile NAME] [--howto PATH] > events.jsonl
```

Defaults: URL `http://127.0.0.1:8000`, `--profile default_profile`.

Profile directory:
`${XDG_CACHE_HOME:-$HOME/.cache}/har-browse/profile/${profile}`.
State (cookies, localStorage, service workers) persists across runs, so
real-site logins only need to be completed once per profile.

## Output

JSONL on stdout. One line per CDP event, shaped `{method, params}` — the
wire format `chrome-har` and other CDP-consuming tools expect. Response
bodies are attached at `Network.responseReceived.params.response.body`
(with `.encoding = "base64"` when applicable).

A bonafide HAR document is one downstream pipeline step away:
`har-browse | node -e 'harFromMessages(...)' > capture.har`. No HAR
reconstruction logic lives in this repo.

## Behavior

1. Launch visible Chromium via `launchPersistentContext(profileDir, ...)`
   (always headful — human-in-the-loop)
2. Attach a CDP session per page; enable Network + Page domains
3. Register persistent overlay injection (survives navigations via `addInitScript`)
4. If `--howto` provided, overlay includes a collapsible instructions panel
5. Navigate to URL with `waitUntil: 'commit'` (returns as soon as the response
   begins — works on any site, including SPAs with SSE/websockets)
6. Human interacts with the site freely (login, navigate, scroll, etc.)
7. Terminate on one of two signals:
   - Human clicks "Done Capturing" → drain in-flight body fetches, close
     context, exit 0
   - Human closes the browser window → same drain + exit sequence

The injected button must persist across page navigations (login redirects,
multi-page flows). Real use cases involve 2FA, captcha, and multi-step login
before reaching the target content.

## Responsibilities

- Persistent-context lifecycle (per-profile state, CDP attach per page, close)
- Blanket CDP event passthrough in chrome-har-compatible shape
- Body attachment: hold `Network.responseReceived` per requestId, fetch
  body via `Network.getResponseBody` on `loadingFinished`, stash onto
  `params.response.body`, then emit in order
- Persistent UI overlay across navigations (the target page is not ours)

## Platform workarounds (Crostini)

Playwright's defaults conflict with ChromeOS's Crostini (Linux container):

- **`viewport: null`** — Playwright overrides the viewport to 1280x720 regardless
  of actual window size. On Crostini the physical window is smaller, pushing
  fixed-position elements off-screen. `null` lets the browser use its real size.
- **`ignoreDefaultArgs: ["--enable-unsafe-swiftshader"]`** — Playwright enables
  SwiftShader (software GL) by default. On Crostini this breaks Wayland fractional
  scaling: text stretches, mouse events land offset from visuals. Removing it lets
  Chromium use hardware GL via Sommelier.

## Reusable output

The browser lifecycle and CDP passthrough patterns transfer directly to real
BB1 capture scripts targeting external providers.
