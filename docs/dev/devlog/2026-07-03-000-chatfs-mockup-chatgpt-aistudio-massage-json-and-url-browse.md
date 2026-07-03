# Devlog: 2026-07-03 — chatfs-mockup-chatgpt aistudio massage-json and url-browse

## Focus

Give AI Studio a `conversation.json` that matches the shape chatgpt/claude
get for free from their native keyed wire format — and wire it into a real
browse entry point, since AI Studio's wire format is JSPB (positional
arrays), not keyed JSON.

## Decisions

### `conversation.raw.json` (plucked JSPB) vs. `conversation.json` (named)

**Rationale:** For chatgpt/claude, `conversation.json` *is* the raw API
response — already keyed, no transform needed. AI Studio's isn't, so pluck's
output alone was never "good" json. Splitting into two files keeps the raw
capture around for audit (same role `cdp.jsonl` already plays) while giving
`conversation.json` the same job description across all three providers:
browse's contract-output, whole and named.
**Alternatives considered:** Naming pluck's AI Studio output `conversation.json`
directly (rejected — lies about file shape by reusing a filename whose
established meaning, elsewhere, is "native keyed"; violates
`design.kb/040-design.kb/no-partial-synthesis.md`'s "don't lie about file
shape with the filename" corollary).

### `massage` as a new pipeline stage, unique to AI Studio

**Rationale:** `chatfs_aistudio_conversation_massage_json.py` decodes the
whole JSPB body into named JSON via a hand-curated `SCHEMA` (slot → field
name, recursive). It emits the *complete* named document (name, runSettings,
metadata, systemInstruction, chunkedPrompt) — not a narrowed subset like
just `turns` (an earlier draft did this and was corrected: picking out a
subset is `pluck`'s job, already done upstream; massage's job is naming
what pluck already isolated, in full).
**Alternatives considered:** Importing `docs/dev/aistudio-schema/rosetta/convert.py`
directly (rejected — that package is exploratory/disposable per the user;
the mockup pipeline owns its own copy). The port surfaced two bugs versus
the original: a dropped `"prompt"` top-level wrapper (verified missing by
diffing against `rosetta/resolvedrive.alt-json.json`, the real ground
truth) and a weakened `Literal["map"]` → `str` type. Both fixed.

### No incidental-index cross-check for AI Studio's `url_browse.py`

**Rationale:** chatgpt/claude's `url_browse` scripts derive `meta.json` from
a *second*, incidentally-captured index endpoint and cross-check it against
the conversation document. AI Studio has no reverse-engineered index endpoint
yet, but doesn't need the cross-check either: `ResolveDriveResource`'s
`metadata` (displayName/lastModified) already carries identity in the same
body that becomes `conversation.json`, so `chatfs_aistudio_layout.index_item`
derives `meta.json` straight from it.
**Alternatives considered:** Blocking `url_browse.py` on the index rung
landing first (rejected — no dependency actually exists; would have
delayed a working entry point for no reason).

### Capture/pluck/massage orchestration lives in the browse script, not `chatfs_aistudio_layout.py`

**Rationale:** chatgpt's and claude's layout modules disagree with each
other here — chatgpt inlines the har-browse+pluck subprocess calls in
`chatfs_chatgpt_conversation_path_browse.py`; only claude's `layout.py` has
a shared `capture()` helper. Layout.py's own scope (mirrored across all
three) is identity/path/placement (`index_item`, `time_dir_for`,
`chat_dir_for`, `place_meta`) — process orchestration doesn't fit that, so
chatgpt's split was followed.
**Alternatives considered:** Adding `capture()` to `chatfs_aistudio_layout.py`
(first draft did this, reverted after the user flagged it as likely the
wrong place).

## Conventions Established

- AI Studio's browse writes 4 files per conversation: `cdp.jsonl` (raw
  capture), `conversation.raw.json` (raw JSPB), `conversation.json` (named),
  `meta.json` (identity) — one more than chatgpt/claude's 3, because of the
  extra massage stage.
- A script that ports logic from `docs/dev/aistudio-schema/` should
  re-verify against that package's own golden pair
  (`rosetta/resolvedrive.{jspb,alt-json}.json`) rather than trusting the
  port is faithful — the port here silently dropped a wrapper key and a
  type on the first attempt.

## Open Questions

- `chatfs_aistudio_conversation_splat.py` still reads raw positional JSPB
  directly, duplicating indices `massage_json.py` now names. Retarget it to
  read `conversation.json`'s `chunkedPrompt.chunks[]` by key once
  `path_render.py` exists (tracked in the parity-ladder todo.kb).
- AI Studio's index endpoint (`ListPrompts`?) is still unreverse-engineered;
  the index rung (`chatfs_aistudio_index_pluck.jq`/`_index_splat.py`) is
  blocked on finding/capturing it.

## References

- `.claude/todo.kb/2026-06-20-000-aistudio-provider-parity-ladder.md` — full
  rung-by-rung status
- `docs/dev/aistudio-schema/discourse.kb/questions.kb/how-does-this-serve-chatfs.md`
  — resolved by this session's work
- `design.kb/040-design.kb/cli-command-shape.kb/noun=conversation.kb/verb=browse.md`
  — AI Studio divergence section, added this session
- `design.kb/040-design.kb/no-partial-synthesis.md` — motivated the
  raw/named file split
