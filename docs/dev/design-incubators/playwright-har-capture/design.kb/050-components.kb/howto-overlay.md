---
why:
  - site-agnostic-capture
  - persistent-overlay
---

# howto-overlay — Site-Specific Instructions for Human Operator

Future component. A `--howto instructions.md` flag would inject rendered markdown
instructions into the persistent capture overlay, guiding the human through
site-specific steps (e.g. "Log in, navigate to conversation X, click Done").

## Interface (proposed)

```
toy_capture --url <url> --har <path> --howto howto-claude.md [--headful]
```

## Rationale

The capture harness is site-agnostic (only the URL varies). But the human
operator may not know what steps a particular site requires. The howto overlay
bridges this gap without coupling the harness to any specific site — the
instructions are external content, not built-in logic.

## Status

Deferred. The basic "Done" button is sufficient for initial use cases where the
operator already knows the site.
