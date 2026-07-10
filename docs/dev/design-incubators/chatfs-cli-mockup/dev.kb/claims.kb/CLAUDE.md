# claims.kb — assertions about external behavior, with status

A claim is something we believe (or are told) about how a live service,
tool, or data source behaves — distinguished from a learning by the
fact that **the world can refute it**. Status carries the burden:
`assumed`, `observed`, `refuted`, `settled`.

Belongs here:
- "Service X fires endpoint Y on action Z"
- "Tool foo emits format bar when ..."
- "The capture is complete iff condition C"

Does NOT belong here:
- Design decisions → `design.kb/`
- Observations that don't depend on external behavior → `learnings.kb/`

Each file is one claim. Frontmatter required (see
`claims.jsonschema.yaml`): `status:` and `last-checked:` at minimum.
When status changes (e.g. assumed → observed), update both fields and
add a brief note in the file body about what changed.

When a prior bad version of this claim was recorded somewhere (todo,
response, doc), capture it under the optional `previously-claimed:`
array in frontmatter. Verbatim quote helps future agents pattern-
match if they encounter the bad version elsewhere in the repo.
