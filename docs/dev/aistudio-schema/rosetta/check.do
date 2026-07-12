# check — the offline gate: redo each endpoint's check independently
# (endpoint/<name>/check.do), then aggregate. Deterministic — no network, no
# live auth. Independent targets, not one combined run: an endpoint whose
# fixture is untouched stays cached, and a divergence in one doesn't suppress
# the other's own OK/DIVERGENT report.
#
# `endpoint/*/check` itself can't be redo-ifchange'd directly — it doesn't
# exist as a file until built, so an unmatched shell glob passes through
# literally instead of expanding. Glob `meta.json` (committed, always
# present) instead, to discover which endpoint dirs exist; a new
# endpoint/<name>/ needs no edit here.
redo-ifchange endpoint/*/meta.json
for meta in endpoint/*/meta.json; do
  redo-ifchange "${meta%/meta.json}/check"
done
echo ok
