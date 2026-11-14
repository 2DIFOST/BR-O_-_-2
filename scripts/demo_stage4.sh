#!/bin/sh
. "$(dirname "$0")/lib.sh"
cd "$ROOT" || exit 1
T=examples/test-repos

echo "== Stage 4: reverse dependencies in a test repository"
run -p A -m test -r $T/diamond.txt -R D
run -p A -m test -r $T/diamond.txt -R B
run -p A -m test -r $T/diamond.txt -R A

echo "== Stage 4: a larger graph, the packages of the graph only"
run -p A -m test -r $T/graph.txt -R D
run -p A -m test -r $T/graph.txt -R F

echo "== Stage 4: depth limit and filter are applied to the graph"
run -p A -m test -r $T/chain.txt -d 2 -R B
run -p A -m test -r $T/chain.txt -d 2 -R D
run -p A -m test -r $T/filter.txt -f X -R B

echo "== Stage 4: cyclic dependencies"
run -p A -m test -r $T/cycle.txt -R C
run -p A -m test -r $T/self-loop.txt -R A

echo "== Stage 4: Maven repository"
run -p org.example:shop-app:1.0.0 -r "$REPO_URL" -R org.example:common-utils:1.2.0
run -p org.example:shop-app:1.0.0 -r "$REPO_URL" -R org.example:logging-api:1.0.0

echo "== Stage 4: errors"
run -p A -m test -r $T/diamond.txt -R X
run -p A -m test -r $T/diamond.txt -R d
run -p org.example:shop-app:1.0.0 -r "$REPO_URL" -R bad
