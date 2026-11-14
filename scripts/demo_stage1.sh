#!/bin/sh
. "$(dirname "$0")/lib.sh"
cd "$ROOT" || exit 1
TESTREPO=$(mktemp)
printf 'A:\n' > "$TESTREPO"

echo "== Stage 1: description of the parameters"
run --help

echo "== Stage 1: error handling of every parameter"
run
run -p app
run -p org.example:app:1.0.0 -r ftp://example.org/repo
run -p org.example:app:1.0.0 -m remote
run -p A -m test
run -p A -m test -r no-such-file.txt
run -p A1 -m test -r "$TESTREPO"
run -p org.example:app:1.0.0 -o graph.jpg
run -p org.example:app:1.0.0 -o no/such/dir/graph.png
run -p org.example:app:1.0.0 -d zero
run -p org.example:app:1.0.0 -d 0
rm -f "$TESTREPO"
