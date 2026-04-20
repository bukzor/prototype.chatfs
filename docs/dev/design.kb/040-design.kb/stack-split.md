---
why:
  - black-box-decomposition
background:
  - fuse-filesystem
source:
  - conversations.cleaned/02-architecture-convergence/094.assistant.text.md
---

# Stack Split: Rust + Node/Playwright Sidecar

Two language runtimes, each owning what it's best at:

**Rust owns:** FUSE filesystem, cache layer, canonical format, markdown
generation, file watching, orchestration, provider plugin registry.

**Node/Playwright sidecar owns:** Browser interaction only. Attaches to
existing Chrome via CDP. Injects UI, captures payload, writes JSON, exits.
Single purpose: "extract conversation, write artifact, exit."

**Interface:** CLI args + JSON. Rust launches sidecar:
`capture_playwright --ref <conversation-ref> --out <artifact_path>`. Sidecar
writes artifact to disk; Rust watches and updates cache.

**Why not all-Rust:** Playwright's best bindings are Node (and Python). Rust
ports lag in features. Embedding JS runtimes in Rust balloons effort. The
pragmatic split keeps system code in Rust and delegates browser expertise to
Node.

**Why not long-lived sidecar:** One-shot CLI (Shape A) is recommended over
persistent agent (Shape B). Each capture spawns a fresh process — clean failure
semantics, no cascading failures, simpler packaging. If startup cost becomes
annoying, evolve to Shape B without changing the outer contract.
