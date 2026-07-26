# sbin -- tools we build for ourselves

Scripts the humans and agents working on har-browse run by hand:
capture forensics, live-session probes, one-off experiments that turned
out to be worth keeping. Not shipped, not imported by `src/`, not part
of the test suite.

**Look here before writing an analysis script.** The reflex to pipe a
throwaway heredoc into `python3 -` is how the same capture parser gets
rewritten five times in one session and thrown away four. If a tool here
almost does what you need, extend it and commit; the next agent inherits
the improvement instead of the reflex.

## Conventions

- Executable, with a shebang; `chmod +x`.
- A header comment stating what question the tool answers, and the
  invocation. That comment is the interface -- there is no `--help`
  discipline here and no test suite to encode intent.
- Prefer reading this package's `{method, params}` JSONL: from a path
  argument, else stdin, so tools compose with `har-browse` directly.
- Record hard-won facts in comments where they will be re-learned
  otherwise. `capture-report.mjs` explains why it reads
  `requestWillBeSentExtraInfo` rather than `requestWillBeSent`, because
  measuring the wrong one costs an afternoon.
- Cross-package tools belong in a repo-root `sbin/`, not here.

Throwaway really is throwaway: scratch that answers one question and
dies goes to `trash/`, which is gitignored. The test is whether the next
session would want it.

`ls` is the inventory; each tool's header comment says what it answers.
