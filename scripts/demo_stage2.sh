#!/bin/sh
. "$(dirname "$0")/lib.sh"
cd "$ROOT" || exit 1
ORG=org.example

echo "== Stage 2: direct dependencies from a Maven repository (file:// URL)"
run -p $ORG:shop-app:1.0.0 -r "$REPO_URL"
run -p $ORG:shop-web:1.0.0 -r "$REPO_URL"
run -p $ORG:report-core:3.1.0 -r "$REPO_URL"
run -p $ORG:logging-api:1.0.0 -r "$REPO_URL"

echo "== Stage 2: errors of the repository"
run -p $ORG:nope:1.0.0 -r "$REPO_URL"
run -p $ORG:shop-app:1.0.0 -r "$REPO_URL/missing-dir"
run -p $ORG:shop-app:1.0.0 -r http://127.0.0.1:9
run -p $ORG:shop-app:1.0.0 -r ftp://example.org/repo
run -p $ORG:shop-app:1.0.0 -m test -r "$REPO_URL"
