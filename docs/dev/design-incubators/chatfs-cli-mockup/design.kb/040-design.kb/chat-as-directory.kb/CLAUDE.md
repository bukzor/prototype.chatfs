# Chat as Directory — Sub-points

Aspects of the chat-as-directory layout that need durable rationale beyond
the headline storage-vs-view principle.

## What belongs here

- A specific facet of the layout that has design rationale (lifecycle splits
  inside `.chat/$UUID/`, mechanics of the front-door symlink, collision
  handling between view paths, etc.)
- Per-script implications when the layout drives a non-obvious script shape.

## What does NOT belong

- The headline storage-vs-view principle — see parent `chat-as-directory.md`.
- Cross-cutting rules followed in other contexts (deterministic regen,
  identity-scoped cleanup, partial-synthesis avoidance) — see sibling
  entries.
- Generic CLI command shape — see `cli-command-shape.md`.
- Implementation details of individual scripts — live in the scripts
  themselves or in devlogs.

## When to add

A new file when a layout aspect surfaces durable rationale (something
future sessions need to honor) that doesn't fit cleanly in one of the
existing files here. Transient implementation notes go in devlogs, not
here.
