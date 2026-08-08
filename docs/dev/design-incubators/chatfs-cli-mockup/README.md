# chatfs-cli-mockup — what should the filesystem *look* like? (graduated)

> **Historical.** The code that grew here was promoted to
> `packages/chatfs-cli/` (2026-08-07) and installs real commands —
> see that package's README for the pipeline anatomy and
> `docs/how-to-chatfs.md` for usage. Its `design.kb/` followed the code
> (2026-08-08) to `packages/chatfs-cli/design.kb/`. What remains in
> this directory:
>
> - `chatfs.demo/<provider>` — captured fixtures (gitignored bulk).
>   Point the installed commands' `--cache` at one to exercise render
>   stages offline.
> - `.claude/` — incubator-era todos and session notes.

## What this incubator asked

The pipeline `BB1 (capture) → BB2 (extract) → BB3 (render)` was
specified in the design.kb in terms of JSONL streams. This incubator
asked the perpendicular question: **what does the user-facing surface
look like?** — hierarchy (date tree vs. UUID storage), lazy markers,
filename collisions, per-conversation layout.

## What it settled

- **Chat-as-directory**: flat UUID-keyed storage under `.chat/`, with a
  `Created=YYYY/MM/DD/...` view of directory-symlinks pointing into it
  (`packages/chatfs-cli/design.kb/040-design.kb/chat-as-directory.md`).
- **Capture exhaust placement**: raw CDP, plucked conversation document,
  and index metadata live in `.data/`, per-UUID, never destroyed by a
  failed re-capture.
- **Render shape**: `chat.md` walks the live path from `current_node`;
  dead branches appear as nested blockquoted asides at their fork
  point; per-message atomic `.md`/`.json` under `messages/`.
- **Two capture entry points**: by URL (one browse trip yields both the
  conversation document and the sidebar index page) and by path (after
  `index-browse | index-splat` has laid down chat dirs).
- **Driver model**: orchestrators address a target and drive leaf
  stages as subprocesses over stdio, teeing intermediates to disk
  (`packages/chatfs-cli/design.kb/040-design.kb/driver-model.md`).
- **Deterministic regeneration**: every stage rebuilds from scratch;
  re-running is always safe
  (`packages/chatfs-cli/design.kb/040-design.kb/deterministic-regeneration.md`).
- **Multi-provider**: chatgpt.com first, then claude.ai (2026-05-11)
  and AI Studio (2026-06-20..07-03) under the same module shape.

Lessons now accrue in `packages/chatfs-cli/design.kb/` (package
internals) and the project-level `design.kb/` (cross-package seams); the
code itself lives (and evolves) in `packages/chatfs-cli/lib/chatfs/`.
