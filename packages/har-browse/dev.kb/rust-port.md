# Rust port of har-browse — Charter

Migrate `har-browse` from Node/Playwright to Rust, in two layers:

1. **`playwright-lite`** — a small Rust crate bundling the Playwright-equivalent plumbing we depend on (Chrome binary fetch via Google's Chrome-for-Testing, curated launch flags, CDP wrapper via `chromiumoxide`).
2. **`har-browse-rs`** — port of the existing Node driver onto `playwright-lite`.

Final cutover deletes the Node implementation.

## Why

JS/Playwright pain points compound (see `rust-port.kb/decisions.kb/port-to-rust.md`): weak typing on async event streams, race-condition debugging, ergonomic cost of cross-language deps for the rest of the chatfs pipeline (Rust). Bit-rot risk if revisited cold in 8 months.

## Working stance

This charter and the commit docs in `rust-port.kb/` are a starting point, not a contract:

- **Improve as you go.** When you notice a better name, a cleaner split, an unneeded step, or a missed criterion — change it. The plan should track reality, not constrain it.
- **Rename aggressively.** Working names (`playwright-lite`, `har-browse-rs`, commit slugs, doc titles) are placeholders. Replace them when something better emerges; update references.
- **Plans aren't normative.** `## Outcomes` checkboxes are normative (definition of done). `## Plan` is just direction — change it if it stops fitting reality.
- **Suggest structural improvements proactively.** If a kb refactor (renaming, splitting, promoting a hand-off to a contract) would help, propose it.

## Strategy

Build the foundation first, port on top. The two crates can be developed and tested independently, and the crate boundary forces the CDP-to-JSONL contract to be frozen early.

## Commit TOC

Phase 1 — `playwright-lite` (6 commits):

- `0100` scaffold
- `0200` fetch-chrome (chrome-for-testing-manager)
- `0300` vendor-flags (chrome-launcher `DEFAULT_FLAGS` + drift assertion)
- `0400` launch (chromiumoxide integration; smoke test)
- `0500` profile-hygiene (`SingletonLock`, first-run prefs)
- `0600` process-tree-and-noise (`setsid`/`killpg`, stderr filter, breakpad)

Phase 2 — `har-browse-rs` port (7 commits):

- `0700` skeleton
- `0750` jsonl-schema-spec **(soft: doc-only)** — writes `dev.kb/jsonl-schema.md` before implementing against it
- `0800` cdp-to-jsonl (**JSONL contract freeze**)
- `0900` done-button (`Runtime.addBinding`)
- `1000` barrier-reentrant
- `1050` causal-watermark (multi-witness + range + body-integrity) — may split further into `1025`/`1075` if work reveals natural seams
- `1100` cli + runtime assertions

Phase 3 — cutover (2 commits):

- `1200` toy_pluck.sh bridges to Rust output (coexistence)
- `1300` retire Node implementation; update docs

15 commits total. `0N00` numbering allows insert-between via `0150`, `0825`, etc.

## Success criteria

- Rust har-browse captures equivalent JSONL on `toy_server` fixture (byte-stable for fields we control).
- BARRIER and causal-watermark invariants from the original Node implementation hold (see `rust-port.kb/facts.kb/current-architecture.md`).
- No Node toolchain dependency at runtime.

## Out of scope

- Headless mode (har-browse is real-browser-first; see `rust-port.kb/facts.kb/threat-model.md`).
- Bot-detection mitigations.
- Publishing `playwright-lite` to crates.io.

## References

- `rust-port.kb/facts.kb/` — observable givens
- `rust-port.kb/decisions.kb/` — choices made for this port
- `rust-port.kb/commits.kb/` — per-commit records (populated as work progresses)
- `rust-port.kb/handoffs.kb/` — inter-session hand-offs (ephemeral)

## End state

At commit `1300`: `rm -rf dev.kb/rust-port.md dev.kb/rust-port.kb/`. Anything worth preserving (JSONL schema, BARRIER invariants, assertion implementations) gets promoted to permanent docs in `dev.kb/` before the sweep.
