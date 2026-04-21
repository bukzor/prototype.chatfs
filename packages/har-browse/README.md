---
last-updated: 2026-04-21
---

# Playwright HAR Capture — Toy Project

Learn browser-driven HAR capture using Playwright against a local-only toy app.

## Intended use

Personal-scale capture of your own sessions (login → navigate → record) for
local archival and processing. Assumes you own the account, are acting at
human scale, and have read the target site's terms of service.

Not intended for: scraping third-party content, bulk account automation,
circumventing rate limits that apply to your account, or any task a target
site's anti-bot defenses are specifically designed to stop.

## Risks

**Terms of service.** Many sites prohibit or restrict browser automation
against their web interface, even for access to your own account's data.
Using this tool may violate those terms and put your account at risk of
restriction or termination. Read the ToS for your target site — this tool
does not read it for you.

**Anti-bot circumvention.** `src/capture.mjs` sets
`--disable-blink-features=AutomationControlled`, which hides the
`navigator.webdriver` signal (a W3C-spec property whose defined meaning is
"this browser is under automated control") from Cloudflare Turnstile and
similar detectors. This is a deliberate misrepresentation. It is
defensible only under the intended-use conditions above — not when the
detector is correctly identifying what you're actually doing.

**Secret material at rest.** The persistent profile directory
(`${XDG_CACHE_HOME:-$HOME/.cache}/har-browse/profile/*`) contains session
cookies and local storage for every site you've logged in through it.
Captured HAR files contain full request/response bodies including auth
headers, bearer tokens, and any payloads sent or received. Treat both
like password files: don't commit to git, don't share, don't sync to
cloud drives unencrypted.

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

### `har-browse`

Launches a visible Chromium browser via Playwright, navigates to a URL, and
records all network traffic to a HAR file. Injects a persistent "Done Capturing"
button that survives page navigations. The script blocks until the human either
clicks the button (success, exit 0) or closes the window (cancelled, exit 2).

```bash
har-browse [URL] [--har PATH] [--profile NAME] [--howto PATH]
```

Defaults: URL `http://127.0.0.1:8000`, `--har out.har`, `--profile default_profile`.

With `--howto`, a collapsible instructions panel appears in the overlay.

State (cookies, localStorage, service workers) persists across runs in
`${XDG_CACHE_HOME:-$HOME/.cache}/har-browse/profile/${profile}`, so real-site
logins only need to be completed once per profile. Pick distinct profile names
for distinct target sites (e.g. `--profile chatgpt`, `--profile claude`).

### `toy_pluck.sh`

Extracts `/api/conversation` responses from a HAR file via jq.
Reads HAR from stdin, writes JSON to stdout. Handles base64-encoded responses.

```bash
./toy_pluck.sh < out.har > extracted.json
```

### `src/test_persistent_injection.mjs`

Automated test that verifies the "Done Capturing" button survives multiple page
navigations. Spins up its own toy server, runs headless, and checks the HAR
contains expected entries. No manual interaction needed.

```bash
./src/test_persistent_injection.mjs
```

## Testing

```bash
./src/test_persistent_injection.mjs
```

## Usage

```bash
# Terminal 1: start the toy server
./toy_server/run.sh

# Terminal 2: capture, then extract
har-browse
./toy_pluck.sh < out.har > extracted.json
```
