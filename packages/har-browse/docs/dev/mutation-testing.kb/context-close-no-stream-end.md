---
status: gap
attempts: 1
---

# `capture.mjs`: `context.waitForEvent("close")` arm dropped from Done race

The Done race has two arms — `page.waitForFunction(... dataset.clicked)`
and `context.waitForEvent("close")` — so the events stream terminates
whether the user clicks "Done Capturing" or closes the browser window.
If the close arm is dropped, window-close leaves the consumer hanging
on the async iterator forever.

User-visible bug: `har-browse` CLI never exits if the human closes the
window instead of clicking the overlay button. No existing test
exercises this path.

## Injection

`src/capture.mjs`: remove `context.waitForEvent("close")` from the
`Promise.race([...])` arms (or change `Promise.race` to await only the
waitForFunction).

## Test Result

Marked gap after testing via `tests/initial_nav.spec.mjs`'s context-close
path. With the close arm removed, the test still passes in ~800ms.

Analysis: when `context.close()` runs, the page is torn down and
`page.waitForFunction(...)` rejects with "Target page, context or
browser has been closed". The `done` chain wraps the race with
`.catch(() => {})`, which swallows that rejection and proceeds to
`.finally(...)` → `emit('end')`. So waitForFunction's
rejection-on-close acts as a de facto close arm — the explicit
`context.waitForEvent("close")` arm is redundant.

The kb's predicted "await times out" doesn't materialize because the
.catch wrapper neutralizes the close arm's effect. Worth keeping the
explicit arm for clarity (and against future refactors that might
remove the .catch), but the runtime behavior is identical with or
without it.
