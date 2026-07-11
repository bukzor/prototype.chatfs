# check — the offline gate: convert.py must still produce output "similar
# enough" to the real alt=json, for EVERY committed golden pair. Converts
# each committed JSPB fixture and name/shape-diffs it against its committed
# alt=json (verify.py); any pair's divergence fails the build. Deterministic
# — no network, no live auth. The glob is real shell expansion at build time,
# so a new <subject>.{jspb,alt-json}.json pair needs no edit here.
redo-ifchange convert.py correlate.py verify.py *.jspb.json *.alt-json.json
./verify.py 1>&2
echo ok
