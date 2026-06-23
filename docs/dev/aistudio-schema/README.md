# AI Studio schema extraction

Brute-force the MakerSuite proto schema — field numbers, names, cardinality,
nested-message graph — out of the AI Studio web bundle.

Why this, not the server: the proto is
`google.internal.alkali.applications.makersuite.v1.MakerSuiteService`. The
`internal` package is unpublished, and the `$rpc` front end exposes no gRPC
reflection or discovery doc. But the schema ships to the browser.

Why it works: the bundle uses Google's *immutable JS protos*. Field
**numbers** are integer literals in the generated accessors, and accessor
**method names** (`getTitle`, `getPrompt`, `getRole`) survive minification.
The accessor primitive (`_.l`, `_.X`, `_.xi`, …) encodes the field type.

## Source

A CDP network capture whose `Network.responseReceived` events carry response
bodies (`.params.response.body`) for the `boq-makersuite` JS modules. The
existing `../design-incubators/chatfs-mockup-chatgpt/aistudio.cdp.jsonl`
qualifies.

## Pipeline

    # 1. capture -> bundles/<module-id>.js (raw), then format in place
    ./extract-bundles.py ../design-incubators/chatfs-mockup-chatgpt/aistudio.cdp.jsonl
    ./prettify-bundles.sh

    # 2. bundles -> flat accessor table
    cat bundles/*.js | ./grep-accessors.sh | ./parse-accessors.py > accessors.jsonl

    # 3. or walk one message graph — by RPC method, across ALL bundles
    ./walk-graph.py --rpc ResolveDriveResource bundles/*.js
    ./walk-graph.py i9a bundles/*.js        # or from a known ctor

- `extract-bundles.py` — capture → one raw `bundles/<id>.js` per module
- `prettify-bundles.sh` — format the bundles in parallel
- `grep-accessors.sh` — JS → one accessor definition per line
- `parse-accessors.py` — accessor line → `{name, number, prim, submsg}` JSONL
- `walk-graph.py` — BFS a message graph from a starting ctor

## Live access (server returns named fields — no bundle RE)

The `$rpc` endpoint returns fully-named proto3 JSON when called with `?alt=json`,
which obviates positional decoding when you can replay auth. Auth (cookie +
SAPISIDHASH) is extracted from a CDP capture into gitignored `secrets/`.

    # one-time: extract auth from a capture into secrets/aistudio.headers.curl
    ./refresh-secrets.sh aistudio.<stamp>.cdp.jsonl

    ./curl-aistudio -j ResolveDriveResource '["<prompt-id>"]' | jq .   # named JSON
    ./curl-aistudio    ResolveDriveResource '["<prompt-id>"]'          # positional JSPB

- `refresh-secrets.sh` — CDP capture → `secrets/aistudio.headers.curl` (auth)
- `curl-aistudio` — authenticated `$rpc` call; `-j` ⇒ `?alt=json` named output.
  Exits 7 on HTTP 401 (auth expired → re-capture and re-run `refresh-secrets.sh`)
- `live-replay.sh` — one-shot introspection battery (alt=json / discovery /
  reflection) recording what the server does and does not expose

Caveat: `?alt=json` names are server-side only; they do **not** appear in the
bundles or in a capture's JSPB bodies. Offline decoding of a capture still needs
the position→name map (see `discourse.kb/`).

## Accessor grammar

    get<Name>(){return _.<prim>(this, [<Ctor>,] <number> [, ...])}

- `<number>` is the proto field number (the lone integer argument).
- `<Ctor>` (when present) is the minified submessage constructor — the edge
  to the next message in the graph.

## Primitive legend (observed — extend as new ones appear)

| prim   | meaning                                   |
|--------|-------------------------------------------|
| `_.l`  | singular scalar (string / number)         |
| `_.Mj` | singular scalar (varint)                  |
| `_.X`  | singular submessage; 2nd arg = ctor       |
| `_.xi` | repeated submessage; 2nd arg = ctor       |

Unknown primitives surface as-is in the `prim` field — look them up in the
bundle and add a row rather than guessing.

## Walking the graph

The RPC stub pins the entry types. The stub lists the method path, then the
request ctor, then the response ctor:

    "/…/MakerSuiteService/ResolveDriveResource",
    _.h9a,   // request
    i9a,     // response

`walk-graph.py --rpc <Method>` resolves the response ctor and walks it for you.
Follow each `_.X`/`_.xi` edge down. Cross-check field numbers against the
positional indices in
`../design-incubators/chatfs-mockup-chatgpt/dev.kb/claims.kb/aistudio-jspb-prompt-shape.md`.

**Coverage caveat — getter recovery is partial per message.** `ResolveDriveResource`
*does* carry the whole conversation (its response Prompt's `Name` is
`prompts/<id>`; a sibling `chatfs_aistudio_conversation_pluck.jq` extracts the
turns from it). But the response ctor `_.Qw` exposes only 2 of its ~14+ JSPB
slots through getters (`getName` idx0, `getMetadata` idx4); the **turns array
has no generated getter in these bundles**, so the walk terminates before the
conversation content. Generated accessors exist only for fields the app reads
that way — so this method recovers a *skeleton*, not every field. Recovering
the turn/role/content numbers needs either the module that defines the turn
message's getters, or positional reverse-engineering straight from payloads
(which is what the `.jq` does).
