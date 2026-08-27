#!/usr/bin/env bash
# T272 — the two remaining questions the main drive does not answer.
#
#  (1) DOES THE GRAFT SURVIVE THE OTHER SHELLS? go-env.sh is `#!/bin/sh` and is SOURCED,
#      so `return` and the `return 2 2>/dev/null || exit 2` idiom have to behave in every
#      shell that might source it. Driven, not assumed, in each shell present on this host.
#  (2) DOES THE MODULE STILL BUILD through the grafted seam? CLAUDE.md § Verification:
#      `go build ./...`, `go vet ./...`, `go test ./...`.
set -u -o pipefail
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../.." && pwd)"
GE="$REPO/.softhouse/bin/go-env.sh"
hr() { printf '%s\n' '------------------------------------------------------------------------'; }
RC=0

hr; echo "(0) SYNTAX, in every shell on this host"
for sh in sh bash zsh dash ksh; do
  if command -v "$sh" >/dev/null 2>&1; then
    if "$sh" -n "$GE" 2>/dev/null; then echo "  $sh -n : OK"; else echo "  $sh -n : FAILED"; RC=1; fi
  else
    echo "  $sh    : NOT ON THIS HOST (tested with command -v) — not exercised, not claimed"
  fi
done

hr; echo "(1) SOURCED in each shell, toolchain PRESENT, GEREGE_GO_STRICT=1"
echo "    Strict must be a NO-OP here in every shell: rc 0, src=pinned."
for sh in sh bash zsh dash ksh; do
  command -v "$sh" >/dev/null 2>&1 || { echo "  $sh : absent"; continue; }
  out="$( cd "$REPO" && GEREGE_GO_STRICT=1 "$sh" -c '. "$1"; printf "rc=%s src=%s" "$?" "${GEREGE_GO_SOURCE:-UNSET}"' _ "$GE" 2>/dev/null )"
  echo "  $sh : $out"
  case "$out" in *"rc=0 src=pinned"*) ;; *) echo "      UNEXPECTED"; RC=1 ;; esac
done

hr; echo "(2) SOURCED in each shell, toolchain ABSENT, GEREGE_GO_STRICT=1 -> rc 2, src=refused"
SCRATCH="$(mktemp -d)"; trap 'rm -rf "$SCRATCH"' EXIT HUP INT TERM QUIT
mkdir -p "$SCRATCH/off/.softhouse/bin"; git init -q "$SCRATCH/off"
cp "$GE" "$SCRATCH/off/.softhouse/bin/go-env.sh"
for sh in sh bash zsh dash ksh; do
  command -v "$sh" >/dev/null 2>&1 || { echo "  $sh : absent"; continue; }
  out="$( cd "$SCRATCH/off" && PATH=/usr/bin:/bin:/usr/sbin:/sbin GEREGE_GO_STRICT=1 \
          "$sh" -c '. "$1"; printf "rc=%s src=%s" "$?" "${GEREGE_GO_SOURCE:-UNSET}"' _ \
          "$SCRATCH/off/.softhouse/bin/go-env.sh" 2>/dev/null )"
  echo "  $sh : $out"
  case "$out" in *"rc=2 src=refused"*) ;; *) echo "      UNEXPECTED"; RC=1 ;; esac
done

hr; echo "(3) EXECUTED rather than sourced — the UNSUPPORTED path the \`|| exit 2\` idiom covers"
echo "    A top-level \`return\` is an error in bash and dash when the file is RUN. The idiom"
echo "    suppresses that message and falls through to exit 2, so the status is still 2 and"
echo "    never an accidental 0. This is the cloud arm's idiom and the reason it was kept."
for sh in sh bash zsh dash; do
  command -v "$sh" >/dev/null 2>&1 || { echo "  $sh : absent"; continue; }
  ( cd "$SCRATCH/off" && PATH=/usr/bin:/bin:/usr/sbin:/sbin GEREGE_GO_STRICT=1 \
    "$sh" "$SCRATCH/off/.softhouse/bin/go-env.sh" >/dev/null 2>&1 )
  echo "  $sh : executed-directly rc=$?"
done

hr; echo "(4) THE MODULE, through the grafted seam (CLAUDE.md § Verification)"
( . "$GE"
  echo "  activation: src=${GEREGE_GO_SOURCE:-UNSET}  bin=${GEREGE_GO_BIN:-UNSET}"
  cd "$REPO/nexus" || exit 9
  go build ./...; echo "  go build ./... rc=$?"
  go vet   ./...; echo "  go vet   ./... rc=$?"
  go test  ./... 2>&1 | tail -12
  echo "  go test  ./... rc=${PIPESTATUS[0]}" )
brc=$?
[ "$brc" -eq 0 ] || { echo "  the build subshell exited $brc"; RC=1; }

hr
[ "$RC" -eq 0 ] && echo "50-shells-and-build: GREEN" || echo "50-shells-and-build: RED"
exit "$RC"
