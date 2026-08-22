#!/usr/bin/env bash
# T253b — D2 RED-DRIVE. go-env.sh must never export a GOROOT that does not exist,
# and must never substitute a toolchain silently.
#
# NOTHING IN THE REAL TREE IS MOVED. Every scenario runs against a SCRATCH COPY of the
# repo layout (.softhouse/bin/go-env.sh plus a synthetic .git marker), so the pinned
# toolchain at the real path is never touched and the vector store is never near this.
#
# Scenarios, each run in a child bash so the parent's env is never polluted:
#   S1 pinned present      : real repo. Must export the real GOROOT and print NOTHING.
#   S2 pinned present, wt  : this worktree. Must resolve the MAIN checkout via
#                            --git-common-dir, not the worktree.
#   S3 pinned ABSENT + go  : scratch repo, no toolchain, a fake `go` on PATH.
#                            OLD: silent, broken GOROOT.  NEW: announced fallback.
#   S4 pinned ABSENT, no go: scratch repo, empty PATH. NEW: loud, exports no GOROOT,
#                            caller's own refusal stays fail-closed.
#   S5 inherited bogus GOROOT: must be DROPPED, not passed through.
#   S6 sourced under `set -e`: must not abort the caller (the D1 failure mode by
#                            another route).
#
# NO bare `grep`, NO `rg` (P-75) — matching is done with `case`, a shell builtin.
# Every rc is captured and asserted (P-80).
set -euo pipefail

# instruments -> t253-portability -> capture -> .softhouse -> REPO  (four levels).
# The first draft used three and silently addressed `$REPO/.softhouse/.softhouse/...`;
# the assertions caught it, which is the point of asserting rather than assuming.
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../.." && pwd)"
NEW_ENV="$REPO/.softhouse/bin/go-env.sh"
if [ ! -f "$NEW_ENV" ]; then
  printf 'REFUSING: go-env.sh not found at %s — the instrument is mis-anchored.\n' "$NEW_ENV" >&2
  exit 2
fi
OLD_ENV_BODY='GEREGE_TOOLCHAIN=/Users/buv/gerege-nbfi/.softhouse/toolchain
export GOROOT="$GEREGE_TOOLCHAIN/go"
export GOPATH="$GEREGE_TOOLCHAIN/gopath"
export GOCACHE="$GEREGE_TOOLCHAIN/gocache"
export GOMODCACHE="$GEREGE_TOOLCHAIN/gomodcache"
export PATH="$GOROOT/bin:$PATH"'

SCRATCH="$(mktemp -d "${TMPDIR:-/tmp}/t253-d2.XXXXXXXXXX")"
trap 'rm -rf "$SCRATCH"' EXIT HUP INT TERM QUIT
FAILURES=0

hr() { printf '%s\n' "============================================================"; }

ok()   { printf '  ASSERT OK   : %s\n' "$1"; }
bad()  { printf '  ASSERT FAIL : %s\n' "$1"; FAILURES=$((FAILURES + 1)); }

# contains HAYSTACK NEEDLE -> rc 0/1, via `case` (no grep, P-75)
contains() { case "$1" in *"$2"*) return 0 ;; *) return 1 ;; esac; }

# Build a scratch checkout that LOOKS like the repo but has no toolchain.
build_scratch() {                 # build_scratch DIR ENVBODY_MODE(new|old)
  local dir="$1" mode="$2"
  mkdir -p "$dir/.softhouse/bin"
  ( cd "$dir" && git init -q . )
  if [ "$mode" = new ]; then
    cp "$NEW_ENV" "$dir/.softhouse/bin/go-env.sh"
  else
    { printf '#!/bin/sh\n'; printf '%s\n' "$OLD_ENV_BODY"; } > "$dir/.softhouse/bin/go-env.sh"
  fi
}

# run_source DIR EXTRA_ENV_ASSIGNMENTS... -> sets OUT_STDOUT/OUT_STDERR/OUT_RC/OUT_GOROOT
run_source() {
  local dir="$1"; shift
  local so se rc=0
  so="$SCRATCH/so.$$"; se="$SCRATCH/se.$$"
  set +e
  env "$@" bash -c '
      . "$1/.softhouse/bin/go-env.sh"
      printf "GOROOT=[%s]\n" "${GOROOT:-<unset>}"
      printf "GEREGE_GO_SOURCE=[%s]\n" "${GEREGE_GO_SOURCE:-<unset>}"
      printf "which_go=[%s]\n" "$(command -v go || printf "<none>")"
  ' _ "$dir" >"$so" 2>"$se"
  rc=$?
  set -e
  OUT_STDOUT="$(cat "$so")"; OUT_STDERR="$(cat "$se")"; OUT_RC="$rc"
}

hr
echo "S1 — PINNED PRESENT (the real repo). Must export the real GOROOT and stay SILENT."
run_source "$REPO" "PATH=$PATH"
printf '  stdout: %s\n' "$(printf '%s' "$OUT_STDOUT" | tr '\n' ' ')"
printf '  stderr: [%s]\n' "$(printf '%s' "$OUT_STDERR" | tr '\n' ' ')"
if [ "$OUT_RC" -eq 0 ]; then ok "sourcing returned 0"; else bad "sourcing returned $OUT_RC"; fi
if [ -z "$OUT_STDERR" ]; then ok "SILENT on the happy path (BAR output is unperturbed)"
else bad "printed on the happy path — the Mac BAR log would change"; fi
if contains "$OUT_STDOUT" "GEREGE_GO_SOURCE=[pinned]"; then ok "provenance recorded as pinned"
else bad "provenance not 'pinned'"; fi
if contains "$OUT_STDOUT" "/gerege-nbfi/.softhouse/toolchain/go"; then
  ok "GOROOT points into the MAIN checkout's toolchain"
else bad "GOROOT is not the main checkout toolchain"; fi

hr
echo "S2 — PINNED PRESENT, sourced FROM THIS WORKTREE. Must resolve the MAIN checkout."
printf '  worktree            : %s\n' "$REPO"
printf '  --git-common-dir    : %s\n' "$(git -C "$REPO" rev-parse --git-common-dir)"
if contains "$OUT_STDOUT" "GOROOT=[/Users/buv/gerege-nbfi/.softhouse/toolchain/go]"; then
  ok "a worktree resolved the MAIN checkout's shared toolchain, not its own empty one"
else bad "worktree did not resolve the main checkout: $OUT_STDOUT"; fi
if [ -d "$REPO/.softhouse/toolchain" ]; then
  bad "this worktree unexpectedly HAS its own toolchain — S2 proves nothing"
else
  ok "this worktree has NO toolchain of its own, so the git hop is load-bearing"
fi

hr
echo "S3 — PINNED ABSENT, a \`go\` on PATH. OLD form vs NEW form."
mkdir -p "$SCRATCH/fakebin"
{ printf '#!/bin/sh\n'; printf '%s\n' 'echo "go version go0.0.0-FAKE test/arm64"'; } \
  > "$SCRATCH/fakebin/go"
chmod +x "$SCRATCH/fakebin/go"

build_scratch "$SCRATCH/old" old
build_scratch "$SCRATCH/new" new

echo "  --- OLD go-env.sh (the shipped defect) ---"
run_source "$SCRATCH/old" "PATH=$SCRATCH/fakebin:/usr/bin:/bin"
printf '  stdout: %s\n' "$(printf '%s' "$OUT_STDOUT" | tr '\n' ' ')"
printf '  stderr: [%s]\n' "$(printf '%s' "$OUT_STDERR" | tr '\n' ' ')"
if contains "$OUT_STDOUT" "GOROOT=[/Users/buv/gerege-nbfi/.softhouse/toolchain/go]"; then
  ok "RED REPRODUCED: OLD exports a hardcoded GOROOT for a path this checkout does not have"
else bad "RED NOT reproduced: $OUT_STDOUT"; fi
if [ -z "$OUT_STDERR" ]; then
  ok "RED REPRODUCED: OLD said NOTHING about it — this is the silence that becomes"
  echo "                'a HARD money guard did not compile' downstream"
else bad "OLD unexpectedly printed a diagnostic"; fi

echo "  --- NEW go-env.sh ---"
run_source "$SCRATCH/new" "PATH=$SCRATCH/fakebin:/usr/bin:/bin"
printf '  stdout: %s\n' "$(printf '%s' "$OUT_STDOUT" | tr '\n' ' ')"
printf '  stderr:\n'; printf '%s\n' "$OUT_STDERR" | sed 's/^/    | /'
if contains "$OUT_STDOUT" "GOROOT=[<unset>]"; then
  ok "GREEN: NEW exported NO GOROOT — nothing points at a directory that is not there"
else bad "NEW still exported a GOROOT: $OUT_STDOUT"; fi
if contains "$OUT_STDERR" "FALLBACK IN EFFECT"; then
  ok "GREEN: the substitution is ANNOUNCED"
else bad "no fallback announcement"; fi
if contains "$OUT_STDERR" "go0.0.0-FAKE"; then
  ok "GREEN: the announcement names the VERSION actually being used"
else bad "announcement omits the version"; fi
if contains "$OUT_STDERR" "$SCRATCH/fakebin/go"; then
  ok "GREEN: the announcement names the BINARY actually being used"
else bad "announcement omits the binary path"; fi
if contains "$OUT_STDERR" "THIS IS NOT THE PINNED TOOLCHAIN"; then
  ok "GREEN: the announcement says so in as many words"
else bad "announcement does not disclaim the pinned toolchain"; fi
if contains "$OUT_STDOUT" "GEREGE_GO_SOURCE=[fallback-path]"; then
  ok "GREEN: provenance is machine-readable"
else bad "provenance not recorded"; fi

hr
echo "S4 — PINNED ABSENT and NO \`go\` anywhere. Must be loud and export nothing."
# CALIBRATION FIRST (the scenario is worthless if it is vacuous). The first draft used
# PATH=$SCRATCH/emptybin, which had no `bash` either — `env` died rc=127 before go-env.sh
# ever ran and four assertions failed against a scenario that never happened. A stock
# PATH of /usr/bin:/bin is the honest "no repo toolchain" shell: real enough to run, and
# it must be CHECKED to contain no `go` rather than assumed to.
BARE_PATH=/usr/bin:/bin
if PATH="$BARE_PATH" command -v go >/dev/null 2>&1; then
  bad "CALIBRATION: $BARE_PATH already has a \`go\` ($(PATH="$BARE_PATH" command -v go)) — S4 would be vacuous"
else
  ok "CALIBRATION: $BARE_PATH contains no \`go\`, so S4 really is the no-toolchain case"
fi
run_source "$SCRATCH/new" "PATH=$BARE_PATH"
printf '  stdout: %s\n' "$(printf '%s' "$OUT_STDOUT" | tr '\n' ' ')"
printf '  stderr:\n'; printf '%s\n' "$OUT_STDERR" | sed 's/^/    | /'
if contains "$OUT_STDOUT" "GOROOT=[<unset>]"; then ok "no GOROOT exported"
else bad "a GOROOT was exported with no toolchain at all"; fi
if contains "$OUT_STDERR" "NO \`go\` on PATH either"; then ok "loud about total absence"
else bad "not loud about total absence"; fi
if contains "$OUT_STDOUT" "GEREGE_GO_SOURCE=[absent]"; then ok "provenance = absent"
else bad "provenance not 'absent'"; fi
if contains "$OUT_STDOUT" "which_go=[<none>]"; then
  ok "the caller's own \`command -v go\` check will now fire — refusal stays FAIL-CLOSED"
else bad "a go leaked onto PATH"; fi

hr
echo "S5 — an INHERITED bogus GOROOT must be DROPPED, not passed along."
run_source "$SCRATCH/new" "PATH=$SCRATCH/fakebin:/usr/bin:/bin" "GOROOT=/nonexistent/goroot"
printf '  stderr:\n'; printf '%s\n' "$OUT_STDERR" | sed 's/^/    | /'
if contains "$OUT_STDOUT" "GOROOT=[<unset>]"; then ok "the bogus inherited GOROOT was dropped"
else bad "bogus GOROOT survived: $OUT_STDOUT"; fi
if contains "$OUT_STDERR" "dropping inherited GOROOT"; then ok "and the drop was announced"
else bad "the drop was silent"; fi

hr
echo "S6 — sourced under \`set -e\`. Must NOT abort the caller (D1's failure mode, other route)."
set +e
env "PATH=$BARE_PATH" bash -c '
    set -euo pipefail
    . "$1/.softhouse/bin/go-env.sh"
    echo "CALLER-STILL-ALIVE"
' _ "$SCRATCH/new" >"$SCRATCH/s6.out" 2>"$SCRATCH/s6.err"
S6RC=$?
set -e
printf '  rc=%d stdout=[%s]\n' "$S6RC" "$(cat "$SCRATCH/s6.out")"
if [ "$S6RC" -eq 0 ] && contains "$(cat "$SCRATCH/s6.out")" "CALLER-STILL-ALIVE"; then
  ok "the caller survived sourcing with no toolchain at all, under set -euo pipefail"
else bad "sourcing killed a set -e caller (rc=$S6RC) — that is D1 by another route"; fi

hr
if [ "$FAILURES" -eq 0 ]; then
  echo "D2 RED-DRIVE: all assertions held."
  exit 0
fi
echo "D2 RED-DRIVE: $FAILURES assertion(s) FAILED."
exit 1
