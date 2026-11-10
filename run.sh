#!/bin/sh
ROOT=$(cd "$(dirname "$0")" && { pwd -W 2>/dev/null || pwd; })
if [ -z "$PYTHON" ]; then
    for candidate in python3 python py; do
        if "$candidate" -c "" >/dev/null 2>&1; then
            PYTHON=$candidate
            break
        fi
    done
fi
PYTHONPATH="$ROOT/src" exec "$PYTHON" -m depgraph "$@"
