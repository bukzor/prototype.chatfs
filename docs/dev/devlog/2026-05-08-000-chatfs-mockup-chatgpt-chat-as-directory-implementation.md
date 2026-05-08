# 2026-05-08: chatfs-mockup-chatgpt — chat-as-directory implementation

## Focus

Land the chat-as-directory layout in code (designed in the May 5
session). Storage moves to `.chat/$UUID/`; date-tree becomes a view of
symlinks pointing into storage. End-to-end against a live ChatGPT URL.

## What Happened

**Implemented per design.** Rewrote 7 scripts. `place_meta` now writes
`meta.json` to `.chat/$UUID/meta.json`, runs identity-scoped view-symlink
purge (sweeps `root.rglob` for symlinks whose target contains the UUID),
and places fresh view symlinks (`$TITLE.md` → `chat.md`, `.chat` →
chat dir). `path_render` allowlists captured (`{meta.json,
conversation.json, cdp.jsonl}`), purges the rest, splats, unpacks
`conversation.splat/*` up one level, writes `chat.md`. `url_browse`
moves staged captures into `.chat/$UUID/` then calls `place_meta`.
`resolve_chat_dir` encapsulates the loose ergonomics (chat-dir, file
inside it, view-symlink resolution, view-dir-via-`.chat`-shortcut)
behind a single function; downstream code is strict and asserts on
unexpected state.

**Smoke + live verified.** Smoke: rm-rf demo, splat 56 chats from
cached `chatgpt.index.jsonl`, migrate one chat's captures into
`.chat/$UUID/`, re-render → 134 turns, byte-stable across re-render,
identity-scoped purge stable across re-splat (439 → 439 symlinks).
Live: user ran `conversation_url_browse.py` against
`https://chatgpt.com/c/69f21e0c-…`, 188 messages plucked / 129 turns
rendered.

**Judgment-call follow-ups.** User reviewed the calls I'd made:

- Kept `conversation_url_render.py` as the noun-verb-locator cell
  (`conversation × url × render`); was a flagged loose end.
- **Removed `uuid:` frontmatter** from `chat.md` entirely. Rationale
  in `view-symlink.md` ("self-identifying when copied outside the
  tree") doesn't pull weight: anyone with the tree finds the chat by
  content; anyone without can't access ChatGPT under your account
  anyway. Stripped from code, README, and the design doc's
  "Frontmatter for portability" section.
- **Tightened `resolve_chat_dir`** to assert its result is a real dir
  whose parent is named `.chat/`. Loose ergonomics encapsulated;
  downstream stays strict.
- **Added duplicate-UUID assert** to `index_splat`. Prior code counted
  ts-dir collisions which became meaningless under UUID-keyed
  storage; replaced with a real sanity check.

**Content spot-check surfaced a real bug.** Inspecting the
live-rendered `chat.md`: 12 fork points (10 assistant-regen, 2
user-edit; one 4-way), 33 dead-branch turns blockquoted at fork
points, 96 live turns. Render correctly walks `current_node` → root.
But the inline `messages/<stem>.md` links break textually when read
through the view symlink (`2026/.../$TITLE.md`): `messages/` doesn't
exist alongside the symlink, so a path-textual renderer (web rendering
— GitHub Pages, mkdocs) 404s. Symlink-resolving readers (editors,
POSIX file APIs) work in both places.

**Decision: collapse the view to a single directory-symlink.** Three
alternatives rejected:

1. Document the limitation — *"we don't document bugs."*
2. Add `messages` (and originally `conversations`) symlinks in each
   view dir — leaves a multi-symlink view; `conversations/` was
   overreach (not referenced from `chat.md`).
3. Make `chat.md` links absolute — messy, not relocatable.

User suggested a fourth: ts-dir IS the symlink, no nesting. Rejected
because it loses title-in-path navigation and can't host
same-second-different-title collisions.

Chosen: `YYYY/.../$TITLE → .chat/$UUID/` (one symlink per chat in the
view dir, the symlink IS the chat dir), and move captured exhaust
under `.chat/$UUID/.data/` to clean the visible chat-dir surface.
Captured `chat.md` link resolution becomes
`view/$TITLE/messages/<stem>.md` → `.chat/$UUID/messages/<stem>.md`
textually. Strategic todo persisted at
`.claude/todo.kb/2026-05-08-000-…-data.md`.

## Lessons

**Spot-checking renders is non-negotiable.** "Rendered 134 turns"
read like success, but the inline links 404 under web rendering. The
only way to find that was to actually walk the live data. Sessions
that land a major change need a content read-through, not just a
"does it run" check.

**"Don't document bugs" is sharper than it sounds.** I proposed
documenting the link-resolution asymmetry as a known limitation. The
user pushed back: documenting it formalizes the bug. Either fix it or
don't ship it. The directory-symlink redesign came out of refusing to
document the limitation.

**Ergonomic encapsulation rule.** When a function is intentionally
forgiving for input-shape ergonomics (`resolve_chat_dir` accepts four
shapes), the forgiving logic must be wholly inside that function and
the function must end with a strict assertion of its post-condition.
Downstream code then assumes a canonical shape and raises on
unexpected state without defensive checks. Loose-then-strict is
clearer than loose-throughout.

## Next Session

- `.claude/todo.kb/2026-05-05-002-…-noun-verb-model-sub-kb.md` —
  planning, discussion with user before any kb creation.
- `.claude/todo.kb/2026-05-08-000-…-data.md` (new) — collapse view to
  directory-symlink + hide captured exhaust under `.data/`. Touches
  `place_meta`, all browse/render scripts, design.kb, and README.
  Ergonomic cost: `cat date/$TITLE.md` → `cat date/$TITLE/chat.md`.
