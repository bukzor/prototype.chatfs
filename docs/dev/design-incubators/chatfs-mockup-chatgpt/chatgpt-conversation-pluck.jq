#!/usr/bin/env -S jq -rcf
# Pluck the /backend-api/conversation/{id} response body (one per line).
# Excludes sub-paths like /stream_status, /textdocs, /init.
select(.method == "Network.responseReceived"
       and (.params.response.url | test("/backend-api/conversation/[0-9a-f-]+$")))
| .params.response.body | fromjson
