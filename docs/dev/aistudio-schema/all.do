# Default target: build the whole schema-extraction DAG.
#   accessors.jsonl — schema recovered from the JS bundle (offline RE)
#   rosetta/check   — convert.py output stays faithful to the real alt=json
redo-ifchange accessors.jsonl rosetta/check
