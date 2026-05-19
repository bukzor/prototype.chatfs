# Commit granularity is bounded by test-assertion change

Commits should be as small as possible, with one floor: each commit
must change at least one test assertion — add a new one, strengthen
an existing one, or fix one that was failing. "Meaningful" here means
"extant," not "large."

The principle excludes **dead-infra commits**: a parser change with
no test that exercises it; mechanism code that has no failing test
motivating it. Parser + handler + smoke-test land together when no
intermediate split has its own asserting test.

## Why

The asserted-invariant set is the executable summary of what the
codebase guarantees. A commit that doesn't change this set has not
moved the system's guarantees — and therefore has no behavioral
content visible to a future reader. Such commits dilute `git log`,
inflate review surface, and offer no bisection signal.

Bisection in particular: each commit can be characterized by "this is
when assertion X started holding." Machinery committed without a
test that uses it is unbisectable for that machinery — the failure
mode only manifests later, when something tries to use it.

## Practical consequences

- **Parser change + handler change + test land together** when
  neither half has a meaningful intermediate assertion. Splitting
  them feels modular but is dead infra in both halves.
- **A `n` counter on a server response lands with the assertion that
  consumes it.** The counter alone has no behavioral content.
- **Mechanism that snapshot-defers BARRIER lands with the smoke test
  that asserts BARRIER FIFO** — not as a prep commit followed by a
  test commit.

## Where this differs from "atomic commits"

The conventional "atomic commit" view says one logical change per
commit. This principle is stricter: a commit must produce a
*verifiable* logical change — verifiable means asserted in test. A
parser change is atomic but not verifiable on its own; under this
principle it bundles with the user that does the asserting.

## When the principle doesn't apply

Refactors that intentionally preserve all assertions don't change any
test. Those are legitimate commits — but label them explicitly
("refactor, no assertion change") rather than mixing them with
assertion-changing commits.

## Source

Emerged in the 2026-05-12 BARRIER landing planning, when a
five-commit plan was compressed to four by removing the
parser-only-no-test step.
