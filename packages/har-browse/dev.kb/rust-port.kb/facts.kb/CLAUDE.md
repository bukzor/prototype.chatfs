# Facts (Rust port)

Observable givens informing the port. Each file describes one fact: a verifiable property of the existing system, the target Rust ecosystem, or a constraint the port inherits.

## What belongs here

- Properties of the current Node/Playwright implementation
- Properties of the target Rust ecosystem (crate capabilities, gaps, known issues)
- Constraints / threat-model givens the port inherits unchanged

## What does NOT belong here

- Choices we're making for the port → `../decisions.kb/`
- Plans for future work → charter or `../commits.kb/`
- Speculation without verifiable source

Each fact should be citable: name the source (file path, issue URL, manifest, etc.) so it can be re-verified.
