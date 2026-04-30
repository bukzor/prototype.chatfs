# Design — chatfs-mockup-chatgpt

Decisions about the shape of the capture/splat/render pipeline and the CLI
surface that drives it.

## What belongs here

- CLI command structure (nouns, verbs, locator sub-nouns)
- Regeneration semantics (freshness, idempotence, fail-modes)
- Contracts between pipeline stages (what each stage may rely on, what it
  must not synthesize)

## What does NOT belong

- Implementation details of individual scripts (live in the scripts
  themselves or in devlogs)
- The specific filesystem layout under `chatfs.demo/` (parent
  `040-design.kb/rotate-90-degrees-layout.md` and `user-interface.kb/`)
