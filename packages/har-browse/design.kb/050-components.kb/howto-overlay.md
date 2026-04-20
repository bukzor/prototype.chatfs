---
why:
  - site-agnostic-capture
  - persistent-overlay
---

# howto-overlay — Site-Specific Instructions for Human Operator

A `--howto instructions.md` flag injects plaintext instructions into the
persistent capture overlay, guiding the human through site-specific steps
(e.g. "Log in, navigate to conversation X, click Done").

## Interface

```
har-browse --howto howto-example.md
```

When `--howto` is provided, the overlay includes a collapsible `<details>`
panel showing the file contents as plaintext. The panel starts open so the
operator sees instructions immediately, and can collapse it to access the
underlying page.

## Overlay UX

- Collapsible instructions via native `<details>` element (no JS needed)
- Draggable via a dot-grid grip handle on the left edge (CSS visual, JS drag)
- 80% opacity, full on hover
- Hidden entirely when `--howto` is not provided

## Rationale

The capture harness is site-agnostic (only the URL varies). But the human
operator may not know what steps a particular site requires. The howto overlay
bridges this gap without coupling the harness to any specific site — the
instructions are external content, not built-in logic.
