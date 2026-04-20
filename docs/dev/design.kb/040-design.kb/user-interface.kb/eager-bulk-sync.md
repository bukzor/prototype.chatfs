# Eager Bulk Sync to Plain Files

A periodic background job fetches every conversation and writes plain
markdown files to a local directory. Users then use any tool on the local
copy; there's no daemon, no mount, no lazy loading.

**Pros.** Extremely simple user model: "chatfs is a directory that gets
rsynced periodically." No daemon. Fully offline after sync.

**Cons.** Does not scale. Most users have hundreds-to-thousands of
conversations accumulated over time, most of which are never re-read. Eager
sync wastes bandwidth and burns provider goodwill (every sync hits every
conversation). Even if acceptable for one user, the per-user network cost
multiplied across users is not a defensible posture toward the provider.

This is a sync-strategy choice masquerading as a user-interface choice —
the user-facing surface is plain files either way. What distinguishes it is
the "sync everything, always" commitment, which is incompatible with lazy
loading (`020-goals.kb/lazy-filesystem.md`).
