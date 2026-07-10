# Idempotence falls out of purge + rm-rf, no flags needed

The whole splat/render pipeline is idempotent without any "is-newer-
than" gating, freshness caches, or `--force` flags:

- `path_render.purge_non_captured` removes everything except the
  `.data/` allowlist before invoking splat
- `splat` itself `shutil.rmtree`s `.data/conversation.splat/` before
  writing it
- `place_meta` purges existing view symlinks by UUID before writing
  a fresh one

Result: the second run wipes derived state and rebuilds it. Verified
twice now — chatgpt at scale (188-message rerender, byte-stable),
claude on a small test chat (md5
`251c88f6340c0d0bea53fb7970950701` stable across rerenders).

## Why this is worth recording

Earlier iterations of the pipeline had `is_newer_than` gates and
60-minute CDP caches. They got removed under
`docs/dev/adr/2026-04-29-000-no-freshness-caches.md`. The lesson:
**determinism beats freshness logic**. The cost of always re-deriving
is negligible compared to the bugs freshness-gates hide.

This holds because the input artifacts are byte-stable (captured
CDP, captured response bodies) and the derivation is pure. If either
became non-deterministic — e.g. a render step embedded a timestamp —
freshness gates would suddenly look attractive again. Don't go
back.
