# bundles/ — boq-makersuite JS modules extracted from the CDP capture and
# prettier-formatted. Directory target: build into a tmp dir, swap on success
# so the live bundles/ is never half-written.
exec >&2  # directory target: keep stray stdout out of redo's $3

capture=../design-incubators/chatfs-mockup-chatgpt/aistudio.cdp.jsonl
redo-ifchange extract-bundles.py prettify-bundles.sh "$capture"

tmp=$3.tmp
rm -rf "$tmp"
mkdir "$tmp"
./extract-bundles.py "$tmp" <"$capture"
./prettify-bundles.sh "$tmp"
rm -rf "$1"
mv "$tmp" "$3"
