# Commit 0600: process-tree-and-noise

## What
Process-tree cleanup, stderr filter, `--disable-breakpad`.

## Plan
- Spawn Chrome with `pre_exec(|| setsid())`; capture PGID.
- `Drop` on the `Browser` wrapper: `SIGTERM` the process group, then `SIGKILL` after a short timeout.
- Add `--disable-breakpad`, `--disable-crash-reporter` to launch flags.
- Wire Chrome's stderr through a filter that drops well-known noise (GPU errors, font config).

## Refs
- `../facts.kb/unknown-unknowns.md`

## Outcomes
- [ ] Test: `launch()` then `kill -TERM` the parent — within 5 s, no Chrome child PIDs remain in the original PGID
- [ ] Test: stdout pipeline from `har-browse-rs` (or `playwright-lite` test bin) contains zero lines originating from Chrome stderr
- [ ] No minidump files appear under the profile dir after a forced kill
