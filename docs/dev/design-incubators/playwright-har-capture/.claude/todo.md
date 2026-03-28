---
anthropic-skill-ownership: llm-subtask
---

- [x] M0 — Manual Baseline (toy server, conversation fixture, XHR on load)
- [x] M1 — HAR Capture (Playwright captures valid HAR with /, index.js, api/conversation)
- [x] M2 — Capture Overlay (persistent injected UI, howto instructions, human clicks to finalize)
  - [x] Basic injection: button appears on initial page load
  - [x] Persistent injection: button survives page navigations (login redirects, multi-page flows)
  - [x] howto-overlay: `--howto instructions.md` injects site-specific guidance into overlay
- [x] M3 — Extraction (toy_pluck.sh: jq filter, stdin HAR → stdout JSON, handles base64)
- [-] M4 — Markdown Emission (toy_emit: extracted.json → branch-main.md, branch-alt.md) — out of scope for incubator
- [-] M5 — Adversarial Cases — out of scope (trivial or belongs to downstream pipeline)
