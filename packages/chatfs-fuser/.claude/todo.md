<anthropic-skill-ownership llm-subtask />

# chatfs-fuser

- [ ] Dynamic routing — lazy inode allocation, replacing build-time `dir_each`
  - After: update README.md (API section, examples, FAQ) to reflect new API
  - Design validated in Python sketch; see `docs/dev/design-incubators/fusefs-dynamic-routing/`
  - Policies: `docs/dev/technical-policy.kb/{stateless-re-evaluation,posix-error-semantics,inode-lifecycle}.md`
  - [ ] Lazy inode table: assign inodes in lookup/readdir, not at build time
    - `DynamicDir` (list + template callbacks), `StaticDir`, `File` entry types
    - Stateless re-evaluation: resolve path from root on every access
  - [ ] ESTALE handling: distinguish "inode exists but path no longer resolves"
    from "inode never existed" (ENOENT)
  - [ ] `entry_valid=0` / `attr_valid=0`: force kernel to re-validate on every access
  - [ ] Correct `readdir` `..` inode — derive parent from `ino_to_path`
    - Currently hardcoded to inode 1; path table makes this trivial

