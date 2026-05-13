# End-of-commit procedure

After a commit lands (or is about to land).

## Steps

1. In `commits.kb/NNNN-slug.md`, tick all completed `## Outcomes` boxes. If the
   commit landed but criteria shifted (new ones added, original ones obsolete),
   update the list and explain the shift in `## Notes`.
2. If any emergent surprises arose during implementation, capture them in
   `## Notes` (distinct from Outcomes).
3. Delete any `handoffs.kb/*.md` entries this commit consumed. See
   `consume-handoff.md` for the promote-vs-delete decision.
4. If the upcoming commit needs context from this one that doesn't fit in the
   commit doc, write a `handoffs.kb/$topic.md` (see `../handoffs.kb/CLAUDE.md`
   for triggers and format).
5. If commit scope diverged materially from the charter TOC, update
   `dev.kb/rust-port.md`.
6. Update `$PWD/.claude/focus.md` to the next commit doc.

## Trigger

A commit has landed. Run before moving to the next commit.
