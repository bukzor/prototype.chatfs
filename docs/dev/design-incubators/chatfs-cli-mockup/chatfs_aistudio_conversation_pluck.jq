#!/usr/bin/env -S jq -rcf
# Pluck each prompt message out of the ResolveDriveResource response
# body, one per line. AI Studio prompts are Drive-backed; the whole
# conversation arrives in this RPC as application/json+protobuf (JSPB —
# positional arrays, not keyed objects).
#
# ResolveDriveResource resolves any Drive resource, not just prompts,
# so URL alone doesn't guarantee a prompt body — guard on shape too:
# the first message's [0] is "prompts/<id>". `.[]` flattens the
# envelope to one message per line.
select(.method == "Network.responseReceived"
       and (.params.response.url | test("[./]MakerSuiteService/ResolveDriveResource$")))
| .params.response.body
| strings  # 204, interrupted responses
| fromjson
| select((.[0][0]? // "") | strings | test("^prompts/"))
| .[]
