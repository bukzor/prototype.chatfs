# Commit 0750: jsonl-schema-spec (soft)

## What
Write the durable JSONL output contract as `dev.kb/jsonl-schema.md`. Doc-only commit.

## Plan
- Read existing `src/capture.mjs` to extract the observed wire shape.
- Document: one JSON object per line; `{method, params}` outer shape; `response.body` location and `encoding` semantics.
- Distinguish CDP-wire-derived fields (we commit to byte-equivalence) from har-browse-specific fields (our responsibility; document any).

## Refs
- `../facts.kb/current-architecture.md`
- `../decisions.kb/documentation-conventions.md` (durable contracts live at `dev.kb/` root)

## Outcomes
- [ ] `dev.kb/jsonl-schema.md` exists at the repo's primary `dev.kb/` location
- [ ] Schema document specifies: outer line shape (`{method, params}`), response-body location, base64 encoding flag rule
- [ ] Schema explicitly lists CDP-derived vs har-browse-specific fields
- [ ] Schema includes a byte-stability commitment statement that future changes to har-browse-specific fields require updating the doc first
