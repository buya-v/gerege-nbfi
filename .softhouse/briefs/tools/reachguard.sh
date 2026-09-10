#!/bin/bash
# reachguard runner — the tracked witness for .softhouse/guards/reachguard/main.go.
#
# reachguard is LEG 2, the go/types reachability discriminator for I3 balance writes. It is
# NOT invoked by conformance.sh, and deliberately so: the six recorded I-3 sites are mostly
# UNRESOLVED (and any PROVABLY-NO it does report is a finding for review, not a waiver), and
# wiring that into run_guards would turn a recorded red into a hard guard failure without
# deciding anything. It is run on demand, beside the ledgerguard red drive, by whoever wants
# the reachability question answered.
#
# The canonical guards directory grades every tracked .go/.sh/.py file beneath it, and
# .softhouse/guards/reachguard/main.go records THIS file as its REACHED-BY witness. The literal
# path to main.go below is what keeps that witness verified; do not remove it.
#
# Usage: reachguard.sh [args passed through to the checker]
#   REACHGUARD_ROOT overrides the module directory (default: <repo>/nexus).
set -u
here="$(cd "$(dirname "$0")" && pwd)"
repo="$(cd "$here/../../.." && pwd)"
run_root="${REACHGUARD_ROOT:-$repo/nexus}"
cd "$repo/.softhouse/guards/reachguard" || exit 2
exec go run . -root "$run_root" "$@"
