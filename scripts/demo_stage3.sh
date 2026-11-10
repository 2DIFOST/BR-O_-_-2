#!/bin/sh
. "$(dirname "$0")/lib.sh"
cd "$ROOT" || exit 1
T=examples/test-repos

echo "== Stage 3: test repository, transitive dependencies (BFS)"
run -p A -m test -r $T/diamond.txt
run -p A -m test -r $T/graph.txt

echo "== Stage 3: maximum depth"
run -p A -m test -r $T/chain.txt -d 1
run -p A -m test -r $T/chain.txt -d 3
run -p A -m test -r $T/chain.txt -d 10

echo "== Stage 3: filter by a substring of the package name"
run -p A -m test -r $T/filter.txt
run -p A -m test -r $T/filter.txt -f X
run -p A -m test -r $T/filter.txt -f Y
run -p A -m test -r $T/filter.txt -f A

echo "== Stage 3: cyclic dependencies"
run -p A -m test -r $T/cycle.txt
run -p A -m test -r $T/self-loop.txt
run -p A -m test -r $T/cycle.txt -d 2

echo "== Stage 3: Maven repository, different versions and a missing POM"
run -p org.example:shop-app:1.0.0 -r "$REPO_URL" -d 2
run -p org.example:shop-app:1.0.0 -r "$REPO_URL" -f common-utils
run -p org.example:cycle-a:1.0.0 -r "$REPO_URL"
run -p org.example:report-tool:3.1.0 -r "$REPO_URL" -d 5

echo "== Stage 3: errors of the test repository"
run -p Z -m test -r $T/diamond.txt
TESTREPO=$(mktemp)
printf 'A: B\nB C\n' > "$TESTREPO"
run -p A -m test -r "$TESTREPO"
printf 'A: b\n' > "$TESTREPO"
run -p A -m test -r "$TESTREPO"
printf 'A: B\nA: C\n' > "$TESTREPO"
run -p A -m test -r "$TESTREPO"
rm -f "$TESTREPO"
