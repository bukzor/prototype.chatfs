# Policy-Safe Automation Boundary

The architecture's separation of "live mount" from "sync" is not just a
technical choice — it's a policy boundary that determines what assistants can
help with.

**Allowed (assistants can help):**
- Tooling that guides and records what user manually does in-browser
- Local processing of artifacts obtained manually
- Capture mechanics that don't drive navigation or replay requests
- Filesystem materialization, indexing, caching, rendering
- Launching tabs with instructions, watching for files
- Everything after the HAR/artifact hits disk

**Not allowed (assistants must refuse):**
- Any step where a script causes the service to return data (even with valid
  cookies/tokens)
- Extracting tokens/cookies for browserless retrieval
- Background scraping triggered by filesystem reads
- Designs aimed at unattended bulk retrieval
- "Gradually reducing interactive bits" toward automation

**Why reads must never trigger network:**
From the service's perspective, `ls`/`grep` generating requests is
indistinguishable from automated scraping. `ls` causes many reads (readdir,
getattr, prefetching). Even "you typed the command" produces traffic patterns
that are "agentic automation."

**The crisp rule:**
Only allow network when the user performs an explicit "sync" operation that is
not a normal filesystem read. Enforce minimum interval and
one-tab/one-conversation scope per sync.

This boundary is what makes the architecture durable — it continues working as
long as manual web access continues working. UI changes rarely break it because
the only dependency is "user can open conversation and export/capture artifact."
