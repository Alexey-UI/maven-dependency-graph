#!/bin/sh
set -eu
ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
cd "$ROOT"
if ! command -v npm >/dev/null 2>&1; then
    echo 'Установите Node.js 22+ с https://nodejs.org/ и повторите запуск.' >&2
    exit 1
fi
CHROME='/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'
if [ -x "$CHROME" ]; then
    PUPPETEER_SKIP_DOWNLOAD=true npm install --prefix .tools/mermaid \
        @mermaid-js/mermaid-cli@11.12.0
    cat > .tools/puppeteer.json <<'JSON'
{"executablePath":"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"}
JSON
else
    npm install --prefix .tools/mermaid @mermaid-js/mermaid-cli@11.12.0
fi
