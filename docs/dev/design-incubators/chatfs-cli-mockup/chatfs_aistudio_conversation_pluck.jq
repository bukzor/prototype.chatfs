#!/usr/bin/env -S jq -rcf
# Pluck the ResolveDriveResource response body that carries the prompt
# (one per line). AI Studio prompts are Drive-backed; the whole
# conversation arrives in this single RPC as application/json+protobuf
# (JSPB — positional arrays, not keyed objects).
#
# That RPC endpoint is generic (index/recents calls reuse it), so we
# anchor the URL on end-of-path and also guard on body shape: the prompt
# payload is a JSPB array whose [0][0] is "prompts/<id>".
select(.method == "Network.responseReceived"
       and (.params.response.url | test("[./]MakerSuiteService/ResolveDriveResource$")))
| .params.response.body
| strings  # 204, interrupted responses
| fromjson
| select((.[0][0]? // "") | strings | test("^prompts/"))
