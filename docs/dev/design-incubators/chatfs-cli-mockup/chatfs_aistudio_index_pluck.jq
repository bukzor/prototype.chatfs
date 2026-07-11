#!/usr/bin/env -S jq -rcf
# Pluck each ListPrompts index entry, one per line. A response body is
# the JSPB envelope `[[<entry>, ...]]`; `.[0][]` flattens straight to
# individual entries so downstream doesn't need to know how many
# response bodies were captured (i.e. doesn't need to care about
# pagination — see chatfs_aistudio_index_splat.py). Entries share
# ResolveDriveResource's PROMPT/METADATA schema (see
# chatfs_aistudio_conversation_massage_json) with an empty
# chunkedPrompt (index entries carry no turn content).
select(.method == "Network.responseReceived"
       and (.params.response.url | test("[./]MakerSuiteService/ListPrompts$")))
| .params.response.body
| strings  # 204, interrupted responses
| fromjson
| .[0][]
