#!/bin/sh
set -eu
ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
for name in chain diamond single shorter depth-zero depth-one filtered; do
    echo "=== $name ==="
    "$ROOT/run.sh" "$ROOT/examples/$name.yaml"
done
echo '=== cycle: порядок загрузки невозможен ==='
if "$ROOT/run.sh" "$ROOT/examples/cycle.yaml"; then
    echo 'Ожидалась ошибка цикла' >&2
    exit 1
fi
