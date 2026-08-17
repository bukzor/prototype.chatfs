# 2026-08-16 chatgpt-splat folded into chatfs, cross-provider render-helper dedup

## Focus

Reversing a deliberate, previously-recorded carve-out (chatgpt conversation
splat living outside `chatfs-cli`, in `packages/bukzor.chatgpt-export`), on
user fiat that the carve-out was always provisional and had expired — then
a copy-paste scan surfaced a second, unrelated dedup while looking for more
of the same.

## What happened

1. **Discussion, not just execution.** Asked to move `bukzor.chatgpt_export`
   into `chatfs`, "symmetric to the other two [providers]," or go the other
   direction. Found the question already had an on-record answer (three
   docs: `package-division.md`, the module-shape-refactor todo,
   `verb=splat.md`), all converging on "stays external" with real reasoning
   (own package/test/typesafety identity, predates chatfs-cli by 4 months).
   Recommended holding status quo — rejected. Pushed on "the other
   direction" (splitting claude/aistudio out too) — still wrong, its own
   trigger (heavy deps, external consumer) never fired. User's actual
   point: the *chatgpt-stays-external* carve-out was explicitly provisional
   ("why not... *now*") and they were revoking it by fiat, now. That's the
   one that had a real, live cost: chatgpt was the only provider missing a
   `chatfs-<provider>-conversation-splat` command, silently shelling out to
   a foreign-named `chatgpt-splat` binary instead.

2. **Fold-in** (`75b98a2`). Ported `splat.py`/`splat_test.py` into
   `chatfs.provider.chatgpt.conversation.splat`, matching claude/aistudio's
   shape (importable `splat()` + thin `main()`, subprocess-invoked from
   `path_render.py`). The Decimal-preserving JSON helper moved with it as
   provider-local `chatfs.provider.chatgpt.json` — chatgpt-specific
   (`create_time` needs sub-millisecond precision `typed_json`'s plain-float
   parsing loses), not folded into the shared root. New entry point
   `chatfs-chatgpt-conversation-splat`; `bukzor.chatgpt-export` dropped as a
   `chatfs-cli` dependency. Updated the three docs that had asserted the old
   state as canon rather than leaving them stale.

3. **Dedup pass 1** (`8fc3c11`). Removed the now-dead `splat.py`/
   `splat_test.py` copies from `bukzor.chatgpt-export`; moved the
   float-rejection typesafety test to `chatfs-cli` along with its subject.
   Getting it green again required giving `chatfs-cli` its own scoped
   `[tool.pyright]` strict block (confirmed inert for the repo-root
   `basedpyright .` sweep — that invocation never reads a nested package's
   config). Along the way: `bukzor.chatgpt-export/typesafety/
   test_float_rejection.py` has apparently never actually run under the
   documented root-level `pytest .` workflow — `pytest-pyright`'s file
   collection check is relative to cwd, not repo root, so it only fires
   when invoked with cwd inside the owning package. Pre-existing, not
   introduced here; noted in the commit rather than fixed (out of scope).
   `bukzor.chatgpt-export` keeps `json.py` (still `har2jsonl`'s dependency)
   and `har2jsonl.py`/`har2jsonl_test.py` (unreferenced by the current
   har-browse/pluck capture path) — that package's ultimate fate is a
   separate, still-open decision.

4. **Copy-pasta scan, on request.** Asked to scan for more duplication
   after the fold-in. `grep '^def '` per provider dir, intersected names
   across claude/chatgpt/aistudio, manually triaged each hit. Most
   same-named functions (`build_tree`, `basename_for`, `load_turns`,
   `capture`, `place_meta`) are legitimately different per-provider bodies
   already routing through shared `chatfs.shell` helpers — not bugs. Two
   were real: `fenced_json`/`render_details`, near-verbatim across all
   three `conversation/splat.py` files, each docstring admitting the
   mirroring ("mirrors claude/aistudio's splat"). Same shape as the
   `caller_location()` dedup two commits prior (`e824658`, this session's
   opening commit, not written by this session).

5. **Dedup pass 2** (`1610efe`). New shared `chatfs/splat.py` (distinct
   from `chatfs/render.py` — splat-stage per-message fragment rendering vs.
   render-stage turn/tree assembly). Unified rather than picked-arbitrarily:
   `render_details` gained `tool=` on aistudio's copy (additive, its one
   call site never passed it); `fenced_json` standardized on
   `ensure_ascii=False` (chatgpt's copy lacked it, silently `\uXXXX`-escaping
   non-ASCII in its rarely-hit "unmodeled content" fallback) and gained a
   Decimal-safe `default=` hook (chatgpt's Decimal-preserving JSON parse can
   put a `Decimal` anywhere in the raw content handed to it).

6. **Methodology discussion.** Asked how to build confidence against
   duplication that isn't literal copy-paste — same purpose, different
   representation. Answered with a ranked, evidence-grounded take (not a
   generic checklist): structural priors from parallel provider trees,
   grep for self-incriminating comments, test-*name* diffing as a cheap
   purpose-level proxy (ran it live: zero overlap across all three
   providers' test names — consistent with "already caught what's
   catchable this way"), and named the real gap — nothing here catches
   same-purpose-under-a-different-name; that needs pairwise LLM judgment
   scoped to the design.kb's named "verbs," not yet done.

## Loose ends, explicitly not resolved

- **`bukzor.chatgpt-export` package fate.** `json.py` + `har2jsonl.py` +
  `har2jsonl_test.py` remain; `har2jsonl` is unreferenced by any current
  pipeline path (the har-browse/pluck capture path replaced manual
  HAR-file extraction). Decide: port `har2jsonl` into `chatfs` too and
  retire the package, or keep it as legitimate standalone prior art.
- **`pytest-pyright` cwd-relative collection.** The float-rejection
  typesafety test (old location or new) has never run under `pytest .`
  from repo root — only `cd <owning package> && pytest typesafety`. Affects
  both the old and new location equally; not a regression from this
  session, but undocumented anywhere durable until now.
- **Semantic-duplication audit not run.** The design.kb names a fixed set
  of per-provider "verbs" (splat, browse, render, pluck, massage, capture,
  place) — a same-purpose-different-shape audit scoped to those, provider
  by provider, hasn't been done. Flagged as real, unscoped work, not a
  concrete plan.

## Next session

Three follow-ups filed: `.claude/todo.kb/2026-08-16-001-bukzor-chatgpt-export-package-fate.md`
(strategic — needs a decision), a `.claude/todo.md` bullet for the
pytest-pyright collection gap (small, mechanical once someone picks a fix),
and `.claude/ideas.kb/2026-08-16-000-semantic-duplication-audit.md`
(speculative — scoped but uncommitted).
