---
anthropic-skill-ownership: llm-subtask
---

- [x] M0 — Manual Baseline (toy server, conversation fixture, XHR on load)
- [x] M1 — HAR Capture (Playwright captures valid HAR with /, index.js, api/conversation)
- [x] M2 — Triggered Refresh (script injects button, human clicks to finalize, HAR has ≥1 api/conversation)
- [ ] M3 — Extraction (toy_pluck: HAR → extracted.json, handle encodings)
- [ ] M4 — Markdown Emission (toy_emit: extracted.json → branch-main.md, branch-alt.md)
- [ ] M5 — Adversarial Cases (latency, mixed encodings, large payloads, interrupted captures)
