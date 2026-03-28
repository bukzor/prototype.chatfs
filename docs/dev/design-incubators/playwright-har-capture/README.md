---
last-updated: 2026-03-28
---

# Playwright HAR Capture — Toy Project

Learn browser-driven HAR capture using Playwright against a local-only toy app.

## Setup

```bash
# Install Node dependencies (from this directory)
pnpm install

# Install Playwright's Chromium (one-time, ~110MB)
npx playwright install chromium
```

On ChromeOS/Crostini: the outer Chrome is not accessible for automation.
Playwright needs its own Chromium inside the container.

## Scripts

### `toy_server/run.sh`

Starts a Python HTTP server serving static files from `toy_server/` on port 8000.
Provides the toy app (HTML/CSS/JS) and a fixed `/api/conversation` JSON fixture.

### `toy_capture/capture.mjs`

Launches a visible Chromium browser via Playwright, navigates to a URL, and
records all network traffic to a HAR file. Injects a persistent "Done Capturing"
button that survives page navigations. The script blocks until the human clicks
the button, then writes the HAR and exits.

```bash
./toy_capture/capture.mjs [URL] [--har PATH] [--howto PATH]
```

Defaults: URL `http://127.0.0.1:8000`, `--har out.har`

With `--howto`, a collapsible instructions panel appears in the overlay.

### `toy_pluck.sh`

Extracts `/api/conversation` responses from a HAR file via jq.
Reads HAR from stdin, writes JSON to stdout. Handles base64-encoded responses.

```bash
./toy_pluck.sh < out.har > extracted.json
```

### `toy_capture/test_persistent_injection.mjs`

Automated test that verifies the "Done Capturing" button survives multiple page
navigations. Spins up its own toy server, runs headless, and checks the HAR
contains expected entries. No manual interaction needed.

```bash
./toy_capture/test_persistent_injection.mjs
```

## Testing

```bash
./toy_capture/test_persistent_injection.mjs
```

## Usage

```bash
# Terminal 1: start the toy server
./toy_server/run.sh

# Terminal 2: capture, then extract
./toy_capture/capture.mjs
./toy_pluck.sh < out.har > extracted.json
```
