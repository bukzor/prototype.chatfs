---
why:
  - no-network-on-read
  - explicit-sync-triggers
background:
  - google-piper-precedent
source:
  - conversations.cleaned/06-design-spec-project-handoff/167.assistant.text.md#4
  - conversations.cleaned/05-fuse-implementation-details/159.assistant.text.md
---

# Work-Enqueueing Model

FUSE handlers must stay fast. Expensive work (BB pipelines, user interaction,
file parsing) runs in a background job queue, not in the filesystem call path.

```
touch file / echo sync > control
         |
FUSE handler enqueues job
         |
async task queue
         |
job runs BB1 -> BB2 -> BB3
         |
writes to staging/<jobid>/
         |
atomic rename: staging -> current
         |
FUSE reads serve new content
```

**Job lifecycle:** Each sync trigger enqueues a job keyed by
`(provider, conv_ref)` with deduplication — if a job is already running for
that key, return "in progress."

**Job states:** `idle`, `syncing`, `waiting_user`, `failed`, `done`. Exposed
via `status` control file.

**Failure semantics:** Failures never corrupt cache. They update status and
preserve artifacts/logs for debugging. Last-known-good `current/` is untouched.

**Prior art:** rclone mount, Google Piper workspace mounts — both use this
pattern of thin filesystem layer + background workers.
