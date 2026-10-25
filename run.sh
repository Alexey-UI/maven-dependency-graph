#!/bin/sh
set -eu
ROOT=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
PYTHON=${PYTHON:-"$ROOT/.venv/bin/python"}
for NODE_BIN in "$ROOT"/.tools/node-*/bin; do
    if [ -d "$NODE_BIN" ]; then PATH="$NODE_BIN:$PATH"; fi
done
PATH="$ROOT/.tools/mermaid/node_modules/.bin:$PATH"
export PATH
export PYTHONPATH="$ROOT/src${PYTHONPATH:+:$PYTHONPATH}"
exec "$PYTHON" -m dependency_graph "$@"
