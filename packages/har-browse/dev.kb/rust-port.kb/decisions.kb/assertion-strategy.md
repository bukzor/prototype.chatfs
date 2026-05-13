# Decision: runtime assertions against deferred work

We defer three implementation tasks to *future work*, gated by runtime assertions that fire precisely when the deferred work becomes necessary.

## The pattern

For each known limitation:

1. Record it as a deferred future-work item.
2. Add a runtime/test-time assertion that detects when reality crosses into the limitation's scope.
3. When the assertion fires, the deferred work moves to active.

Trades pre-emptive code for monitoring. Ensures we don't pay for solutions to problems we may never hit.

## Three assertions

### Flag drift

- **Limitation deferred:** CI job that diffs vendored `DEFAULT_FLAGS` against upstream.
- **Assertion:** vendor records `UPSTREAM_SHA`. Periodic check (test target or release-time) queries GitHub for the latest commit touching `chrome-launcher/src/flags.ts`. Failure if it post-dates `UPSTREAM_SHA`.
- **Triggers:** any drift. Coarse; refine to path-filtered if noisy.

### Iframe-URL gap (chromiumoxide #280)

- **Limitation deferred:** raw `AttachToTargetParams` workaround for cross-origin iframe URL retrieval.
- **Assertion:** on `Target.attachedToTarget`, if `targetInfo.type == "iframe"`, assert non-empty `targetInfo.url`. Asserts in real captures.
- **Triggers:** the workaround becomes worth writing.

### Chrome version drift

- **Limitation deferred:** re-verifying the vendored flag list applies to the in-use Chrome version.
- **Assertion:** after launch, compare `Browser.getVersion` product string to the CfT-fetched version. Warn or fail on mismatch (e.g., user overrode binary path).
- **Triggers:** flag-list applicability stale.

## Why this pattern is worth the line count

Cheaper than the deferred work, *and* gives a precise trigger for when the deferred work earns its cost. Avoids speculative implementation.
