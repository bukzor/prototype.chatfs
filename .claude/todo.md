<anthropic-skill-ownership llm-subtask />

# Tactical Tasks

- [x] chatgpt-splat quick fixes (batch)
  - [x] #8: `if create_time:` → `if create_time is not None:` in compute_min_timestamp and parse_messages
  - [x] #7: find_roots — assert isinstance instead of silent filter
  - [x] #10: remove `# type: ignore[index]` from tests — use isinstance narrowing
  - [x] #14: strengthen enumerate tests — assert message identity with `assert ... is ...`
  - [x] #9: replace test `_make_tree` with production `build_tree`
  - [x] #5: inline `write_all_messages` into `main()`
- [ ] #4: json `parse_float=Decimal` — eliminate float intermediary for timestamps
- [ ] #1: inspect empty text_content data, add test, decide fix for `extract_text_content` returning ""
- [ ] #6: convert enumerate_conversation_links recursion to stack-based iteration
- [ ] [#13: parse_messages unit-factor and mutation-testing](todo.kb/2026-03-12-000-chatgpt-splat-parsemessages-unit-factor-and-mutation-testing.md)
- [ ] [#12/#2: fork semantics discussion and tests](todo.kb/2026-03-12-001-chatgpt-splat-fork-semantics-discussion-and-tests.md)
- [x] Prompt engineering: update writing-python-code.md — `proc_` → "obvious side-effect verb"
- [x] Prompt engineering: add "inline trivial functions" to making-code-changes.md

## Pending (blocked on skill evolution)

- [ ] [Harmonize with llm-* skills](todo.kb/2026-01-02-000-harmonize-with-llm-skills.md)

## Later

- [ ] har2jsonl.py should use idiomatic json (`.json` module instead of stdlib `json`)
