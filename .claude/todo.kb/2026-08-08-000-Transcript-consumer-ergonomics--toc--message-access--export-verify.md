---
managed-by: Skill(llm-subtask)
status: open
cost-benefit-sweh:
  timebox:
    "@value": 2.0
    rationale: |
      Three small consumer-facing capabilities over already-rendered
      exports; toc and single-message access may reduce to "make the
      existing per-message links real", leaving verify as the only
      new logic.
    confidence: unsure
  benefit-2w:
    "@value": 0.5
    rationale: |
      Payoff is per-transcript-consuming-session, elsewhere (agent
      workflows over exports); locally it hardens the BB3 render
      contract. Rises sharply if ledger-serialization sessions recur.
    confidence: unsure
---

# Transcript consumer ergonomics: toc, message access, export verify

**Priority:** Medium
**Complexity:** Low–Medium
**Context:** Filed 2026-08-08 from the consumer side: an agent session
in `prototype.llm-stet` serialized the export at
`chatfs/Building a reasoning audit system/` (69 messages, 1733-line
`chat.md`, ~67k tokens) into a design corpus, then audited the result
against the transcript. Every transcript operation below was done with
`grep -n '^#'` + `sed` ranges and three paged reads. **Requirements
only**, from the consumer's seat — command spelling and placement
belong to this repo's own conventions
(`packages/chatfs-cli/design.kb/` command-shape decisions), and
whether each capability is a command, a render-mode, or just "the
per-message files actually existing" is an implementation choice this
entry deliberately doesn't make.

## Problem Statement

A rendered `chat.md` is the whole conversation in one file, which is
exactly right for humans and exactly wrong for an agent with a context
budget: the consumer needs to know what's in the transcript, and read
selected messages, *without* paying for the whole file. Today that
takes hand-rolled grep/sed. Worse, the export's own affordance for
this — `chat.md`'s per-message links into `messages/` — dangles in the
llm-stet export (no `messages/`, no `.data/`), and nothing tells the
consumer whether that's a partial-export mode or a broken export.

## Requirements (consumer's seat)

- [ ] **Message index ("toc"):** ordinal, role, timestamp, reply-to,
      and location (line span in `chat.md` and/or per-message path) —
      obtainable without loading the transcript body. Field use:
      locating the final ledger reprint and the closing four messages
      of a 69-message transcript.
- [ ] **Single-message access:** the body of message N alone. Field
      use: the audit needed messages 038 and 066–069, ~15% of the
      file. Note the rendered links imply `messages/*.md` already *is*
      the designed answer; if so this requirement reduces to those
      files existing (or being producible on demand).
- [ ] **Export integrity ("verify"):** every intra-export reference
      resolves (`messages/`, `.data/`, anything else `chat.md`
      links); nonzero exit on failure, so provenance imports (like
      llm-stet's `chatfs/` baseline commit) can be gated on it. A
      deliberately-partial export mode, if one exists, should be
      distinguishable from a broken export.
- [ ] **Machine-parseable output** for the index and verify results —
      the consumer is usually an agent, not a human.

## Non-goals

- Transcript *semantics* — extracting claim lines, last-wins ledger
  state, label censuses. That's `llm-claim-ledger-replay`; see the
  cross-referenced entry below, whose non-goals point back here.

## Success Criteria

- [ ] Against `prototype.llm-stet/chatfs/Building a reasoning audit
      system/`: index lists 69 messages with roles/timestamps/reply-to
      matching the `# [NNN · role · timestamp]` headings; message 067
      is retrievable alone; verify fails (dangling `messages/` and
      `.data/` links) — or passes with an explicit partial-export
      designation, if that's a mode.
- [ ] An agent can do the above without reading `chat.md` in full.

## See also

- Consumer provenance: `~/repo/github.com/bukzor/prototype.llm-stet/`
  — the export at `chatfs/Building a reasoning audit system/chat.md`
  (committed `1e99367` as provenance baseline, dangling links and
  all); the serialization session (2026-08-08, claude-code, unexported
  as of filing) is where these needs surfaced.
- Sibling requirements from the same session:
  `~/.claude/skills/llm-claim-ledger/.claude/todo.kb/2026-08-08-000-Helper-command-family-bin-llm-claim-ledger.md`
  — its non-goals section defers chatfs ergonomics to this entry.
- This repo's rendering design: `docs/dev/design.kb/040-design.kb/`
  (BB3 rendering; `black-box-decomposition.md`) — where the
  chat.md ↔ `messages/` contract lives.
- Command-shape conventions: `packages/chatfs-cli/design.kb/`
  (noun-verb, partition-prefix scope) — governs spelling if these
  become CLI surface.
- Possible prior art in-house:
  `~/repo/github.com/bukzor/prototype.claude-export-cli/` — appears to
  be an earlier exporter; not assessed, flagged for dedup.
