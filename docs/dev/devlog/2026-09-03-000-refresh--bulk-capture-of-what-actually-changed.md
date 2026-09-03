# 2026-09-03 refresh: bulk capture of what actually changed

## Focus

`chatfs-refresh N` and its per-provider twins: run the index, then
capture the conversations that changed in the last N days and aren't
already captured up to date. Explicitly **not** in scope: unattended
capture. Every browse still opens a window and waits for the human.

## What happened

1. **Scope correction, before any code.** The first estimate priced an
   auto-cut for `har-browse` (end a capture when the payload arrives and
   the network settles) as the blocker, because a refresh that opens
   forty windows sounded useless. The user hadn't asked for that and
   didn't want it: the value is the bookkeeping, not the clicking.
   Refresh's job is deciding which chats are worth a click -- on an
   887-chat account, three clicks instead of nine hundred. Price with
   that assumption removed: a few hours, no blockers.

2. **`--cache` was appended twice by every index driver** (found while
   replaying a fixture through a stub `har-browse`, not by reading):

       + $ chatfs-provider-claude-index --cache …/cache
       Capturing https://claude.ai/recents → …/cache/claude/claude/.data/index.cdp.jsonl

   `extract_cache` appends the provider segment centrally -- deliberately,
   so no leaf can forget -- and the bare-noun drivers forwarded their
   already-appended root to both child stages, which appended again.
   Every `chatfs-provider-<p>-index` run has been landing one level too
   deep. Fixed with `chatfs.cli.cache_root`, the named inverse a driver
   forwards; pinned offline by a test that monkeypatches `sh.pipe` and
   reads the argv.

3. **The placement record carries `updated`.** Refresh needs two
   answers per chat -- is it recent, is our copy behind -- and the index
   splat's stdout was the only stream it sees. Normalized across the
   three providers in each `layout.updated_at`: claude's `updated_at`,
   chatgpt's `update_time`, AI Studio's `last_modified`.

4. **The refresh commands.** `chatfs-provider-<p>-refresh <days>` runs
   the index, checks coverage, then browses each recent-and-stale chat,
   emitting the records it refreshed. `chatfs-refresh <days>` runs all
   three in turn. Design entry:
   `packages/chatfs-cli/design.kb/040-design.kb/cli-command-shape.kb/verb=refresh.md`.

5. **Verified by replay, not only by unit test.** A synthesized
   two-chat CDP stream (one changed an hour ago, one a year ago) driven
   through the real commands with a stub `har-browse`: run 1 captures
   and renders exactly the recent chat; run 2 skips both, naming its
   reason for each; a 3650-day window exits 3 without browsing anything;
   the fan-out reports two providers failed and one ok, exit 1. This is
   the level at which the double-append bug was visible and the unit
   tests were not.

## Decisions

### Staleness is `mtime(conversation.json)` vs. the index's `updated`

**Rationale:** `conversation.json` is written by one stage and
atomically promoted only on success, so its mtime is a completed
capture's finish time. No new on-disk format.

**Alternatives considered:** a watermark in `meta.json` -- impossible as
posed, because the index splat rewrites `meta.json` from the fresh item
*before* anything reads the old value back, so the number the decision
needs is already gone. A dedicated stamp file beside `conversation.json`
would work and remains the upgrade path if mtime proves untrustworthy
(a cache copied without `-a` reads as entirely fresh); it buys nothing
today.

### A chat with no `updated` timestamp is not refreshed

**Rationale:** an absent timestamp is no evidence of recency. Reversed
from this session's own first draft, which said unknown-means-stale on
"a wasted click is cheaper than silent staleness" -- true per chat,
false in aggregate, because a provider that stopped sending the field
would then open a window for every chat in the account. The silence that
argument feared is bought back directly instead: the count of undated
records prints to stderr unconditionally, and an index where *no* record
carries a timestamp fails the coverage check outright.

### Coverage is checked before the first browse

**Rationale:** nothing scrolls the sidebar yet, so a captured index can
stop inside the window and look complete. Proof of coverage is one
indexed chat *older* than the cutoff. Discovering the shortfall after
twenty clicks would spend the operator's whole attention budget to buy
an incomplete set, so the check runs first and exits 3 naming the date
to scroll back to.

## Conventions Established

- **A verb may apply to the `provider` partition itself**, with no noun
  between, when its object is that provider's whole cache
  (`provider claude refresh`). Coining a `cache` noun no other command
  takes, purely to restore noun-then-verb symmetry, would cost more than
  it explains.
- **Fan-out driver**, added to the partition vocabulary beside
  dispatching form and bare-noun driver: a command with no provider
  segment that runs every provider's form of itself. A dispatching form
  reads its provider off an address; an address-less verb can't
  dispatch, but can still have a shortest-name form that finishes the
  job. It does not stop at the first provider's failure.
- No ADR: the decision is CLI surface shape, which this package records
  in `design.kb/040-design.kb/cli-command-shape.kb/` -- a second home
  would drift.

## Open Questions

- Automatic index coverage still depends on the unsolved har-browse
  "wait until `has_more=false`" item. Until then the operator scrolls
  and refresh only checks.
- Index splat is quadratic in cache size: `_purge_view_symlinks` walks
  `root.rglob("*")` once per item placed (~2.5 min for 887 chats,
  measured). Refresh makes that a per-run cost rather than a one-time
  one. Filed in the package taskfile.

## References

- `packages/chatfs-cli/design.kb/040-design.kb/cli-command-shape.kb/verb=refresh.md`
- `packages/chatfs-cli/design.kb/040-design.kb/cli-command-shape.kb/noun=index.md`
  -- amended: it claimed `created` was deliberately absent from the
  placement record, and `updated` needed its own justification rather
  than a quiet contradiction.
- `docs/how-to-chatfs.md` -- "Pull everything that changed recently"
