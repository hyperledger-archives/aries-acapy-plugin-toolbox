#! /usr/bin/env bash
set -eou pipefail

function die {
    >&2 echo "Fatal: ${@}"
    exit 1
}

# If not in docs directory, fail
[[ "$(basename $PWD)" == "docs" ]] || die "Must be run from docs"

for README in **/**/README.md; do
    ./find_messages_in_doc.awk "$README"
done
