#!/usr/bin/env bash
# T254 reviewer instrument: REPRODUCE the Mac author's claim that the CLOUD
# go-env.sh does not clear a stale inherited GOROOT, and therefore announces a
# fallback to a `go` that then cannot run.
#
# METHOD. Both versions only reach their fallback arm when NO pinned toolchain
# is found. On this Mac the pinned toolchain IS found (main checkout), so the
# fallback is forced by staging each script in a throwaway tree that is:
#   - outside any git repo   -> `git rev-parse --git-common-dir` fails
#   - has no .softhouse/toolchain -> every candidate is ABSENT
# A real `go` is then placed on PATH (the pinned binary, which honours $GOROOT),
# and a BOGUS GOROOT is exported before sourcing. That is the exact shape the
# claim describes: an inherited GOROOT pointing nowhere.
#
# P-75/P-80: no grep/rg selectors decide anything here; every verdict is read
# from an exit status or a captured stream. set -euo pipefail. Any unexpected
# rc ABORTS rather than printing an absence.
set -euo pipefail

OUT="${1:?outdir}"
GOBIN_DIR=/Users/buv/gerege-nbfi/.softhouse/toolchain/go/bin
BOGUS=/nonexistent/t254/goroot

[ -x "$GOBIN_DIR/go" ] || { echo "FATAL: no pinned go at $GOBIN_DIR/go" >&2; exit 90; }

STAGE=$(mktemp -d "${TMPDIR:-/tmp}/t254-goroot.XXXXXXXXXX")
trap 'rm -rf "$STAGE"' EXIT

echo "======================================================================"
echo "T254 F-x: STALE INHERITED GOROOT — cloud vs mac go-env.sh"
echo "stage:  $STAGE   (outside any git repo, no toolchain)"
echo "bogus:  GOROOT=$BOGUS"
echo "go on PATH: $GOBIN_DIR/go ($("$GOBIN_DIR/go" version))"
echo "======================================================================"

# Confirm the stage really is outside git, so the fallback arm is genuinely
# reached and we are not measuring something else.
set +e
( cd "$STAGE" && git rev-parse --git-common-dir >/dev/null 2>&1 )
grc=$?
set -e
echo "control: git rev-parse --git-common-dir in stage -> rc=$grc (non-zero = outside a repo, as required)"
[ "$grc" -ne 0 ] || { echo "FATAL: stage is inside a git repo; the fallback arm would not be reached" >&2; exit 91; }
echo

for impl in cloud mac; do
  d="$STAGE/$impl/.softhouse/bin"
  mkdir -p "$d"
  cp "$OUT/.goenv-$impl.sh" "$d/go-env.sh"

  echo "----------------------------------------------------------------------"
  echo "### $impl  —  sourcing with a BOGUS GOROOT already exported"
  echo "----------------------------------------------------------------------"

  # A fresh bash, so nothing leaks between the two arms.
  set +e
  env -i \
    HOME="$HOME" \
    PATH="$GOBIN_DIR:/usr/bin:/bin:/usr/sbin:/sbin" \
    GOROOT="$BOGUS" \
    TMPDIR="${TMPDIR:-/tmp}" \
    /bin/bash --noprofile --norc -c '
      . "$1/go-env.sh"
      echo "--- POST-SOURCE STATE ---"
      echo "GOROOT after source     = ${GOROOT-<unset>}"
      echo "GEREGE_GO_SOURCE        = ${GEREGE_GO_SOURCE-<unset>}"
      echo "command -v go           = $(command -v go 2>/dev/null || echo none)"
      echo "--- DOES THE ANNOUNCED go ACTUALLY RUN? ---"
      out=$(go version 2>&1); rc=$?
      echo "go version rc=$rc"
      echo "go version out: $out"
      exit $rc
    ' _ "$d"
  rc=$?
  set -e
  echo "### $impl: final rc from the sourced-then-run probe = $rc"
  echo
done

echo "======================================================================"
echo "READING: rc=0 with a real version string means the announced fallback"
echo "WORKS. rc!=0 with 'cannot find GOROOT directory' means the script"
echo "announced a substitution to a compiler that CANNOT RUN — the very error"
echo "its own header describes."
echo "======================================================================"
