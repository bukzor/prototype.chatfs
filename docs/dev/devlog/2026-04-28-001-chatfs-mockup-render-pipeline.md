# 2026-04-28: chatfs-mockup — end-to-end render pipeline

## Focus

Close the mockup loop: take the date-tree splat from earlier sessions
all the way to a readable `$TITLE.md` per conversation, including the
chatgpt branch structure (forks/regenerations/edits).

## What Happened

**`2537723` — capture → splat → render pipeline.** Per timestamp
directory now contains `meta.json`, `content.cdp.jsonl`,
`$UUID.json`, `$UUID.splat/`, and a rendered `$TITLE.md`.
`chatgpt-page-capture.py` drives `har-browse` against the
conversation URL, plucks via `chatgpt-conversation-pluck.jq`, and
runs `chatgpt-splat`. `chatgpt-render.py` walks
`mapping[current_node]` back to root and emits H1 turn headings
(`seq · role · time`, with content-type suffix when non-default)
linking to the atomic per-message `.md` under `messages/`.

**`013affc` — dead-branch forks as blockquoted asides.** First render
walked only the live path, hiding all alternates behind splat
directory traversal. Now the renderer walks the full mapping tree
and emits dead branches as nested blockquoted sections immediately
after their fork point — depth = how many forks deep, expressed as
nested `> ` prefixes. Live continuation re-emerges unprefixed once
the dead siblings are flushed. Within a dead subtree, latest-by-
`create_time` is treated as the primary continuation; further forks
go deeper. On the demo conversation: 88 → 134 turns rendered, max
depth 3, ~2.4% byte overhead from `> ` prefixes.

**Real-conversation validation.** Ran on a 327-message physics chat
("Quantum Gravity and UV Catastrophe"). 11 fork points, 20 dead
branches, all surfaced inline as expected. Markdown is navigable:
turn headings link back to the splat, blockquote nesting reads
naturally, ChatGPT's inline `\(...\)` and code fences pass through
unchanged.

## Decisions

**Render walks the full mapping tree, not just `current_node`.**
The alternative — leaving alternates accessible only by `cd`-ing
into `$UUID.splat/conversations/<fork-dir>/` — keeps the live
markdown tidy but makes alternates invisible to anyone reading
`$TITLE.md`. Inlining as blockquote asides preserves the live read
order while making fork structure visible. Cost was small (2.4%
bytes); benefit is "you can see what was tried and abandoned" with
no extra navigation.

**Latest-by-`create_time` is the primary continuation inside a
dead subtree.** A dead subtree may itself fork further. Picking the
latest child as the in-aside "main" line, with further siblings
nested deeper, mirrors what the user most recently chose at each
internal fork — i.e., the dead subtree shows what the user *would*
have ended up with along that branch, not an arbitrary first-child
walk.

## Lessons

**Fork dirs are user-message variants, not assistant regenerations.**
All 11 fork points in the demo chat are `user.text` forks — the user
edited their own prompt and re-sent each time. Whether ChatGPT also
exposes assistant-regen forks at all in the captured payload is
still open; the splat fork structure didn't surface any.

**Splat-time conventions matter for the renderer.** The splat
already encodes fork structure as `NNN.user.text.<timestamp>/`
subdirectories under `conversations/`, with the `.md`/`.json`
files materialized once under `messages/` and symlinked from
`conversations/`. Render only had to consult `mapping` + the
per-message `.md` files; no need to reparse the original payload.

## Next Session

- BB1/BB2/BB3 boundary in design.kb is JSONL streams; this incubator
  is hand-driven Python. Worth deciding what (if anything) folds
  back into the design before the FUSE work starts.
- Multi-provider sketch — does claude.ai sit under the same date
  tree, or under a sibling `chatfs.demo/claude/`? The current layout
  assumes per-provider top-level dirs but only chatgpt is exercised.
