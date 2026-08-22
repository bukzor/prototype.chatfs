---
managed-by: Skill(llm-subtask)
cost-benefit-sweh:
  timebox:
    "@value": 1.0
    rationale: |
      Seven of the twelve are mechanical (one schema file, one enum
      value, one legacy-shape rewrite). The other five wait on rulings
      in another repo and cost nothing here until those land.
  benefit-2w:
    "@value": 1.0
    rationale: |
      `llm.kb-validate` is only useful at zero. A tree that reports
      twelve known-benign errors trains everyone to skim the output,
      and the thirteenth -- the real one -- rides in unnoticed.
---

# Clear the twelve frontmatter validation errors

`llm.kb-validate .` reports 12 errors across this repo. They are five
distinct causes, not twelve problems. Surveyed 2026-08-22 during the
fleet-wide schema sweep.

## Fixable here, now (7)

- **3 x `No schema found`** -- `docs/dev/background.kb/` has no sibling
  `docs/dev/background.jsonschema.yaml`. Write it from the keys the
  three files actually carry.
- **3 x `kind: investigation`** -- not in the `kind` enum of
  `docs/dev/sources.jsonschema.yaml`. Either widen the enum or
  re-classify the three files; read them before choosing.
- **1 x legacy field shape** --
  `docs/dev/questions.kb/how-does-this-serve-chatfs.md` carries an
  unquoted `resolved:` date and a stray `status`, both from a schema
  revision that passed it by.

## Waiting on rulings in bukzor-agent-skills (5)

- **3 x `.claude/todo.md` roll-up** -- same class as the 47 across the
  fleet. Ruled: the fields live, and a file may name its own schema via
  the `# yaml-language-server` modeline (`MODELINE_SELECTS`,
  `llm-kb/claims.kb/design.claims.kb/a-file-may-name-its-own-schema.md`).
  Clears the moment `llm.kb-validate` honours the modeline
  (`VALIDATE_ENFORCES`); nothing to do here first.
- **2 x `status` enum drift** -- `exploring` and `active`, from no
  vocabulary at all. Blocked on `STATUS_ENUM`
  (`llm-kb/claims.kb/design.claims.kb/status-is-four-enums-under-one-name.md`),
  which is open: `status:` is four incompatible enums under one name,
  and picking a word here before that closes is a rename that teaches
  nobody anything.

## Not a cause

Migration `2026-08-21-002` did **not** leave this tree's `why:` slugs
unresolved; it resolved all three, and
`packages/chatfs-cli/design.kb/` validates clean. What it deliberately
deferred was the `status`/`blocked-on`/`superseded-by` trio, which is
the second bullet above.
