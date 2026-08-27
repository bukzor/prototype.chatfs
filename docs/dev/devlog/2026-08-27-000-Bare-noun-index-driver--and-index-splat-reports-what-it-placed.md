# 2026-08-27 Bare-noun index driver, and index splat reports what it placed

## Focus

Two small CLI-surface changes, both starting from the same observation:
`chatfs-claude-index-browse` alone prints 318KB to a terminal, and the
thing you actually wanted was never browse's output.

## What happened

1. **Why the index browse output is huge.** Measured rather than guessed,
   with a `jq` byte breakdown: `settings` is 74% of a claude index entry
   and `settings.enabled_mcp_tools` alone is 54%; the identity fields
   everything downstream reads are 4%. Browse is doing nothing wrong —
   it's a leaf that emits its provider's pages verbatim, and those pages
   are mostly per-conversation feature flags.

2. **`chatfs-<provider>-index`, the bare-noun driver** (`e30795c`). The
   noun with no verb runs the noun's whole pipeline: `index browse |
   index splat` over one `--cache`. Asked for on tab-completion grounds —
   the bare noun sorts before its own `-browse`/`-splat` leaves, so the
   whole-job command is offered first — which turns out to be the right
   ordering for the right reason: it *is* the default action.

   New `sh.pipe()` joins the two as an OS pipe, with `pipefail`
   semantics (raises on either stage's non-zero exit, not just the
   last's) and the producer reported first, since a browse failure
   surfaces downstream as splat complaining about empty input.

   Module home is `index/__main__.py`, which resolves the collision
   between "kebab name == module path" (pointing at the `index`
   *package*) and the style rule that `__init__.py` holds no code. It
   also makes `python -m chatfs.provider.<p>.index` name the driver.

   A noun earns a driver only when its stages compose into one obvious
   default. `conversation`'s verbs are alternatives, not a sequence, so
   it gets none.

3. **`index splat` writes what it placed** (`98e60bd`). Asked whether
   `-index` should emit jsonl of what it indexed, then self-corrected in
   the same breath: that implies *splat* should be in charge of it.
   Correct, and it's a fix rather than an addition — splat was the one
   stage violating this repo's own JSONL layer contract ("Write JSONL to
   stdout", CLAUDE.md) without being its documented exception
   (`render-md`), and it was a dead end: it did real work and said
   nothing about it.

   `place_meta` now returns a `Placement` NamedTuple — the identity it
   placed under plus the storage dir and the live view symlink — and
   each provider's index splat prints `{id, title, chat_dir, view}` per
   chat placed. Identity comes from `place_meta`'s already-normalized
   arguments, not the provider's own field names (claude `uuid`/`name`
   vs chatgpt/aistudio `id`/`title`), so one `jq` reads every provider's
   stream:

       chatfs-claude-index --cache ~/chats/claude |
         jq -r .chat_dir |
         xargs -rL1 chatfs-claude-conversation-path-browse

   `created` is deliberately not in the record: it's in `meta.json`, it's
   encoded in `view`'s path segments, and emitting it uniformly would
   mean re-deriving AI Studio's create_time/last_modified fallback
   outside the wrapper that owns that choice.

4. **The driver needed no change to gain this.** It emits whatever its
   last stage emits, because it *is* the pipe. Giving the driver a
   stdout of its own would have made it a third implementation of the
   index flow rather than a way to run the existing one — and would have
   contradicted `driver-model.md` one commit after writing it there.

## Conventions established

- **Bare-noun driver** — new vocabulary in
  `packages/chatfs-cli/design.kb/040-design.kb/cli-command-shape.md`. The
  noun with no verb is the noun's default action. Earned only where the
  stages compose into one obvious default.
- **Placement record** — the shared `{id, title, chat_dir, view}` shape
  every provider's index splat emits, documented at
  `cli-command-shape.kb/noun=index.md`. `chat_dir` is the machine handle
  (what `conversation path browse` takes), `view` the human one.
- **Verbatim meta.json is the contract, not an oversight** — ruled by
  the user when the 318KB measurement made dropping `settings` tempting:
  filtering means parsing a structure nothing downstream has claimed
  yet, and what is currently opaque stays opaque. Recorded at
  `docs/dev/technical-policy.kb/path-ownership.md` so the next session
  that measures the same bytes doesn't re-open it.

## Loose ends, explicitly not resolved

- Nothing drives `index splat`'s `main()` under test. The stdout
  contract and the first-sight dedup rule were verified once by hand,
  against a throwaway fake `har-browse` in `trash/`; `place_test.py`
  covers only `Placement` itself. Filed in `.claude/todo.md` under
  "Index pipeline follow-ups".
- `.claude/todo.kb/2026-08-22-000-clear-the-twelve-frontmatter-validation-errors.md`
  had no `todo.md` line, so it was invisible to every backlog sweep
  since it was written. Listed now; the older "4 frontmatter violations"
  Deferred bullet is marked superseded by it (same drift, re-surveyed).

## Next session

Cover `index splat`'s `main()` with a real test — the todo has the
fixture shape per provider. Nothing else here is half-done; the
graduation & integration umbrella remains the active arc.

## References

- `packages/chatfs-cli/design.kb/040-design.kb/cli-command-shape.md` —
  "Why a bare-noun driver", `__main__.py` naming
- `packages/chatfs-cli/design.kb/040-design.kb/driver-model.md` — the
  driver is the pipe
- `packages/chatfs-cli/design.kb/040-design.kb/cli-command-shape.kb/noun=index.md`
  — "What index splat emits"
- `docs/how-to-chatfs.md` — the `index | jq | xargs` bulk-capture loop
