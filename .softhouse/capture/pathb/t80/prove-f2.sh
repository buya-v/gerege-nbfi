#!/bin/sh
# T80 — proof for T85 F-2: when P7 (PostgreSQL version) fails, the REST of the suite must still run.
#
# `preconditions.sh` had `'$PIN_PG_MAJOR_MINOR…'` — the identifier ran straight into U+2026 (bytes
# e2 80 a6), bash read 0xe2 as part of the name, and under `set -u` the script DIED at that line.
# It failed closed (exit 1), so it was never a false pass; but every check after P7 — P8 through P15,
# INCLUDING THE ENTIRE ROUNDING-MODE CANARY — silently never ran, and the breach summary never
# printed.  The strongest assertion in the rig was disabled by a single environment drift.
#
# The probe forces P7 and only P7 to fail (probe/docker answers `select version()` with a wrong
# version and forwards everything else to the real binary), then runs BOTH the pre-fix script from
# git and the fixed one, and counts what actually executed.
set -u
T80=$(cd "$(dirname "$0")" && pwd)
W=$(cd "$T80/.." && pwd)
O=$T80/out
CANON=$W/t22-audit/req/calc-pmode2-gerege.json
PREFIX_COMMIT=813acb1                     # T80's own pre-F-2 preconditions.sh
SH=${SH:-sh}
cd "$W"

chmod +x "$T80/probe/docker" 2>/dev/null

git show "$PREFIX_COMMIT:.softhouse/capture/pathb/t36/preconditions.sh" > "$O/.f2-prefix.sh"

echo "=== T85 F-2 — a guard that dies instead of firing"
echo "run at $(date -u +%Y-%m-%dT%H:%M:%SZ)   interpreter: $SH"
echo "probe: docker shim answers 'select version()' with PostgreSQL 9.9.9 so P7, and only P7, fails"
echo

# LC_ALL=C AND grep -a ARE BOTH REQUIRED HERE.  The pre-fix transcript ends in `PIN_PG_MAJOR_MINOR<e2>: unbound
# variable`, an invalid UTF-8 byte; BSD grep suppresses matches it considers binary, so a plain
# `grep -c` reported NOTHING for the very line that proves the defect.  And `-a` alone is NOT
# enough: BSD /usr/bin/grep in a UTF-8 locale cannot match a line carrying an invalid multibyte
# sequence at all, so it returns 0 rather than 1 [measured: `grep -ac` -> 0, `LC_ALL=C grep -ac`
# -> 1, same file].  A counter that silently returns zero on the evidence it is counting is the
# same failure this whole task is about.
report() {                                  # report <label> <transcript>
  t=$2
  echo "  exit status ................. $3"
  echo "  PASS lines ................. $(LC_ALL=C grep -ac '^  PASS' "$t" || true)"
  echo "  FAIL lines ................. $(LC_ALL=C grep -ac '^  FAIL' "$t" || true)"
  echo "  P7 breach reported ......... $(LC_ALL=C grep -ac 'PostgreSQL version is' "$t" || true)"
  echo "  checks AFTER P7 (P8-P15):"
  echo "    tenant row (P8) .......... $(LC_ALL=C grep -ac "tenant 'gerege' exists" "$t" || true)"
  echo "    timezone (P9) ............ $(LC_ALL=C grep -ac 'timezone_id' "$t" || true)"
  echo "    rounding-mode row (P10) .. $(LC_ALL=C grep -ac 'rounding-mode' "$t" || true)"
  echo "    JVM mode in force (P13) .. $(LC_ALL=C grep -ac 'running JVM initialized' "$t" || true)"
  echo "    CANARY digest pin (P14b) . $(LC_ALL=C grep -ac 'canary request pinned by DIGEST' "$t" || true)"
  echo "    CANARY arithmetic (P14c) . $(LC_ALL=C grep -ac 'effective rounding mode canary' "$t" || true)"
  echo "    MNT currency (P15) ....... $(LC_ALL=C grep -ac 'MNT seeded' "$t" || true)"
  echo "  breach summary printed ..... $(LC_ALL=C grep -ac 'PRECONDITIONS BREACHED' "$t" || true)"
  echo "  unbound-variable death ..... $(LC_ALL=C grep -ac 'unbound variable' "$t" || true)"
}

echo "--- 1. PRE-FIX preconditions.sh ($PREFIX_COMMIT)"
PATH="$T80/probe:$PATH" CANARY_REQ="$CANON" "$SH" "$O/.f2-prefix.sh" gerege > "$O/.f2-prefix.txt" 2>&1
st1=$?
report prefix "$O/.f2-prefix.txt" "$st1"
echo "  last line: $(tail -1 "$O/.f2-prefix.txt")"
echo

echo "--- 2. FIXED preconditions.sh (this branch)"
PATH="$T80/probe:$PATH" CANARY_REQ="$CANON" "$SH" t36/preconditions.sh gerege > "$O/.f2-fixed.txt" 2>&1
st2=$?
report fixed "$O/.f2-fixed.txt" "$st2"
echo

echo "--- 3. the FIXED transcript in full, so the count above is checkable"
sed 's/^/  | /' "$O/.f2-fixed.txt"
echo

echo "--- 4. attest.py under the same probe (T85: the pre-fix form died with UnicodeDecodeError)"
PATH="$T80/probe:$PATH" ATTEST_OUT="$O/f2-attest-gerege" ATTEST_TASK=T80 \
  python3 t36/attest.py gerege > "$O/.f2-attest.txt" 2>&1
st3=$?
echo "  exit status ................. $st3"
echo "  UnicodeDecodeError ......... $(LC_ALL=C grep -ac 'UnicodeDecodeError' "$O/.f2-attest.txt" || true)"
echo "  Traceback .................. $(LC_ALL=C grep -ac 'Traceback' "$O/.f2-attest.txt" || true)"
echo "  clean ABORT message ........ $(LC_ALL=C grep -ac 'ABORT: preconditions breached' "$O/.f2-attest.txt" || true)"
echo "  wrote anything into f2-attest-gerege: $( [ -d "$O/f2-attest-gerege" ] && echo YES || echo no )"
echo

rc=0
canary_prefix=$(LC_ALL=C grep -ac 'effective rounding mode canary' "$O/.f2-prefix.txt" || true)
canary_fixed=$(LC_ALL=C grep -ac 'effective rounding mode canary' "$O/.f2-fixed.txt" || true)
summary_fixed=$(LC_ALL=C grep -ac 'PRECONDITIONS BREACHED' "$O/.f2-fixed.txt" || true)
[ "$canary_prefix" = "0" ] || { echo "UNEXPECTED: the pre-fix script ran the canary"; rc=1; }
[ "$canary_fixed" = "1" ] || { echo "FAIL: the fixed script did not run the canary"; rc=1; }
[ "$summary_fixed" = "1" ] || { echo "FAIL: the fixed script printed no breach summary"; rc=1; }
[ "$st2" = "1" ] || { echo "FAIL: the fixed script did not exit 1"; rc=1; }
[ "$st3" = "1" ] || { echo "FAIL: attest.py did not exit 1"; rc=1; }
[ -d "$O/f2-attest-gerege" ] && { echo "FAIL: attest.py wrote into its output directory on a breach"; rc=1; }

cp "$O/.f2-prefix.txt" "$O/F2-prefix-transcript-$SH.txt"
cp "$O/.f2-fixed.txt"  "$O/F2-fixed-transcript-$SH.txt"
rm -f "$O/.f2-prefix.sh" "$O/.f2-prefix.txt" "$O/.f2-fixed.txt" "$O/.f2-attest.txt"
[ "$rc" = 0 ] || exit 1
echo "RESULT: F-2 CLOSED — with P7 failing, the fixed script runs P8-P15 including the canary,"
echo "        prints its breach summary, exits 1; and attest.py aborts cleanly instead of crashing."
exit 0
