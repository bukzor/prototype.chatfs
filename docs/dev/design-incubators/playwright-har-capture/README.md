---
last-updated: 2026-03-24
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

## Usage

```bash
# Terminal 1: start the toy server
toy_server/start.sh

# Terminal 2: capture a HAR
toy_capture/run.sh http://127.0.0.1:8000 out.har
```
