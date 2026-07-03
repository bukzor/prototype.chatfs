# Browse orchestration belongs in the browse script, not `*_layout.py`

`chatfs_chatgpt_layout.py` and `chatfs_claude_layout.py` disagree with each
other on where the har-browse-and-pluck subprocess orchestration lives:

- chatgpt inlines it in `chatfs_chatgpt_conversation_path_browse.py` — no
  shared helper.
- claude factors it into `chatfs_claude_layout.py`'s `capture(url, chat_dir)`.

A first draft of `chatfs_aistudio_conversation_url_browse.py` followed
claude's precedent (added `capture()` to `chatfs_aistudio_layout.py`) and
was corrected: `*_layout.py`'s actual scope, consistent across all three
providers once you look past claude's outlier, is identity/path/placement
(`index_item`, `time_dir_for`, `chat_dir_for`, `place_meta`) — not process
orchestration. AI Studio's orchestration (capture → pluck → massage →
place_meta) lives directly in `chatfs_aistudio_conversation_url_browse.py`.

## Implication

Don't assume agreement between chatgpt and claude on structural questions
just because both are "the existing precedent" — check both before
following either. When they disagree, prefer whichever matches a module's
stated/documented scope over whichever is more recently written.
