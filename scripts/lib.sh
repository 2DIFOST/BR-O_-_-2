#!/bin/sh
ROOT=$(cd "$(dirname "$0")/.." && pwd)

run() {
    printf '$ depgraph'
    for arg in "$@"; do printf ' %s' "$arg"; done
    printf '\n'
    "$ROOT/run.sh" "$@"
    printf '[exit code: %s]\n\n' "$?"
}
