#!/usr/bin/env bash
# T253b — PEER COMPARISON, executed rather than read.
#
# Two independent implementations of T253 exist. This one (T253b, the Mac fire) and
# the cloud fire's at origin/softhouse/T253-harness-portability @ d7a7ea3. The driver
# asked for a difference report on the merits. Reading two files and asserting a
# difference is an opinion; running both against the same scenarios is a measurement.
#
# THEIR BRANCH IS NEVER MODIFIED AND NEVER CHECKED OUT. Their go-env.sh is extracted
# read-only with `git show` into a scratch tree.
#
# The scenario is the one that distinguishes them: A SHELL THAT ALREADY CARRIES A
# STALE GOROOT. That is not hypothetical — it is what every shell in this repo looks
# like after sourcing the OLD go-env.sh once, which is exactly the state a host is in
# mid-migration, and on a non-Mac host that inherited GOROOT points at nothing.
#
# No bare `grep`, no `rg` (P-75); matching via `case`. Every rc captured (P-80).
set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../.." && pwd)"
THEIR_REF="d7a7ea3"
MINE="$REPO/.softhouse/bin/go-env.sh"

SCRATCH="$(mktemp -d "${TMPDIR:-/tmp}/t253-cross.XXXXXXXXXX")"
trap 'rm -rf "$SCRATCH"' EXIT HUP INT TERM QUIT
FAILURES=0
ok()  { printf '  OK   : %s\n' "$1"; }
bad() { printf '  FAIL : %s\n' "$1"; FAILURES=$((FAILURES + 1)); }
contains() { case "$1" in *"$2"*) return 0 ;; *) return 1 ;; esac; }

# Extract theirs read-only. If the ref is not present, REFUSE — do not report an
# absence as a difference (P-80: a missing ref is an ERROR, not a measured negative).
if ! git -C "$REPO" cat-file -e "$THEIR_REF:.softhouse/bin/go-env.sh" 2>/dev/null; then
  printf 'REFUSING: %s:.softhouse/bin/go-env.sh is not present. Fetch it first.\n' "$THEIR_REF" >&2
  exit 2
fi

build_tree() {                    # build_tree DIR SRCFILE
  mkdir -p "$1/.softhouse/bin"
  ( cd "$1" && git init -q . )
  cp "$2" "$1/.softhouse/bin/go-env.sh"
}

git -C "$REPO" show "$THEIR_REF:.softhouse/bin/go-env.sh" > "$SCRATCH/theirs.sh"
build_tree "$SCRATCH/mine"   "$MINE"
build_tree "$SCRATCH/theirs" "$SCRATCH/theirs.sh"

# A fake `go` that reports its GOROOT exactly as the real one does when GOROOT is bad.
mkdir -p "$SCRATCH/fakebin"
cat > "$SCRATCH/fakebin/go" <<'FAKE'
#!/bin/sh
if [ -n "${GOROOT:-}" ] && [ ! -d "${GOROOT:-}" ]; then
    echo "go: cannot find GOROOT directory: $GOROOT" >&2
    exit 2
fi
echo "go version go0.0.0-FAKE test/arm64"
FAKE
chmod +x "$SCRATCH/fakebin/go"

probe() {                         # probe DIR LABEL
  local dir="$1" label="$2"
  set +e
  env "PATH=$SCRATCH/fakebin:/usr/bin:/bin" "GOROOT=/nonexistent/stale/goroot" \
    bash -c '
      . "$1/.softhouse/bin/go-env.sh"
      printf "  final GOROOT      : %s\n" "${GOROOT:-<unset>}"
      printf "  GEREGE_GO_SOURCE  : %s\n" "${GEREGE_GO_SOURCE:-<unset>}"
      printf "  does \`go\` work?   : "
      if go version >/dev/null 2>&1; then printf "YES — %s\n" "$(go version)"
      else printf "NO — %s\n" "$(go version 2>&1)"; fi
    ' _ "$dir" >"$SCRATCH/$label.out" 2>"$SCRATCH/$label.err"
  set -e
  printf '%s\n' "--- $label ---"
  sed 's/^/  /' "$SCRATCH/$label.out"
  printf '  stderr:\n'; sed 's/^/    | /' "$SCRATCH/$label.err"
}

echo "============================================================"
echo "SCENARIO: pinned toolchain ABSENT, a usable \`go\` on PATH,"
echo "          and the shell ALREADY CARRIES A STALE GOROOT."
echo "          (the state of any shell that sourced the OLD go-env.sh once)"
echo "============================================================"
probe "$SCRATCH/mine"   mine
probe "$SCRATCH/theirs" theirs
echo
echo "=== ASSESSMENT ==="

M_OUT="$(cat "$SCRATCH/mine.out")"
T_OUT="$(cat "$SCRATCH/theirs.out")"

if contains "$M_OUT" "final GOROOT      : <unset>"; then
  ok "T253b (mine) DROPPED the stale GOROOT"
else bad "T253b did not drop the stale GOROOT"; fi
if contains "$M_OUT" "does \`go\` work?   : YES"; then
  ok "T253b: the fallback go actually RUNS"
else bad "T253b: the fallback go does not run"; fi

if contains "$T_OUT" "final GOROOT      : <unset>"; then
  ok "d7a7ea3 (theirs) also dropped the stale GOROOT"
else
  printf '  NOTE : d7a7ea3 LEAVES the stale GOROOT in place (it exports none, but does\n'
  printf '         not clear the inherited one).\n'
fi
if contains "$T_OUT" "does \`go\` work?   : YES"; then
  ok "d7a7ea3: the fallback go actually RUNS"
else
  printf '  FINDING: d7a7ea3 announces a fallback to a go that then CANNOT RUN, with the\n'
  printf '           very error its own header describes: "cannot find GOROOT directory".\n'
  printf '           The announcement is correct; the substitution it announces does not work.\n'
fi

echo
echo "=== the OTHER direction: what theirs has that mine does not ==="
if PATH=/usr/bin:/bin python3 - "$SCRATCH/theirs.sh" "$MINE" <<'PY'
import sys
theirs = open(sys.argv[1], encoding="utf-8").read()
mine = open(sys.argv[2], encoding="utf-8").read()
print("  GEREGE_GO_STRICT in theirs : %s" % ("GEREGE_GO_STRICT" in theirs))
print("  GEREGE_GO_STRICT in mine   : %s" % ("GEREGE_GO_STRICT" in mine))
PY
then :; fi
echo "  d7a7ea3 offers GEREGE_GO_STRICT=1 — an opt-in HARD REFUSAL, so the rejected"
echo "  alternative is reachable as CONFIG rather than as a patch. T253b has no such"
echo "  switch. On the merits this is THEIRS BETTER and it should be adopted."

echo
if [ "$FAILURES" -eq 0 ]; then
  echo "CROSS-COMPARE: my own assertions held. Differences reported above are findings,"
  echo "not failures — the driver reconciles, not this instrument."
  exit 0
fi
echo "CROSS-COMPARE: $FAILURES assertion(s) about MY OWN implementation FAILED."
exit 1
