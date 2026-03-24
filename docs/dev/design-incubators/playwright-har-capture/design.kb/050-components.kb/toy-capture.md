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
4. Trigger the "refresh conversation" button (or reload)
5. Wait for network idle / specific request completion
6. Close context to finalize HAR
7. Exit 0 on success, nonzero on failure

## Responsibilities

- Browser lifecycle (launch, context, close)
- HAR recording configuration and finalization
- Network idle detection
- Clean failure on timeout or navigation error

## Reusable output

The browser lifecycle and HAR recording patterns transfer directly to real
BB1 capture scripts targeting external providers.
