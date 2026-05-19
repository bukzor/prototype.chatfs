#!/usr/bin/env -S jq -rcf
# Pluck the /chat_conversations/{id}?tree=True&... response body (one per
# line). The URL carries query params (tree, rendering_mode, etc.) so we
# anchor on end-of-path-segment, not end-of-url.
select(.method == "Network.responseReceived"
       and (.params.response.url | test("/chat_conversations/[0-9a-f-]+($|\\?)")))
| .params.response.body
| strings  # 204, interrupted responses
| fromjson
