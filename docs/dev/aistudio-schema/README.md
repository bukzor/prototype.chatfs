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
    ./aistudio-reauth                 # drive a browser, capture, extract auth
    # or, from an existing capture:
    ./refresh-secrets.sh aistudio.<stamp>.cdp.jsonl

    ./curl-aistudio -d '["<id>"]' 'ResolveDriveResource?alt=json' | jq .  # named JSON
    ./curl-aistudio -d '["<id>"]'  ResolveDriveResource          | jq .  # positional JSPB

- `aistudio-reauth` — browser → capture → auth (run when curl-aistudio 401s)
- `refresh-secrets.sh` — CDP capture → `secrets/aistudio.headers.curl` (auth)
- `curl-aistudio` — authenticated `$rpc` call; it *is* curl. A bare `Method`
  (or `Method?alt=json`) token expands to the full `$rpc` URL; `?alt=json` ⇒
  named proto3 JSON, omitted ⇒ positional JSPB
- `live-replay.sh` — one-shot introspection battery (alt=json / discovery /
  reflection) recording what the server does and does not expose

Caveat: `?alt=json` names are server-side only; they do **not** appear in the
bundles or in a capture's JSPB bodies. Offline decoding of a capture still needs
the position→name map (see `discourse.kb/` and `rosetta/` below).

## Converting JSPB → JSON, reproducibly (`rosetta/`)

`rosetta/convert.py` turns a positional JSPB body into the named JSON form,
driven by a hand-curated `slot → field` SCHEMA. The rest of `rosetta/` exists to
keep that SCHEMA honest: capture the *same* prompt in both encodings, correlate
them to author/repair the SCHEMA, and assert the conversion stays faithful.

The Rosetta stone is the **golden pair** — one prompt fetched both ways:

    resolvedrive.jspb.json       # positional (the converter's input)
    resolvedrive.alt-json.json   # named (the ground truth to match)

Five steps, each a tool (run from `rosetta/`):

    # 1+2. capture the golden pair (live; needs auth — see Live access above)
    ./capture.sh [PROMPT_ID]

    # 3. correlate the pair → proposed `slot → field` maps per message type
    ./correlate.py             # ordering heuristic (an AID, not an oracle)
    ./correlate.py --values    # the other lens: value → jspb index-paths

    # 4. edit SCHEMA in convert.py by hand, guided by step 3 + walk-graph.py
    ./convert.py < resolvedrive.jspb.json | jq .

    # 5. assert the conversion is "similar enough" to the real alt=json
    ./verify.py                # name/shape diff; exit 1 on divergence

Step 5 is also the redo gate `rosetta/check` (in `all.do`): it converts the
committed JSPB fixture and name/shape-diffs it against the committed alt=json,
offline, failing the build on any divergence.

"Similar enough" = same field **names** and **structure**. Leaf *values*
legitimately differ between encodings and are not compared: bools (`0/1` vs
`true/false`), enums (ints vs names), and timestamps (`[seconds, nanos]` vs
RFC3339 string) — the last differs in shape too, the one tolerated gap.

Why step 4 is hand-curated, not generated: the step-3 ordering heuristic
mis-assigns slots whenever a field is absent in the sample (the monotonic claim
skips the null slot). It narrows the search; the bundle field numbers
(`walk-graph.py`) and populated-slot tree (`body-shape.py`) confirm it. See
`discourse.kb/questions.kb/can-we-decode-deterministically.md`.

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
