---
why:
  - site-agnostic-capture
---

# Persistent Overlay Across Navigations

The injected "Done Capturing" button must survive page navigations. Real capture
sessions involve login flows (redirects), 2FA pages, and multi-step interactions
before reaching the target content. If the overlay disappears on navigation, the
human has no way to signal completion.

**Verification:** Navigate away from the initial page and back; the "Done
Capturing" button remains visible and functional throughout.
