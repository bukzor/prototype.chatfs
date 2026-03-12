---
why:
  - three-subsystem-pipeline
  - deterministic-output
---

# toy_emit — extracted.json → Markdown

Reads `extracted.json`, renders branch markdown files into an output directory.

## Interface

```
toy_emit <json-path> --outdir output/
```

## Output

- `branch-main.md` — Main conversation thread
- `branch-alt.md` — Alternative branch (from the fork in the fixture)

## Responsibilities

- Walk the conversation graph following parent pointers
- Identify branches (multiple children of one parent)
- Render each branch as markdown
- Atomic writes (write to staging, rename into place)

## Notes

Deliberately minimal. chatgpt-splat already validates complex rendering.
The value here is confirming the pipeline shape end-to-end.
