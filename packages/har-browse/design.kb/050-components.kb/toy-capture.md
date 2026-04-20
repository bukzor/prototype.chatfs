---
why:
  - three-subsystem-pipeline
  - har-lifecycle
  - persistent-overlay
  - site-agnostic-capture
---

# har-browse — Playwright HAR Capture Script

The primary learning target. A one-shot Playwright script that captures a HAR.

## Interface

```
har-browse [URL] [--har PATH] [--profile NAME] [--howto PATH]
```

Defaults: URL `http://127.0.0.1:8000`, `--har out.har`, `--profile default_profile`.

Profile directory:
`${XDG_CACHE_HOME:-$HOME/.cache}/har-browse/profile/${profile}`.
State (cookies, localStorage, service workers) persists across runs, so
real-site logins only need to be completed once per profile.

## Behavior

1. Launch visible Chromium via `launchPersistentContext(profileDir, ...)`
   (always headful — human-in-the-loop)
2. Register persistent overlay injection (survives navigations via `addInitScript`)
3. If `--howto` provided, overlay includes a collapsible instructions panel
4. Navigate to URL with `waitUntil: 'commit'` (returns as soon as the response
   begins — works on any site, including SPAs with SSE/websockets)
5. Human interacts with the site freely (login, navigate, scroll, etc.)
6. Terminate on one of two signals:
   - Human clicks "Done Capturing" → `context.close()` flushes HAR, exit 0
   - Human closes the browser window → log "Cancelled by user.", exit 2

The injected button must persist across page navigations (login redirects,
multi-page flows). Real use cases involve 2FA, captcha, and multi-step login
before reaching the target content.

## Responsibilities

- Persistent-context lifecycle (per-profile state, HAR recording, close)
- HAR recording configuration and finalization
- Persistent UI overlay across navigations (the target page is not ours)
- Distinguishing success (done-click) from cancellation (window-close) via
  exit code, so `&&`-chained pipelines halt on cancel

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

The browser lifecycle and HAR recording patterns transfer directly to real
BB1 capture scripts targeting external providers.
