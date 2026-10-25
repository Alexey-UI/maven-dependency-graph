#!/bin/sh
set -eu
ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
for name in maven commons-text slf4j; do
    "$ROOT/run.sh" "$ROOT/examples/$name.yaml"
done
