# Devlog: 2026-07-27 — First user-facing doc: how-to-chatfs

## Focus

User asked: "use chatfs to pull down a .md of `https://claude.ai/chat/00bd72f3-...`".
Doing it cost ~55k tokens of source-reading to find *which command to run*. The
session's real output is the fix for that: `docs/how-to-chatfs.md`, the first
file in the top-level user-facing namespace `docs/README.md` has been reserving
since day one.

The capture itself worked first try, unattended-clean: 101 messages, 102 turns
rendered, no manual recovery. That is the second data point worth recording —
the claude provider path is not fragile.

## Decisions

### The discovery failure was a documentation failure, not a search failure

**Rationale:** Every entry point an agent reads first agreed that nothing works
yet — root `README.md` said "Not ready for use. Documentation and design phase";
`packages/chatfs/` says "the CLI is a stub"; `CLAUDE.md`'s Key Files listed two
design incubators but not `chatfs-cli-mockup/`, the one that actually runs
end-to-end. Each statement was locally true and the ensemble was misleading: the
working pipeline was the one thing unmentioned. No amount of better searching
fixes a consistent wrong signal; only editing the signal does.

**Alternatives considered:** Adding the run command directly to `CLAUDE.md` —
the first attempt, and rejected on user feedback. It puts user-facing operating
instructions in the agent-context file, and it would need editing again at
graduation. `CLAUDE.md` now carries a short generic "What Works Today" that
names the incubator and defers to the how-to for anything runnable.

### User-facing docs live at `docs/*.md`, not under `docs/dev/`

**Rationale:** `docs/README.md` line 25 already reserved the top-level namespace
for user-facing documentation; nothing had claimed it. `docs/dev/` is
developer-facing by construction, and the incubator README is stage-by-stage
pipeline internals — the wrong altitude for someone who just wants their chat on
disk.

## Conventions Established

- The status line in `README.md` scopes its "pre-alpha" claim to the *unbuilt*
  part (FUSE mount, `chatfs` command) and points at what does work. A blanket
  "not ready for use" on a repo that has a working path is a lie that costs the
  next reader real time.
- `HACKING.md` opens with the use-vs-develop split rather than assuming every
  reader is a contributor.
- Same pass found `HACKING.md`'s Setup was describing an abandoned approach —
  `cd claude-api && uv sync` (that directory is long gone) and a
  `CLAUDE_SESSION_KEY` cookie, which now survives only in `trash/`. Replaced
  with the real `uv sync` + `pnpm install` and an explicit "no API key needed".
  Worth a periodic grep: setup instructions rot silently because nobody
  who already has a working checkout ever runs them.

## Open Questions

- `docs/how-to-chatfs.md` and the incubator `README.md` now both carry command
  lines. Overlap is deliberate (different audiences, different altitude) but it
  is a drift risk; at graduation they should be re-cut, not both edited.
- The how-to documents `chatgpt` and `aistudio` as working by module-path swap.
  That is taken from the incubator README (aistudio landed 2026-06-20..07-03),
  not verified live this session — only the claude path was run.

## References

- `docs/how-to-chatfs.md` — the artifact
- `docs/dev/design-incubators/chatfs-cli-mockup/README.md` — the dev-facing
  counterpart it defers to
- `.claude/todo.md` — graduation arc now carries the how-to's follow-on edit
- `packages/har-browse/.claude/todo.kb/2026-07-22-001-*.md` — why origin-storage
  clearing is a documented failure mode in the how-to
