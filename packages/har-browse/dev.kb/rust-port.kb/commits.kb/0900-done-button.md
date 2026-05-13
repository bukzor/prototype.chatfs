# Commit 0900: done-button

## What
Inject the "Done" button; wire its click as the terminate signal.

## Plan
- Use `Runtime.addBinding` to expose `__harBrowseDone` per page on attach.
- Inject a page script via `Page.addScriptToEvaluateOnNewDocument` creating a fixed-position "Done" button that calls `__harBrowseDone()` on click.
- Driver listens for `Runtime.bindingCalled`.

## Refs
- `../facts.kb/current-architecture.md`
- `../facts.kb/threat-model.md`

## Outcomes
- [ ] After launch, every page has a visible fixed-position "Done" button
- [ ] Test: `Runtime.evaluate("__harBrowseDone()")` triggers shutdown of the capture loop
- [ ] On shutdown trigger, JSONL stream flushes any pending events before the process exits
- [ ] Process exits with status 0 on Done-button termination
