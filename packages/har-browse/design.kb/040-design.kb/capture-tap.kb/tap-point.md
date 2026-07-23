---
why:
  - capture-everything
  - unblocked-sessions
---

# Tap Point: Browser DevTools Protocol on a Spawned, Human-Driven Browser

Capture attaches via CDP to a spawned Chromium instance the human drives
directly, observing every target the session opens. The protocol tap
gives an "if it was transferred, we observed it" guarantee — including
cache-served responses — without touching the byte path, so the
session keeps the browser's native TLS/HTTP fingerprint. A dedicated
managed profile (persisted per `--profile`) keeps logins across runs
without touching the user's daily browser.

**Why not a MITM proxy.** Bodies arrive inline — attractive, since the
in-flight body-fetch machinery would dissolve — but the proxy's TLS
fingerprint is not the browser's, a blocking risk on exactly the sites
this tool targets, and cache-served responses never cross the wire: a
silent completeness hole.

**Why not in-page fetch/XHR wrapping.** Misses workers, WebSockets,
navigations, and any transport the wrapper doesn't cover — a
silent-miss risk directly against capture-everything.

**Why not the browser's own batch HAR recorder.** Written at context
close; a crash mid-session loses the entire capture.

**Deferred alternative — extension + `chrome.debugger`.** The same CDP
tap, inside the user's daily browser: native fingerprint, existing
logins, nothing to launch. A viable future shape; costs extension
packaging and MV3 service-worker lifecycle quirks.
