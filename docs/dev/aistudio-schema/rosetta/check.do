# check — the offline gate: convert.py must still produce output "similar
# enough" to the real alt=json. Converts the committed JSPB fixture and
# name/shape-diffs it against the committed alt=json (verify.py); a divergence
# fails the build. Deterministic — no network, no live auth.
redo-ifchange convert.py verify.py resolvedrive.jspb.json resolvedrive.alt-json.json
./verify.py 1>&2
echo ok
