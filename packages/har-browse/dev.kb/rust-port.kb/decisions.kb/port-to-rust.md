# Decision: port har-browse to Rust

Migrate the JS/Playwright implementation to Rust.

## Rationale

- **Testing pain.** Async-event-stream testing in Node is awkward; Rust's `tokio::test` + typed channels + `serde_json` make event-shape assertions natural.
- **Race-condition debugging.** Untyped async + callback timing in JS has been a recurring source of bugs in BARRIER / causal-watermark work. Rust's type system encodes state-machine transitions where JS leaves them implicit.
- **Weak types.** Current code is `@ts-check` on `.mjs` — the weakest possible TS coverage. Cannot enforce invariants on CDP event shapes.
- **Bit-rot risk.** Untyped async JS rots faster than Rust over months of inactivity.
- **Cross-language friction.** The rest of chatfs (`chatfs-fuser`) is Rust. Rust → Node shell-out is the seam where everything else breaks.

## Alternative considered

Stay on JS, harden TS coverage. Rejected: pain points compound, and even fully-typed JS doesn't solve the cross-language seam.

## Trade-off

~3–4 focused sessions of porting work. JSONL output contract acts as the regression gate.
