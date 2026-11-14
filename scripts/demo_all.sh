#!/bin/sh
dir=$(dirname "$0")
for stage in 1 2 3 4; do
    sh "$dir/demo_stage$stage.sh" || exit 1
done
