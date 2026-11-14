#!/bin/sh
. "$(dirname "$0")/lib.sh"
cd "$ROOT" || exit 1
T=examples/test-repos
OUT=out
mkdir -p "$OUT"

show() {
    echo "--- $1"
    cat "$1"
    echo
}

echo "== Stage 5: Mermaid text and PNG for three packages"
run -p org.example:shop-app:1.0.0 -r "$REPO_URL" --draw -o $OUT/shop-app.png
show $OUT/shop-app.mmd
run -p org.example:report-tool:3.1.0 -r "$REPO_URL" -d 5 --draw -o $OUT/report-tool.png
show $OUT/report-tool.mmd
run -p org.example:cycle-a:1.0.0 -r "$REPO_URL" --draw -o $OUT/cycle-a.png
show $OUT/cycle-a.mmd

echo "== Stage 5: test repository, depth limit and filter in the picture"
run -p A -m test -r $T/graph.txt --draw -o $OUT/graph.png
run -p A -m test -r $T/chain.txt -d 2 --draw -o $OUT/chain-d2.png
run -p A -m test -r $T/filter.txt -f X --draw -o $OUT/filter-x.png

echo "== Stage 5: choice of the renderer"
run -p A -m test -r $T/diamond.txt --draw -o $OUT/diamond.png --renderer mmdc
run -p A -m test -r $T/diamond.txt --draw -o $OUT/diamond-online.png --renderer online

echo "== Stage 5: errors"
run -p A -m test -r $T/diamond.txt --draw -o $OUT/bad.txt
run -p A -m test -r $T/diamond.txt --draw -R D
run -p A -m test -r $T/diamond.txt --draw --renderer none
echo "Files are in the directory $OUT/"
