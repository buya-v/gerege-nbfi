#!/usr/bin/env bash
# ledger-invariants-compare.sh — the BOTH-DIRECTIONS comparison DEC-2 §4.4.2 turns on.
#
# This is the comparison `drive-red-ledger-invariants.sh` CONTROL B already runs, factored
# out so that the publication gate can consult THE SAME RULE instead of a copy of it. The
# rule is: the guard's finding set, as a set of `(class, file)` pairs, must be EXACTLY the
# set recorded in `.softhouse/guards/ledger-invariants.baseline`. It fails in BOTH
# directions:
#
#   * a (class, file) pair NOT in the baseline appears -> a violation entered a file that
#     had none.  BLOCKED.
#   * a (class, file) pair IN the baseline disappears -> a known violation was silenced.
#     BLOCKED until the baseline is edited, which is a reviewed diff like any other.
#
# The second direction is the one that earns this: it catches a rename that turns the bar
# green while changing nothing. The baseline itself is NOT editable here (Obligation 3).
#
# The extraction expressions below are IDENTICAL to drive-red-ledger-invariants.sh CONTROL B:
#   observed:  grep '^  \[' | sed -E 's/^  \[([A-Z0-9-]+)\] ([^:]+):.*/\1\t\2/' | sort -u
#   expected:  grep -av '^#' | grep -av '^[[:space:]]*$' | sort -u
#   new_pairs:  comm -13 expected observed
#   gone_pairs: comm -23 expected observed
#
# Exit: 0 = the finding set matches the baseline exactly (both directions hold);
#       1 = a deviation (a pair appeared or a baseline pair disappeared) or the baseline is
#           missing/unreadable — never a pass;
#       2 = unusable (no Go toolchain, guard missing or did not build, nexus/ missing).
#
# Usage:
#   bash .softhouse/guards/ledger-invariants-compare.sh [--baseline <path>]
# The optional `--baseline` override exists for TESTING ONLY. The publication path never
# passes it; the committed baseline is the only baseline the gate consults.

set -u -o pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
NEXUS_DIR="$REPO_ROOT/nexus"
GUARD_SRC="$SCRIPT_DIR/ledgerguard"
BASELINE="$REPO_ROOT/.softhouse/guards/ledger-invariants.baseline"

# NO ENVIRONMENT OVERRIDE. An earlier revision honoured `LEDGER_INVARIANTS_BASELINE` here, with a
# comment asserting it "is never set by the publication path". That was an ASSERTION WITH NOTHING
# ENFORCING IT, and it was a working bypass: neither bar-attest.sh nor conformance.sh sanitises the
# environment before invoking this script, so an inherited variable silently redirected the
# publication decision at a forged baseline. MEASURED: plant a balance write in a file with no
# baseline row, regenerate a baseline that includes it, export the variable -> this script exits 0
# and a brand-new I-3 violation publishes clean. A test that needs a different baseline passes
# `--baseline <path>` BELOW: an argument cannot be inherited from an ambient environment, and the
# publication path passes none. [T506 F-6 class: a fail-open instrument reached by inherited state.]

case "${1:-}" in
  --baseline)
    [ -n "${2:-}" ] || { printf 'ledger-compare: --baseline requires a path\n' >&2; exit 2; }
    BASELINE="$2"
    ;;
esac

say() { printf 'ledger-compare: %s\n' "$*"; }
warn() { printf 'ledger-compare: %s\n' "$*" >&2; }

if [ -f "$REPO_ROOT/.softhouse/bin/go-env.sh" ]; then
  # shellcheck disable=SC1090
  . "$REPO_ROOT/.softhouse/bin/go-env.sh"
fi
if ! command -v go >/dev/null 2>&1; then
  warn "no Go toolchain. EXIT 2 — NOT a match, and never a pass."
  exit 2
fi
if [ ! -f "$GUARD_SRC/main.go" ] || [ ! -f "$GUARD_SRC/go.mod" ]; then
  warn "the guard is MISSING at $GUARD_SRC. EXIT 2 — NOT a match."
  exit 2
fi
if [ ! -d "$NEXUS_DIR" ]; then
  warn "$NEXUS_DIR is missing. There is no population to compare. EXIT 2 — NOT a match."
  exit 2
fi
if [ ! -f "$BASELINE" ]; then
  warn "the baseline is MISSING at $BASELINE. Without it this comparison asserts nothing,"
  warn "and 'no baseline' must never read as 'baseline satisfied'. EXIT 1 — refuse."
  exit 1
fi

WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT
BIN="$WORK/ledgerguard"
if ! (cd "$GUARD_SRC" && go build -o "$BIN" .) 2>"$WORK/build.log"; then
  warn "the guard did not compile. EXIT 2 — NOT a match."
  warn "$(LC_ALL=C sed -n '1,10p' "$WORK/build.log")"
  exit 2
fi

out="$("$BIN" --root "$NEXUS_DIR" 2>&1)"
rc=$?

printf '%s\n' "$out" \
  | LC_ALL=C grep -a '^  \[' \
  | LC_ALL=C sed -E 's/^  \[([A-Z0-9-]+)\] ([^:]+):.*/\1\t\2/' \
  | LC_ALL=C sort -u > "$WORK/observed.tsv"

LC_ALL=C grep -av '^#' "$BASELINE" | LC_ALL=C grep -av '^[[:space:]]*$' \
  | LC_ALL=C sort -u > "$WORK/expected.tsv"

new_pairs="$(LC_ALL=C comm -13 "$WORK/expected.tsv" "$WORK/observed.tsv")"
gone_pairs="$(LC_ALL=C comm -23 "$WORK/expected.tsv" "$WORK/observed.tsv")"

if [ -n "$new_pairs" ]; then
  warn "DEVIATION — a (class, file) pair appeared that the baseline does not record. A"
  warn "violation entered a file that had none. Fix it, or record it in the baseline with the"
  warn "argument for why it stands:"
  printf '%s\n' "$new_pairs" | LC_ALL=C sed 's/^/  + /' >&2
fi
if [ -n "$gone_pairs" ]; then
  warn "DEVIATION — a baseline (class, file) pair DISAPPEARED. A known violation was silenced."
  warn "If it was genuinely repaired, remove its row from the baseline in the same commit so"
  warn "the change is visible in the diff — never by the finding quietly vanishing:"
  printf '%s\n' "$gone_pairs" | LC_ALL=C sed 's/^/  - /' >&2
fi

if [ -n "$new_pairs" ] || [ -n "$gone_pairs" ]; then
  exit 1
fi

n="$(LC_ALL=C grep -ac . "$WORK/expected.tsv")"
[ -n "$n" ] || n=0
say "finding set matches the baseline exactly ($n (class, file) pair(s), none added, none silenced)."
exit 0
