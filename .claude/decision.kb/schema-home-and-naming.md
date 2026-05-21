# Schema files: `./schema/` directory, stem-matching filename convention

JSON-schema files for har-browse-owned JSONL streams live in a `schema/`
directory under the owning package.

## Location

- **Final home (post-port):** `packages/rs-har-browse/schema/`. The
  schemas are owned by har-browse per `decision.kb/bb1-is-har-browse.md`.
- **Transitional home (during port):** may live at
  `packages/har-browse/schema/` and migrate to `rs-har-browse/schema/`
  as part of the "port all docs" cutover step before commit `1300`
  deletes the Node implementation.

## Naming convention

- `<stem>.jsonschema.yaml` validates the file with the matching stem.
- Stem-match is both **literal** (the schema validates a file with that
  exact name) and **conceptual** (the stem is the canonical name for
  the content category).
- Tests use a tmp cwd so a fixed filename for the output stream is no
  impediment — schemas can require matching filenames without
  constraining production deployments.

## Examples

- `cdp-jsonl.jsonschema.yaml` validates `cdp-jsonl.jsonl` (the
  CDP-event stream output by har-browse).
- `diagnostic-jsonl.jsonschema.yaml` (or similar) validates the
  diagnostic-event stream — see
  `decision.kb/separate-diagnostic-stream.md` for the rationale on
  why this is a separate file at all.

## Format

YAML for JSON Schema (anchors + comments justify the overhead vs
JSON).

Decided 2026-05-21.
