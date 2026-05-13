# Commit 0400: launch

## What
Add `chromiumoxide` dep; expose `launch(profile_dir) -> Browser`.

## Plan
- Add `chromiumoxide` to `playwright-lite/Cargo.toml` (with `tokio-runtime` feature).
- Implement `launch::launch(profile_dir: &Path) -> Result<Browser>`: `fetch_chrome()` → `BrowserConfig` with `DEFAULT_FLAGS` + `user_data_dir(profile_dir)` → spawn + connect.

## Refs
- `../facts.kb/ecosystem-survey.md` (chromiumoxide capabilities)
- `0200-fetch-chrome.md`
- `0300-vendor-flags.md`

## Outcomes
- [ ] `launch()` returns a connected `Browser` against `toy_server/` running
- [ ] Integration test navigates to a known toy_server page and reads the expected `<title>`
- [ ] Returned `Browser` drops cleanly (no panic on shutdown)
