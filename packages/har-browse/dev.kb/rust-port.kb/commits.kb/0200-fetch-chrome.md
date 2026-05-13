# Commit 0200: fetch-chrome

## What
Add `chrome-for-testing-manager` dep; expose `fetch_chrome() -> PathBuf`.

## Plan
- Add `chrome-for-testing-manager` to `playwright-lite/Cargo.toml`.
- Implement `binary::fetch_chrome(version: Option<&str>) -> Result<PathBuf>` returning a cached or freshly-downloaded Chrome binary path.

## Refs
- `../facts.kb/ecosystem-survey.md` (CfT crate; arm64/macOS caveat)
- `../decisions.kb/dependency-choices.md`

## Outcomes
- [ ] Integration test (gated on `network-tests` feature) downloads a stable Chrome and asserts the returned path exists
- [ ] Returned path is executable
- [ ] Second call with same version uses the cache (does not re-download)
- [ ] On the current host's arch/OS, the test passes; arches/OSes where it doesn't get a hand-off opened
