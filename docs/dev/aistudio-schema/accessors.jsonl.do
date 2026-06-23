# accessors.jsonl — flat {name, number, prim, submsg} schema table parsed from
# the prettified bundles. Plain file target: the pipeline writes to redo's $3.
redo-ifchange grep-accessors.sh parse-accessors.py bundles
cat bundles/*.js | ./grep-accessors.sh | ./parse-accessors.py >"$3"
