# Devlog: 2026-07-11 — AI Studio index rung landed: IndexItem honesty fix + pluck/splat/browse

## Focus

Immediate plan step 2 (`../.claude/todo.md`): live-capture sitting to
reverse-engineer AI Studio's index endpoint and write the index rung —
`chatfs_aistudio_index_pluck.jq` + `chatfs_aistudio_index_splat.py` +
`..._index_browse.sh`. Reverse-engineering surfaced a schema-honesty gap
in already-landed code; fixed it first, then wrote the three new scripts
against the corrected shape.

## Decisions

### The index endpoint is `ListPrompts`, and both `/library` and any `/prompts/<id>` page fire it

`har-browse https://aistudio.google.com/library` confirms `/library` calls
`MakerSuiteService/ListPrompts` (`POST [100]`, page-size arg) → `{prompts:
[...]}`. A June-20 capture made while visiting a single `/prompts/<id>` page
already contained the identical call — the prompt detail page's sidebar
fires it too. Both captures returned the same 42 entries, no pagination
token present (this account's prompt count is under the requested page
size of 100) — the `has_more=false` premature-stop bug (tracked separately,
har-browse todo) could not be reproduced/observed this session, since
pagination never triggered.

`ListPrompts` entries reuse `ResolveDriveResource`'s existing PROMPT/METADATA
JSPB schema unchanged, confirmed via `docs/dev/aistudio-schema/rosetta/`'s
convert→verify loop, repointed to `ListPrompts` this same session — see
`../../../aistudio-schema/devlog/2026-07-11-000-rosetta-pivot-to-listprompts.md`.

### `IndexItem.create_time` must not be synthesized from `lastModified`

Consequence of the above: `chatfs_aistudio_layout.py::index_item()`
(written 2026-06-22, before the index endpoint was known) assumed
`chunkedPrompt.chunks[0].createTime` would always be available — true for a
full `ResolveDriveResource` fetch, never true for a `ListPrompts` entry
(no turn content at all). The only timestamp a `ListPrompts` entry carries
is `metadata.lastModified.revisionTime` — explicitly *not* creation time
(it advances on every turn; already established when the 2026-07-04
create_time-mislabel fix rejected it as a creation-time source).

Per `../design.kb/040-design.kb/no-partial-synthesis.md` ("don't lie about
file shape with the filename"), the same logic was applied one level down:
don't lie about *field* meaning either. Fix:

- `IndexItem.create_time` → `NotRequired[int]` (only present once a real
  fetch supplies it); added `IndexItem.last_modified: int` (always
  present, honestly named).
- `ChunkedPrompt.chunks` → `NotRequired[list[Turn]]` (matches reality:
  present-but-empty on index entries).
- `index_item()` now handles *both* provenances through the same
  `Conversation` shape — reads `last_modified` unconditionally, sets
  `create_time` only when `chunkedPrompt.chunks` is non-empty. One
  function, no branching on caller identity.

**Alternatives considered:** writing `lastModified` into `create_time`
directly (rejected — the house rule this violates predates this session and
exists for exactly this failure mode) — or a separate `IndexItem` variant
type per provenance (rejected — `NotRequired` handles it with one type and
one function, less to keep in sync as the two provenances converge over a
chat's lifetime — see "graduates" below).

### View-tree gets a uniform `Label=YYYY/...` convention, not a special case

First cut used a `LastModified/`-only-when-approximate prefix (i.e. the
normal case stayed unlabeled `YYYY/...`). User redirected: make it uniform
— *every* date-based view is labeled, including the existing default, so
multiple date-based views (by-tag, by-model, etc. — already anticipated in
`chat-as-directory.md`) can coexist under `root` without collision or an
implied claim. Landed as `chatfs_layout.py::time_dir_for(created, *,
label="Created")` — default changed from no-label to `"Created"`, so
`chatgpt`/`claude` get `Created=YYYY/...` automatically with zero call-site
changes (backward-compatible-by-default, not a behavior regression for
them — their on-disk demo output is gitignored/regenerated, not committed,
so nothing stale needed fixing). AI Studio's `place_meta()` picks
`label="Created"` when `create_time` is known, `label="LastModified"`
otherwise. A later `place_meta` call with real `create_time` "graduates"
the entry: the existing identity-scoped symlink purge (by uuid, whole-root
`rglob`) already finds and removes the old `LastModified=` symlink before
placing the new `Created=` one — no new cleanup logic needed.

### Pluck unwraps to one message per line, so massage/splat don't care which endpoint or how many pages

`chatfs_aistudio_conversation_pluck.jq` used to emit `ResolveDriveResource`'s
whole response body per line — a one-element envelope wrapping the single
prompt message — and `massage()` did the `doc[0]` unwrap itself. Writing
`chatfs_aistudio_index_pluck.jq` against `ListPrompts`'s body (a
many-element envelope, `[[entry, ...]]`) made the shared shape obvious: push
the unwrap into pluck (`.[]` / `.[0][]`) so both scripts emit the same
thing — one bare prompt message per line — regardless of which RPC or how
many entries/pages it came from. `massage()` shrank to `from_message(doc,
PROMPT)` directly (no more `doc[0]`), and `chatfs_aistudio_index_splat.py`'s
`massage_entry()` calls the identical `from_message(entry, PROMPT)` instead
of a second hand-written projection. One consequence: `index_splat` never
sees a page/envelope shape at all, so it needs no pagination-specific code
— one page or many, each entry just arrives as its own line.

### `is_conversation`'s NotRequired guard didn't actually accept an absent `chunks`

Wiring `index_splat.massage_entry` end-to-end (`from_message` → `is_conversation`
assert) caught a bug in the same-session honesty fix: `ChunkedPrompt.chunks`
was declared `NotRequired`, but `is_conversation`'s guard still read
`chunked_prompt.get("chunks")` — `None` for an absent key, which is not a
`list`, so every index-only entry (the exact case the honesty fix was for)
failed the guard. Fixed to `.get("chunks", [])`, matching the declared
shape. Caught by actually writing the consumer, not by re-reading the type
— a reminder that a `NotRequired` field needs its default checked at every
read site, not just declared once at the type.

## Conventions Established

- **Field honesty extends `no-partial-synthesis.md` to fields, not just
  files.** A field name is a claim about what the value means; don't reuse
  one name for two different provenances with different precision.
- **View-tree labels are uniform, not exceptional.** Every date-based view
  under a provider root gets a `Label=YYYY/...` year-segment prefix
  (`Created=` default); this is the one scheme for present and future
  alternate views (by-tag, by-model, ...), not a special case bolted on
  for AI Studio.
- **Pluck fully unwraps to the message level.** A pluck script's output is
  one bare, schema-ready message per line — never an envelope — so every
  downstream consumer (massage, splat) is shape-identical regardless of
  which endpoint or how many entries/pages produced it.

## Open Questions

- `ListPrompts` pagination shape (cursor/`has_more` field name and
  behavior) remains unobserved — this account's 42 prompts fit one page,
  so pagination never triggered. Revisit if/when a larger account or a
  smaller requested page size is captured.

## References

- `../.claude/todo.md` — Immediate plan step 2
- `../.claude/todo.kb/2026-06-20-000-aistudio-provider-parity-ladder.md`
- `../design.kb/040-design.kb/no-partial-synthesis.md`
- `../design.kb/040-design.kb/chat-as-directory.md`
- `../../../aistudio-schema/devlog/2026-07-11-000-rosetta-pivot-to-listprompts.md`
