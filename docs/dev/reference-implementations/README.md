# reference-implementations/ - Third-Party Code for Reference

Git submodules of external repositories kept for reference and comparison.

## What Belongs Here

**External code repositories** tracked as git submodules:

- Reference implementations to study
- Alternative approaches for comparison
- Archived implementations for historical context
- Potential dependencies we're evaluating

These are NOT installed as dependencies (use pyproject.toml for that). They're
here to read, study, and reference during development.

## Current Contents

- **unofficial-claude-api** (st1vms) - Working implementation, uses curl_cffi
  for Cloudflare bypass
- **claude-api-py** (AshwinPathi) - Alternative implementation using urllib
- **claude-unofficial-api** (Explosion-Scratch) - Historical TypeScript
  implementation

See [CLAUDE.md project instructions](../../../CLAUDE.md) for detailed rationale.

## What Doesn't Belong Here

- Our own code (goes in lib/)
- Actual dependencies (declared in pyproject.toml, installed via uv)
- Binary artifacts or compiled libraries
- Temporary experiments (goes in design-incubators/ or gets deleted)

## Usage

Initialize submodules:

```bash
git submodule update --init --recursive
```

Update a submodule:

```bash
cd docs/dev/reference-implementations/unofficial-claude-api
git pull origin main
cd ../../../..
git add docs/dev/reference-implementations/unofficial-claude-api
git commit -m "Update unofficial-claude-api reference"
```

## When to Add a Reference

Add a submodule here when:

- Studying how others solved similar problems
- Comparing different architectural approaches
- Preserving historical context for design decisions
- Evaluating potential dependencies

Don't add if:

- It's a direct dependency (use pyproject.toml)
- It's just documentation (bookmark or save PDF)
- You won't reference it during development
