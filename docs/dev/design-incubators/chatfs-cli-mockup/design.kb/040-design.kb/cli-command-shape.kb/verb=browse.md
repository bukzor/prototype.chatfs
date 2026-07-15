# verb=browse

`browse` captures live state from chatgpt.com via a real browser. The
implementation invokes `har-browse` — a Playwright/CDP harness that opens
a Chromium window, lets the page run, and records the CDP stream to
jsonl. Each browse command then plucks the recorded jsonl through a
verb-specific pluck function (`chatfs_<provider>_layout.pluck_*`, built
on `chatfs_layout.iter_responses_matching`) to produce the captured JSON.

## Commands

- `chatgpt index browse` — loads `https://chatgpt.com`, captures the
  sidebar's `/backend-api/conversations` paging traffic, plucks each
  page to stdout (jsonl, one page per line). See `noun=index.md`.
- `chatgpt conversation {url,path} browse` — loads
  `https://chatgpt.com/c/$UUID`, captures the conversation traffic to
  `.data/cdp.jsonl`, plucks to `.data/conversation.json`. See
  `noun=conversation.kb/verb=browse.md`.

## Naming rationale

`browse` over `capture` or `fetch`. A user typing `chatgpt index browse`
sees a Chromium window pop open and pages of the sidebar scrolling by —
`fetch` reads as a quiet HTTP call, `capture` reads as a passive
side-channel; `browse` accurately signals that a real browser session
is about to start. Reducing user surprise outweighs CLI-verb convention
here.

Implementation consequence: every browse command is non-deterministic in
wall-clock cost (Chromium startup, page render, network) and requires
an authenticated session. Determinism applies to *outputs* via
re-capture rebuild semantics, not to capture latency. See
`../deterministic-regeneration.md`.

## Browse-incidental capture

A single browse session captures more than its named target — any
traffic the loaded page generates lands in the same cdp.jsonl. The
URL-browse command exploits this to populate `.data/meta.json` from the
sidebar's index requests without a separate `index browse` step. The
practice and its constraints live at `../browse-incidental-capture.md`.
