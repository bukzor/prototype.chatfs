---
why:
  - toy-server
---

# M0 — Manual Baseline

Toy server running. Developer manually opens browser, visits localhost, confirms
endpoints work.

## Acceptance

- `toy_server` starts and serves `/` and `/api/conversation`
- Manual browser visit confirms page loads and conversation JSON renders
- No Playwright yet — this validates the target before automating
