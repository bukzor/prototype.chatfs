---
why:
  - three-subsystem-pipeline
  - har-lifecycle
  - persistent-overlay
  - site-agnostic-capture
---

# toy_capture — Playwright HAR Capture Script

The primary learning target. A one-shot Playwright script that captures a HAR.

## Interface

```
toy_capture --url http://127.0.0.1:8000 --har out.har [--outdir artifacts/] [--headful]
```

## Behavior

1. Launch Chromium (headful or headless per flag)
2. Create browser context with HAR recording enabled
3. Navigate to `--url`
4. Inject a persistent "Done Capturing" button into the page
5. Human interacts with the site freely (login, navigate, scroll, etc.)
6. Human clicks "Done Capturing" when finished
7. Close context to finalize HAR
8. Exit 0 on success, nonzero on failure

The injected button must persist across page navigations (login redirects,
multi-page flows). Real use cases involve 2FA, captcha, and multi-step login
before reaching the target content.

## Responsibilities

- Browser lifecycle (launch, context, close)
- HAR recording configuration and finalization
- Persistent UI overlay across navigations (the target page is not ours)
- Clean failure on timeout or navigation error

## Reusable output

The browser lifecycle and HAR recording patterns transfer directly to real
BB1 capture scripts targeting external providers.
