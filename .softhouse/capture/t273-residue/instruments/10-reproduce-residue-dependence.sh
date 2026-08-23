#!/usr/bin/env bash
# T273 — REPRODUCE, FIRST-HAND, the dependence of the BAR's verdict on a file in /tmp
# that no commit records.
#
#   usage: 10-reproduce-residue-dependence.sh <label> <residue-path>
#
# THE RESIDUE PATH IS AN ARGUMENT AND NOT A LITERAL IN THIS FILE, DELIBERATELY. The
# first revision of this instrument opened with `RESIDUE=/tmp/t234_matrix2.txt`, and
# the guard this task added to .softhouse/conformance.sh REFUSED IT — correctly, on its
# own terms: a literal shared-temp assignment in a repo-wide search instrument is the
# exact shape whose repair this task exists to prove. The same run also landed this file
# on the fail-open frontier at TIER1, because its reporting arms were `… || echo "(no
# probe line)"`. Both are fixed here rather than pinned, and the refusal is kept in the
# evidence (evidence/33-after-adding-instruments.log) because a guard that catches its
# own author on its first run is worth more than a clean-looking directory.
#
# ENGINE DECLARATION (P-33/P-53/P-75): every text read below is BSD /usr/bin/grep
# invoked by ABSOLUTE PATH with LC_ALL=C, never a bare `grep` off $PATH and never `rg`.
# No `|| echo` arm reports anything: every count is captured into a variable first and
# then reported by an `if`, so nothing here can print a negative it did not measure.
#
# WHAT IT MEASURES, BOTH TERMS (P-67): the fail-open frontier AND the BAR verdict, with
# the residue PRESENT and with it ABSENT, on whatever tree it is run against. It makes
# no claim about which tree that is — the caller says so via <label>, and the instrument
# records `git rev-parse HEAD` and the porcelain count so a reader can tell pre-fix from
# post-fix without trusting the label.
#
# IT IS NOT A GUARD. It prints measurements; the gate is conformance.sh.
set -u

LABEL="${1:?usage: 10-reproduce-residue-dependence.sh <label> <residue-path>}"
RESIDUE="${2:?usage: 10-reproduce-residue-dependence.sh <label> <residue-path>}"
case "$RESIDUE" in
  /*) ;;
  *) echo "T273: <residue-path> must be absolute; got '$RESIDUE'"; exit 2 ;;
esac

R="$(git rev-parse --show-toplevel)" || { echo "T273: not in a git work tree"; exit 2; }
cd "$R" || { echo "T273: cannot enter $R"; exit 2; }

OUT="$R/.softhouse/capture/t273-residue/evidence"
mkdir -p "$OUT" || exit 2
PARK="$(mktemp -d "${TMPDIR:-/tmp}/t273-park.XXXXXXXXXX")" || exit 2
LINT="$R/.softhouse/capture/t238-failopen/instruments/50-failopen-lint.py"
[ -f "$LINT" ] || { echo "T273: the fail-open linter is absent: $LINT"; exit 2; }

dirty="$(git status --porcelain)"
ndirty=$(printf '%s' "$dirty" | LC_ALL=C /usr/bin/grep -c '' ; :)

echo "### T273 residue-dependence reproduction — label=$LABEL"
echo "  tree      : $R"
echo "  HEAD      : $(git rev-parse HEAD)"
echo "  dirty     : ${ndirty:-0} path(s)"
echo "  residue   : $RESIDUE"
echo "  bash      : $BASH_VERSION"
echo "  date      : $(date -u '+%Y-%m-%dT%H:%M:%SZ')"
echo "  park dir  : $PARK"
echo

# CALIBRATION ON A KNOWN POSITIVE (P-72). Before believing any negative below, establish
# that this instrument can SEE the frontier at all: the linter must print its banner and
# at least one FAILOPEN-FRONTIER row on this tree in its ordinary state. A run that
# measured nothing must never read as "no dependence".
calib="$PARK/calib.txt"
( FAILOPEN_LINT_JSON="$PARK/calib.json" python3 "$LINT" ) >"$calib" 2>&1
if ! LC_ALL=C /usr/bin/grep -aqF 'T238 FAIL-OPEN LINT' "$calib"; then
  echo "T273 CALIBRATION FAILED: the linter printed no banner. Nothing below is admissible."
  exit 2
fi
ncal=$(LC_ALL=C /usr/bin/grep -ac '^FAILOPEN-FRONTIER ' "$calib" ; :)
echo "### CALIBRATION (P-72): linter banner present, frontier rows visible = ${ncal:-0}"
if [ "${ncal:-0}" -lt 1 ]; then
  echo "T273 CALIBRATION FAILED: zero frontier rows. A negative from here would be vacuous (P-35)."
  exit 2
fi
echo

report() {   # report <label> <value-or-empty> <text-when-empty>
  if [ -n "$2" ]; then printf '  %-17s: %s\n' "$1" "$2"
  else                 printf '  %-17s: %s\n' "$1" "$3"
  fi
}

arm() {                        # arm <PRESENT|ABSENT>
  local state="$1" f="$PARK/frontier-$1.txt" b="$OUT/${LABEL}-BAR-residue-$1.log"
  local rc n probe verdict refusal row
  echo "=== ARM: residue $state ==="
  echo "  ls $RESIDUE -> $(ls -la "$RESIDUE" 2>&1)"

  ( FAILOPEN_LINT_JSON="$PARK/lint-$state.json" python3 "$LINT" ) >"$PARK/lint-$state.txt" 2>&1
  LC_ALL=C sed -n 's/^FAILOPEN-FRONTIER //p' "$PARK/lint-$state.txt" >"$PARK/f.raw"
  LC_ALL=C sort "$PARK/f.raw" >"$f"
  n=$(LC_ALL=C /usr/bin/grep -ac '' "$f" ; :)
  echo "  frontier rows    : ${n:-0}"
  LC_ALL=C sed 's/^/    /' "$f"
  row="$(LC_ALL=C /usr/bin/grep -a '02-escape-matrix-fix' "$f")" || row=""
  report "02-escape row" "$row" "(absent from the frontier)"

  bash "$R/.softhouse/conformance.sh" >"$b" 2>&1
  rc=$?
  echo "  BAR exit code    : $rc"
  echo "  BAR log          : ${b#"$R"/}"
  echo "  PROBE LINE COUNT : $(LC_ALL=C /usr/bin/grep -ac 'reference oracle .* probe = ' "$b" ; :)"
  probe="$(LC_ALL=C /usr/bin/grep -a 'reference oracle .* probe = ' "$b")" || probe=""
  report "probe line" "$probe" "(NO PROBE LINE — read the ABSENCE, not a value: P-83)"
  verdict="$(LC_ALL=C /usr/bin/grep -a '^VERDICT' "$b")" || verdict=""
  report "VERDICT line" "$verdict" "(no VERDICT line was printed)"
  refusal="$(LC_ALL=C /usr/bin/grep -a -m1 'no verdict is available' "$b")" || refusal=""
  report "refusal line" "$refusal" "(no refusal line was printed)"
  echo
  cp "$f" "$OUT/${LABEL}-frontier-residue-$state.txt"
}

# --- ARM 1: exactly as the host is right now, whatever that is --------------
had_residue=0
if [ -e "$RESIDUE" ]; then
  had_residue=1
  cp "$RESIDUE" "$PARK/residue.bak" || exit 2
else
  # A clean host has no residue. To measure the PRESENT arm at all we must make one,
  # and we SAY SO rather than letting the reader assume the host supplied it.
  echo "### NOTE: the residue was ABSENT at start; this instrument SYNTHESISES it for the PRESENT arm."
  { printf 'x1y\nxdy\nx y\nxsy\nx_y\nxwy\n'; } >"$RESIDUE" || exit 2
  cp "$RESIDUE" "$PARK/residue.bak" || exit 2
fi
arm PRESENT

# --- ARM 2: the clean host / post-reboot state ------------------------------
rm -f "$RESIDUE" || exit 2
arm ABSENT

# --- restore host state exactly as found ------------------------------------
if [ "$had_residue" = 1 ]; then
  cp "$PARK/residue.bak" "$RESIDUE" && echo "### host state RESTORED: $RESIDUE put back ($(ls -la "$RESIDUE"))"
else
  echo "### host state RESTORED: $RESIDUE left ABSENT, as it was at start"
fi
rm -rf "$PARK"
echo "### done — label=$LABEL"
