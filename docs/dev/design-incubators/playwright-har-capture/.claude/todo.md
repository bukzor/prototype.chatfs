---
anthropic-skill-ownership: llm-subtask
---

- [x] M0 — Manual Baseline (toy server, conversation fixture, XHR on load)
- [x] M1 — HAR Capture (Playwright captures valid HAR with /, index.js, api/conversation)
- [ ] M2 — Triggered Refresh (script injects button, human clicks to finalize, HAR has ≥1 api/conversation)
  - [x] Basic injection: button appears on initial page load
  - [x] Persistent injection: button survives page navigations (login redirects, multi-page flows)
  - [ ] howto-overlay: `--howto instructions.md` injects site-specific guidance into overlay
- [x] M3 — Extraction (toy_pluck.sh: jq filter, stdin HAR → stdout JSON, handles base64)
- [ ] M4 — Markdown Emission (toy_emit: extracted.json → branch-main.md, branch-alt.md)
- [ ] M5 — Adversarial Cases (latency, mixed encodings, large payloads, interrupted captures)
