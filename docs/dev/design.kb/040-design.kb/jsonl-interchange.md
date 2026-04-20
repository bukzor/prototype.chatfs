---
why:
  - pipeline-composability
---

# JSONL Interchange

Pipeline stages pass data as JSONL — one JSON object per line, UTF-8, no
surrounding array. Applies wherever streaming composition matters: BB1 → BB2
→ BB3, and any CLI tool in the pipeline family.

Each stage reads JSONL from stdin or a file, writes JSONL to stdout (except
the final render stage, which emits markdown).

## Why JSONL

- **Streaming.** A downstream stage can start processing as soon as the first
  line arrives; producers can flush incrementally.
- **Unix composable.** Works with `jq -c`, `grep`, `head`, `tail`, `wc -l`
  today — no custom tooling required.
- **Trivial tests.** `echo '{"test":"data"}' | tool | jq` is a one-liner.
- **Clean migration path.** When the system graduates to a binary format
  (capnproto, per `070-future-work.kb/capnproto-migration.md`), JSONL objects
  map directly to struct fields — it's a serialization swap, not a schema
  redesign.

## Alternatives considered

**Why not plain JSON (array-wrapped).** Consumers must parse the entire
structure before processing any element. Breaks `jq -c | head`-style
pipelines and any producer that wants to flush as it goes.

**Why not MessagePack / protobuf / capnproto now.** Binary formats require
schema tooling and capnshell-style adapters before they compose with standard
Unix tools. JSONL gets us to working pipelines today; binary is deferred
until the capnshell ecosystem exists.

**Why not YAML.** Multi-line values and significant indentation break
line-oriented processing.

**Why not NDJSON (the IANA-registered synonym).** Same format. "JSONL" is
more commonly used in the data-tool ecosystem we compose with (`jq`, `duckdb`,
`pandas.read_json(lines=True)`).
