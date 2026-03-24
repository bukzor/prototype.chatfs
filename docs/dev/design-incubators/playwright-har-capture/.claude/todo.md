---
anthropic-skill-ownership: llm-subtask
---

- [x] M0 — Manual Baseline (toy server, conversation fixture, XHR on load+click)
- [x] M1 — HAR Capture (Playwright captures valid HAR with /, index.js, api/conversation)
- [ ] M2 — Triggered Refresh (click button, HAR has 2x api/conversation entries)
- [ ] M3 — Extraction (toy_pluck: HAR → extracted.json, handle encodings)
- [ ] M4 — Markdown Emission (toy_emit: extracted.json → branch-main.md, branch-alt.md)
- [ ] M5 — Adversarial Cases (latency, mixed encodings, large payloads, interrupted captures)
