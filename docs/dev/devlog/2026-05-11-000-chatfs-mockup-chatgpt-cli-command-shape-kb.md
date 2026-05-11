# 2026-05-11: chatfs-mockup-chatgpt — cli-command-shape kb landed

## Focus

Land `design.kb/040-design.kb/cli-command-shape.kb/` — the noun-verb
model sub-kb planned in `.claude/todo.kb/2026-05-05-002-…`. Promote
listing-heavy `cli-command-shape.md` to a summary + companion kb,
capture per-partition rationale, gut the listings from the summary.

## What Happened

**User had a first draft.** Reviewed the existing skeleton: top-level
`CLAUDE.md`, `noun=index.md`, `noun=conversation.md`, `verb=splat.md`,
plus a sub-kb `noun=conversation.kb/` with `verb=browse.md`,
`verb=render.md`, `locator=path.md`, `locator=url.md`. The shape was
partition-rationale, not the script-inventory I'd proposed earlier in
the conversation. The user's framing is sharper: entries exist when
there's durable rationale spanning more than one command at a
partition prefix, not just because a command exists.

**Hive-style `key=value` naming.** Paths are partition prefixes:
`noun=conversation.kb/verb=browse.md` reads as "rationale at the
conversation × browse partition prefix". Documented in the kb's
CLAUDE.md. Deviates from llm-kb's kebab-case convention but is
self-consistent and intentional.

**Three rounds of cleanup.**

1. *Initial pass.* Added `last-updated` to summary frontmatter,
   de-duped the `splat as a verb` section from the summary into
   `verb=splat.md`, added `verb=browse.md` at top level (browse-over-
   capture-over-fetch rationale + commands list + browse-incidental
   notes).
2. *Listings cut.* User flagged that the summary still had substantial
   duplication: the Hierarchy code block (subcommand-path listing) and
   the script-names-on-PATH table (cell→script listing) were pure
   enumerations — `ls cli-command-shape.kb/**/*.md` plus the
   naming-conventions rule covered both. Gutted them. Restructured
   the summary into partition-vocabulary glossary + "Why explicit
   locators" policy + naming-conventions rule + kb pointer. Also
   removed two `Currently: $FILE` enumerations from the kb's CLAUDE.md
   (llm-kb anti-enumeration rule for maintenance guides).
3. *Terminology fix.* User flagged that "cell" was wrong — these are
   CLI commands. Renamed 16 occurrences across kb + todos to
   "command" (preserving plural/case).

**Sibling-doc cross-links added.** `stdio-pipeline-shape.md` and
`chat-as-directory.kb/pipeline-implications.md` both inline-name
scripts. Added a one-paragraph cross-link at the top of each, pointing
at `cli-command-shape.md` + `cli-command-shape.kb/` for the
noun-verb-locator framing. Stdio shape and chat-as-directory
consequences are orthogonal axes to noun-verb partitioning; the
cross-links make the orthogonality explicit.

## Lessons

**Partition-rationale is sharper than script-inventory.** My instinct
was per-command (per-cell) script-inventory — one file per concrete
command. The user's draft is per-partition-prefix rationale: a file
exists only when there's durable rationale that doesn't fit inline.
The bar is "spans more than one command at the prefix AND >50 tokens".
Result: 10 entries instead of 7+, but each one carries content that
wouldn't fit anywhere else. Script-inventory would have been
listing-heavy and would have grown brittle — the very problem the kb
was meant to solve.

**Listings duplicate the kb structure.** A Hierarchy code block lists
every subcommand path; a script-names table lists every kebab
translation. Both are pure enumerations that `ls` + the naming rule
already cover. A summary file should describe themes and policy, not
enumerate instances. The duplicate was hiding in plain sight under
section headings ("Hierarchy", "Script names on $PATH") that sound
substantive enough to keep. They weren't.

**Bullets carry two kinds of content; separate them.** The original
Hierarchy bullets mixed concept-definitions ("Sub-nouns disambiguate
locator type") with design-rationale ("we prefer explicit sub-nouns
over polymorphic single commands because…"). Definitions are
glossary-shaped and belong in the summary. Rationale belongs in the
kb (per-partition entries) — unless it's cross-partition policy, in
which case it gets a dedicated subsection in the summary. The
"explicit locators" policy is exactly that case.

**The matrix-cell metaphor seduced me into the wrong term.** Calling
the leaf nodes of the noun×verb×locator cube "cells" felt natural —
that's what they are in matrix terms. But "cell" is internal jargon
for a concept the user already has a name for: "command". User-facing
names beat internal-shape names. Worth remembering for the next
structural doc where I'm tempted to mint a fresh term.

## Next Session

- **Multi-provider sketch** (`chatfs.demo/claude/` parallel to
  `chatgpt/`) is the next natural step in the project todo. The new
  kb is incubator-scoped; multi-provider sketch is where it gets
  promoted to project level alongside `provider-plugin-model.md`.
