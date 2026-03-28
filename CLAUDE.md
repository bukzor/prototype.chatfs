--- # workaround: anthropics/claude-code#13003
depends:
  - skills/llm-collab
  - skills/llm-subtask
  - skills/llm.kb
---

# chatfs - Development Guide for Claude

## Architecture Overview

chatfs provides lazy filesystem access to chat conversations (claude.ai, ChatGPT). Polyglot Python/Rust repo.

**Pipeline:** Browser-driven capture (BB1) → extraction (BB2) → rendering (BB3). See `docs/dev/design/040-design.kb/black-box-decomposition.md`.

**Rust side:** `chatfs-fuser` crate — FUSE filesystem daemon. Cargo workspace at repo root.

**Node/Playwright side:** Browser automation for HAR capture (BB1). See `docs/dev/design-incubators/playwright-har-capture/`.

**Why JSONL:** Streaming-friendly, works with Unix tools now, easy capnproto migration later.

## Design Knowledge

- `docs/dev/design/` — Layered design.kb (mission → goals → requirements → design → future work)
- `docs/dev/background.kb/` — Technology primers, prior art
- `docs/dev/technical-policy.kb/` — Cross-cutting normative guidance (7 invariants, opaque extractor boundary, etc.)
- `docs/dev/design-incubators/` — Active design explorations with prototypes

For how to create and maintain design knowledge, see `Skill(llm-design-kb)`.

## Key Files

- `packages/` — Polyglot workspace members (Python packages, Rust crates)
- `docs/dev/design/` — Project-level design knowledge (design.kb)
- `docs/dev/design-incubators/playwright-har-capture/` — BB1 capture learning (Playwright HAR)
- `docs/dev/design-incubators/fuser-vfs/` — FUSE filesystem learning
- `docs/dev/design-incubators/fork-representation/` — Fork representation investigation
- `docs/dev/devlog/` — Session narrative history

## Working on Documentation

**Documentation editing principles:**

- **80% confidence threshold** — Make edits when reasonably confident. Edit first, discuss if uncertain.
- **Discussion over speculation** — When uncertain about concepts or design decisions, discuss with user to develop understanding before writing.
- **Breadth-first validation** — Review higher-level docs before diving into subdocs.

**Documentation workflows:**

General validation workflow:
1. **Discuss** concepts with user to develop deep understanding
2. **Read** existing content
3. **Evaluate** accuracy/completeness
4. **Correct/Rewrite** with confidence

NOT: Mechanical fill-in-the-blanks. Reach certainty before making changes.

**Handling TODO-marked docs:**

When you encounter docs marked with "Status: TODO":
1. **Never fill in TODO docs solo** — These require discussion with user first
2. **Discuss concepts first** — Develop understanding through conversation
3. **Only write after reaching certainty** — Discussion must establish clear understanding
4. **May prove unnecessary** — Some breakdown docs might be deleted if main doc suffices

## Conventions

**JSONL format:**

- One JSON object per line
- UTF-8 encoding
- Streaming-friendly (process line-by-line)
- Works with jq

**JSONL layer contract:**

- Read JSONL from stdin
- Write JSONL to stdout (except render-md → markdown)
- Log errors to stderr
- Exit 0 on success
- No terminal dependencies (colors, progress bars)
