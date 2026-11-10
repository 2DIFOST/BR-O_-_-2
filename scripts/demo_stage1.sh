#!/bin/sh
. "$(dirname "$0")/lib.sh"
cd "$ROOT" || exit 1
TESTREPO=$(mktemp)
printf 'A:\n' > "$TESTREPO"

echo "== Stage 1: all parameters and defaults"
run -p org.example:app:1.0.0
run -p org.example:app:1.0.0 -r https://repo.example.org/maven2 -m url \
    -o result.png -d 5 -f test
run -p A -m test -r "$TESTREPO" -d 2

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
