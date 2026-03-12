# Work-Enqueueing Model

FUSE handlers must stay fast. Expensive work (BB pipelines, user interaction,
file parsing) runs in a background job queue, not in the filesystem call path.

```
touch file / echo sync > control
         ↓
FUSE handler enqueues job
         ↓
Tokio task queue (async runtime)
         ↓
job runs BB1 → BB2 → BB3
         ↓
writes to staging/<jobid>/
         ↓
atomic rename: staging → current
         ↓
FUSE reads serve new content
```

**Job lifecycle:** Each sync trigger enqueues a job keyed by
`(provider, conv_ref)` with deduplication — if a job is already running for
that key, return "in progress."

**Job states:** `idle`, `syncing`, `waiting_user`, `failed`, `done`. Exposed
via `status` control file.

**Failure semantics:** Failures never corrupt cache. They update status and
preserve artifacts/logs for debugging. Last-known-good `current/` is untouched.

**Why async:** Modern FUSE servers run on Tokio or async-std. The `fuse3` crate
is explicitly async-first. This makes it natural to enqueue work and return
immediately from FUSE handlers.

**Prior art:** rclone mount, Google Piper workspace mounts — both use this
pattern of thin filesystem layer + background workers.
