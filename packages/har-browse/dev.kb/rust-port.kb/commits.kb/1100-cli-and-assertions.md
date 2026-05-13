# Commit 1100: cli-and-assertions

## What
Full CLI surface (argv, XDG profile resolution) + the three runtime assertions wired up.

## Plan
- Argv parsing: `--profile <name>` (default `"default"`). Resolve via the `xdg` crate.
- Wire runtime assertions from `decisions.kb/assertion-strategy.md`:
  - Iframe-URL assertion on `Target.attachedToTarget`.
  - Chrome version drift: `Browser.getVersion` vs CfT-fetched version.
  - Flag-drift test target (added at `0300`; verify still passes).

## Refs
- `../decisions.kb/assertion-strategy.md`
- `../facts.kb/current-architecture.md` (profile path scheme)

## Outcomes
- [ ] `--profile foo` resolves to `${XDG_CACHE_HOME:-$HOME/.cache}/har-browse/profile/foo`
- [ ] `--profile` default = `"default"` (test that omitting the flag matches `--profile default`)
- [ ] Iframe-URL assertion fires (panics or asserts) when fed a synthetic `Target.attachedToTarget` with `type=iframe` and empty URL
- [ ] Chrome version drift assertion fires when launched against a binary whose version disagrees with the CfT-fetched record
- [ ] Flag-drift test from `0300` still passes
- [ ] Smoke pipeline against `toy_server/` with `--profile test-pipeline` succeeds end-to-end
