---
why:
  - three-subsystem-pipeline
  - har-lifecycle
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
4. Inject a "capture refresh" button into the page via Playwright
5. Click the injected button to trigger additional network activity
6. Wait for network idle / specific request completion
7. Close context to finalize HAR
8. Exit 0 on success, nonzero on failure

## Responsibilities

- Browser lifecycle (launch, context, close)
- HAR recording configuration and finalization
- Injecting UI controls into the target page (the target page is not ours)
- Network idle detection
- Clean failure on timeout or navigation error

## Reusable output

The browser lifecycle and HAR recording patterns transfer directly to real
BB1 capture scripts targeting external providers.
