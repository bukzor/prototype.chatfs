#!/usr/bin/env -S jq -rcf
# Pluck each /chat_conversations_v2?... response body, one per line.
select(.method == "Network.responseReceived"
       and (.params.response.url | test("/chat_conversations_v2\\?")))
| .params.response.body | fromjson
