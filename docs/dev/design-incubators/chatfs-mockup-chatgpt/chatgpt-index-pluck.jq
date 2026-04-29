#!/usr/bin/env -S jq -rcf
# Pluck each /backend-api/conversations?... response body, one per line.
select(.method == "Network.responseReceived"
       and (.params.response.url | test("/backend-api/conversations\\?")))
| .params.response.body | fromjson
