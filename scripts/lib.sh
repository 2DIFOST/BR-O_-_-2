#!/bin/sh
ROOT=$(cd "$(dirname "$0")/.." && { pwd -W 2>/dev/null || pwd; })
REPO_URL="file:///${ROOT#/}/examples/maven-repo"

run() {
    printf '$ depgraph'
    for arg in "$@"; do printf ' %s' "$arg"; done
    printf '\n'
    "$ROOT/run.sh" "$@"
    printf '[exit code: %s]\n\n' "$?"
}
