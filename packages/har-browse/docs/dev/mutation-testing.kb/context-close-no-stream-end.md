---
status: todo
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

## Fixture needed

Test that calls `startCapture`, closes the context programmatically
(`session.context.close()`) without clicking Done, and awaits
`session.done` with a short timeout. Without the mutation, `done`
resolves; with the mutation, the await times out.
