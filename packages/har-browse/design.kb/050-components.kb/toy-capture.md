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
./src/har_browse.mjs [URL] [--har PATH] [--howto PATH]
```

Defaults: URL `http://127.0.0.1:8000`, `--har out.har`

## Behavior

1. Launch visible Chromium (always headful — human-in-the-loop)
2. Create browser context with HAR recording enabled
3. Register persistent overlay injection (survives navigations via `addInitScript`)
4. If `--howto` provided, overlay includes collapsible instructions panel
5. Navigate to `--url`
6. Human interacts with the site freely (login, navigate, scroll, etc.)
7. Human clicks "Done Capturing" when finished
8. Close context to finalize HAR
9. If human closes browser instead, exit cleanly ("Cancelled by user")

The injected button must persist across page navigations (login redirects,
multi-page flows). Real use cases involve 2FA, captcha, and multi-step login
before reaching the target content.

## Responsibilities

- Browser lifecycle (launch, context, close)
- HAR recording configuration and finalization
- Persistent UI overlay across navigations (the target page is not ours)
- Graceful cancellation when browser is closed by user

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
