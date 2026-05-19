# Linter warnings name work to do

A warning from a linter, type checker, or compiler is signal: it
names a structural issue or one in the making. Default response is
to fix the underlying issue.

Suppression markers (`# noqa`, `# type: ignore`, `@ts-expect-error`,
`#[allow(...)]`) are reserved for cases where no other avenue
exists. When suppressing, scope tight (one line, one rule) and
justify inline.

A common pattern: a warning sticks around because the surrounding
work isn't complete — an unused import after a partial refactor, an
unreachable branch after a removed flag. The warning correctly
points at unfinished work; finishing the work resolves it.
