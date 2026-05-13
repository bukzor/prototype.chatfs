# Commit 0800: cdp-to-jsonl

## What
Implement CDP event → JSONL stream. **Freezes the JSONL contract** (per `0750`).

## Plan
- Subscribe to `Network.*` events across all attached chromiumoxide sessions.
- Serialize each as `{method, params}` JSON to stdout, one per line.
- Fetch response bodies via `Network.getResponseBody`; attach at `response.body` with `encoding = "base64"` when appropriate.

## Refs
- `dev.kb/jsonl-schema.md` (from `0750`)
- `../facts.kb/ecosystem-survey.md` (chromiumoxide event streams)
- `0400-launch.md`

## Outcomes
- [ ] Against `toy_server/`, every output line parses as JSON
- [ ] Every output line matches the outer shape specified in `dev.kb/jsonl-schema.md`
- [ ] Response bodies appear at the schema-specified location with correct `encoding` flag
- [ ] Diff against the Node implementation on the same fixture: zero differences on CDP-derived fields (any divergence is in har-browse-specific fields and is documented in the schema)
