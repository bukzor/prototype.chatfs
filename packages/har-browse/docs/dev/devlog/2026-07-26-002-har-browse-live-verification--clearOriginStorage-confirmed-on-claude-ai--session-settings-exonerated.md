# Devlog: 2026-07-26 — har-browse live verification: clearOriginStorage confirmed on claude.ai, session settings exonerated

## Focus

Close the live-verification step left open by `2026-07-26-001`: does the
`clearOriginStorage` fix work against the real claude.ai, and does login
survive? Five human-driven captures against one conversation in one
persistent profile, streams kept in `trash/live-verify/`.

Answer: yes, and the runs corrected two things I believed.

| run | build | `--clear-origin-storage` | entered via | conversation requests |
|-----|-------|--------------------------|-------------|----------------------|
| 1 | fixed | no | Recents, then clicked in | 1 (198115-byte body) |
| 2 | pre-fix (`fb60208^`) | n/a | cold load of the chat URL | **0** |
| 3 | fixed | no | cold load | **0** |
| 4 | fixed | **yes** | cold load | 1 (198115-byte body) |
| 5 | fixed | **yes** | cold load | 1 (198115-byte body) |

Run 2 is a clean reproduction: the human watched the conversation render
while the capture recorded no request for it. Runs 4 and 5 are the fix,
on consecutive captures, with no re-auth -- an authenticated `200`
carrying real conversation content is itself the proof that cookies
survived the clear. The human independently reported run 4 loading
visibly slower than the hydrating runs, which is the mechanism surfacing
as something a person can see.

Run 1 also caught the Recents index paginating to completion: 29
responses with `has_more: true` at 30 items each, then a terminal page
with `has_more: false` and 3 items, 873 conversations in all. That is
the `has_more=false` terminal condition the sibling drain-race todo
(`2026-07-22-000-*`) has been waiting on a live capture to observe.

## Decisions

### The per-session settings do not fix this bug, and saying otherwise would have been wrong

`2026-07-26-001` shipped `Network.setCacheDisabled` and
`Network.setBypassServiceWorker` alongside the storage clear, framed as
one family of fix. Run 3 has both settings and still captures zero
conversation traffic. Neither capture contains a single
`Network.requestServedFromCache` event or a `fromServiceWorker`
response, so for claude.ai these settings address neither path.

They stay -- the gap classes they target are real, and the local tests
prove they work against fixtures that exercise those paths -- but they
are unvalidated against any live provider, and this bug is not evidence
for them. The taskfile and mutation entries now say so.

**Alternatives considered:** leaving the original framing, on the
grounds that the bundle works. Rejected: it would leave a false
attribution in the record, and the next person to trust it would skip
the clear and ship silently empty captures.

### Verification must cold-load the artifact's own URL

Run 1 fetched the conversation and I first read that as the fix working.
It was not: run 1 entered by clicking through from Recents, a
client-side route change that fetches regardless of what sits in
IndexedDB. Only a cold load of the chat URL runs the parse-time
hydration path.

That was a flaw in my experiment, not a subtlety of the app. Any future
check of this behavior -- including the pending chatgpt/aistudio pass --
must navigate directly to the artifact's own URL or it measures nothing.

### The control has to be the pre-fix build

Establishing that the bug was still live meant running the pre-fix tree:
a throwaway git worktree at `fb60208^` with node_modules symlinked in.
Cheap, and it turned "the bug did not reproduce" into "here is the run
where it does". Run 3 (fixed build, no flag) was still needed to
separate the flag from the session settings, but it could not have
established that the bug was live in the first place.

**Alternatives considered:** reasoning from run 1 plus the local
fixtures. Rejected as circular -- the fixtures encode my model of the
bug, so they cannot test that model. Only a run that could fail counts.

## Conventions Established

- A control run means the pre-change build, not the new build with the
  feature switched off. The two differ by everything else that shipped
  alongside, which is exactly what confounded run 1.
- When a capture-completeness claim depends on how a page was reached,
  the navigation path is part of the experimental protocol and belongs
  in the write-up. "Opened the conversation" was not a sufficient
  description of what run 1 did.

## Open Questions

- Should `--clear-origin-storage` default on? A cold-load claude.ai
  capture without it is silently empty of its payload, which is what the
  data-possession mission forbids. Against: it clears app storage every
  capture, including locally held drafts, and slows the load.
  Recommendation recorded on the taskfile as yes for provider flows;
  left off pending the user's call.
- Do chatgpt and aistudio hydrate equivalently? Untested. Same protocol,
  cold-loading a conversation URL on each.
- Does the index page hydrate the same way? Run 1 paginated live, but it
  was a Recents-first navigation, so the cold-load question stays open
  for the index.

## References

- `.claude/todo.kb/2026-07-22-001-*.md` -- Live Verification section
  carries the same matrix
- `docs/dev/devlog/2026-07-26-001-*.md` -- the implementation this
  verifies and the attribution it corrects
- `.claude/todo.kb/2026-07-22-000-*.md` -- the `has_more=false`
  discriminator this run's index pagination speaks to
- Streams: `trash/live-verify/run{1..5}*.jsonl` (gitignored, ~130MB)
