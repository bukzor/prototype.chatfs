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
existing `../design-incubators/chatfs-cli-mockup/aistudio.cdp.jsonl`
qualifies.

## Pipeline

    # 1. capture -> bundles/<module-id>.js (raw), then format in place
    ./extract-bundles.py ../design-incubators/chatfs-cli-mockup/aistudio.cdp.jsonl
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
keep that SCHEMA honest: capture the *same* subject in both encodings, correlate
them to author/repair the SCHEMA, and assert the conversion stays faithful.

The Rosetta stones are **golden pairs**, one per endpoint, held concurrently —
each in its own `endpoint/<name>/` directory, which localizes everything that
varies for that endpoint:

    endpoint/resolvedrive/jspb.json       # positional — ResolveDriveResource, one prompt
    endpoint/resolvedrive/alt-json.json   # named ground truth
    endpoint/resolvedrive/meta.json       # method, param, top-level wrapper shape
    endpoint/listprompts/jspb.json        # positional — ListPrompts, a page of prompts
    endpoint/listprompts/alt-json.json    # named ground truth
    endpoint/listprompts/meta.json        # method, param, top-level wrapper shape

Both endpoints are HYPOTHESIZED to reuse the same PROMPT/METADATA message
types — one shared SCHEMA in `convert.py`, which `verify.py` keeps testing per
endpoint against that endpoint's real alt=json (not a settled fact — see
`discourse.kb/questions.kb/can-we-decode-deterministically.md`). Only the
top-level wrapper shape is declared to differ, in each endpoint's `meta.json`
(`top_level_key`/`repeated`) — `listprompts` entries are additionally sparser
(no `runSettings`/`systemInstruction`; `chunkedPrompt` present but empty,
since the index carries no turn content), but that's a data difference, not a
schema one. Holding both pairs at once is the point: it's evidence for SCHEMA
stability across structurally different endpoints simultaneously, not just
per-pivot.

Five steps, each a tool (run from `rosetta/`), all parameterized by
`ENDPOINT_DIR`:

    # 1+2. capture a golden pair (live; needs auth — see Live access above)
    ./capture.sh endpoint/resolvedrive [PROMPT_ID]
    ./capture.sh endpoint/listprompts [PAGE_SIZE]

    # 3. correlate a pair → proposed `slot → field` maps per message type
    ./correlate.py endpoint/<name>
    ./correlate.py --values endpoint/<name>

    # 4. edit SCHEMA in convert.py by hand, guided by step 3 + walk-graph.py
    ./convert.py endpoint/<name> < endpoint/<name>/jspb.json | jq .

    # 5. assert one endpoint's pair converts "similar enough" to its real alt=json
    ./verify.py                    # every endpoint/*/ with a golden pair (default)
    ./verify.py endpoint/<name>    # one endpoint

Step 5 is also the redo gate `rosetta/check` (in `all.do`) — but not as one
combined check: each `endpoint/<name>/check.do` verifies just its own pair,
independently redo-cacheable, so one endpoint's untouched fixture doesn't
force a sibling to reconvert. `rosetta/check.do` aggregates them. A new
endpoint needs no edit to any `.do` file — both the aggregator and `verify.py`'s
default mode discover endpoints by directory listing.

A new endpoint needs an `endpoint/<name>/` directory: its golden pair, a
`meta.json` (`method`, `default_param`, `body`, `top_level_key`, `repeated`),
and a `check.do` (copy an existing one verbatim — it's endpoint-agnostic).
PROMPT/METADATA stay the one shared SCHEMA in `convert.py`; nothing
endpoint-specific belongs there.

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
`../design-incubators/chatfs-cli-mockup/dev.kb/claims.kb/aistudio-jspb-prompt-shape.md`.

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
