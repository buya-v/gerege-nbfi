#!/bin/bash
# Edge: the harness SOURCED into a shell where _conformance_psub_line is readonly.
h="${1:-.softhouse/conformance.sh}"
readonly _conformance_psub_line=conformance-psub-live
( . "$h" --help ) >/dev/null 2>&1
echo "sourced-with-readonly exit=$?"
( . "$h" --help ) 2>&1 | head -3
