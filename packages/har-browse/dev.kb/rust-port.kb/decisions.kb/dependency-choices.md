# Decision: dependency picks

Three external dependencies + one vendored snippet, in `playwright-lite`.

## Chosen

- **`chrome-for-testing-manager`** — Chrome binary acquisition via Google's CfT manifest. Decoupled from CDP framework; we ignore its `thirtyfour` glue.
- **`chromiumoxide`** — CDP wrapper. Handles target auto-attach automatically and recursively (see `../facts.kb/ecosystem-survey.md`).
- **Vendored `chrome-launcher` `DEFAULT_FLAGS`** — copied verbatim from `GoogleChrome/chrome-launcher` at a pinned upstream commit SHA. Drift monitored at runtime (see `assertion-strategy.md`).

## Rejected

- `headless_chrome` — worse iframe/worker coverage, 142+ open issues.
- `fantoccini` — WebDriver only, no response bodies.
- `playwright-rust` forks — wrap the Node Playwright driver; defeat the port's purpose.
- `playhard` / `patchright` — closest near-miss, but locates pre-installed Chrome (not CfT) and reimplements CDP transport (not on chromiumoxide).
- `chrome_launcher` crate (chouzz) — stale Rust port, 2 commits ever. Reference only, not dependency.
- Git submodule for the flag list — overhead disproportionate to 27 lines of data.

## Why vendor instead of subtree/submodule

The flag list is ~27 string literals. Vendoring keeps the array visible in code review, version-controls cleanly, and a runtime assertion catches drift. Submodule machinery is built for tracked subprojects; this is a tracked snippet.
