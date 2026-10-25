#!/bin/sh
set -eu
ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
cd "$ROOT"
for NODE_BIN in "$ROOT"/.tools/node-*/bin; do
    if [ -d "$NODE_BIN" ]; then PATH="$NODE_BIN:$PATH"; fi
done
PATH="$ROOT/.tools/mermaid/node_modules/.bin:$PATH"
export PATH
export PYTHONPATH="$ROOT/src"
"$ROOT/.venv/bin/python" -m unittest discover -s tests -v
"$ROOT/.venv/bin/python" scripts/check_quality.py
