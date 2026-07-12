# check — this endpoint's offline gate: convert jspb.json, name/shape-diff
# against alt-json.json. Deterministic — no network, no live auth. Built
# independently of every other endpoint/*/check — this one's fixtures
# changing doesn't force a sibling endpoint to reconvert (see ../../check.do).
redo-ifchange ../../convert.py ../../verify.py meta.json jspb.json alt-json.json
../../verify.py . 1>&2
echo ok
