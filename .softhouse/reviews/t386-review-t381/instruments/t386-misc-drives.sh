#!/usr/bin/env bash
# T386 -- three small drives the review owes its own claims.
#
#   bash .softhouse/reviews/t386-review-t381/instruments/t386-misc-drives.sh <repo> <ref>
#
#  M1  IS `:127`'s SURVIVING `2>/dev/null` REALLY FAIL-CLOSED?  T381 asserts it is. Drive it:
#      make `git rev-parse --show-toplevel` fail and read what the sweep does.
#  M2  THE INVERSE DEFECT IN sel()'s NEW CHECK. `printf | grep -q` under `pipefail`: `grep -q`
#      exits on the FIRST match, so `printf` can take EPIPE and `pipefail` would hand back
#      printf's non-zero -- which `esc_rc >= 2` reads as "the CHECK ITSELF did not run". A guard
#      that misfires on its own success is the mirror image of one that cannot fire.
#  M3  DOES sel()'s BACKSLASH-CLASS REFUSAL ACTUALLY CATCH A `\b` SELECTOR, and does the sweep
#      still complete on a HEALTHY corpus (the control T383 taught this fire to demand)?
set -uo pipefail
REPO=${1:?usage: <repo> <ref>}
REF=${2:?usage: <repo> <ref>}
SRC='.softhouse/capture/t363-oracle-baseline/instruments/casualty-sweep.sh'
W=$(mktemp -d "${TMPDIR:-/tmp}/t386-misc.XXXXXXXX"); trap 'rm -rf "$W"' EXIT
git -C "$REPO" show "$REF:$SRC" > "$W/sweep.sh" || exit 2
echo "UNDER TEST sha256 $(shasum -a 256 < "$W/sweep.sh" | cut -d' ' -f1)"
echo

echo '=== M1: `git rev-parse --show-toplevel` forced to fail (the surviving 2>/dev/null) =='
mkdir -p "$W/shim1"
cat > "$W/shim1/git" <<SHIM
#!/usr/bin/env bash
if [ "\${1:-}" = "rev-parse" ] && [ "\${2:-}" = "--show-toplevel" ]; then
  echo "fatal: not a git repository" >&2; exit 128
fi
exec $(command -v git) "\$@"
SHIM
chmod +x "$W/shim1/git"
( cd "$REPO" && PATH="$W/shim1:$PATH" bash "$W/sweep.sh" ) > "$W/m1.txt" 2>&1
M1=$?
echo "  exit=$M1"; sed 's/^/    /' "$W/m1.txt" | head -5
if [ "$M1" -eq 2 ] && grep -q 'SWEEP ABORT (exit 2)' "$W/m1.txt"; then
  echo "  >>> CONFIRMED FAIL-CLOSED: the silenced stderr does not hide the failure, because the"
  echo "  >>> status is read by the \`||\` and :128 refuses. T381's classification of :127 stands."
else
  echo "  >>> *** :127 IS NOT FAIL-CLOSED (exit $M1)."
fi
echo

echo '=== M2: does `printf | grep -q` misfire on a SUCCESSFUL match under pipefail? ======'
probe() {   # probe <label> <pattern>  -- the LABEL is printed, never the pattern: one of these
            # is 200 kB and dumping it would bury the result it exists to show.
  local label="$1" pat="$2" rc
  set -uo pipefail
  printf '%s' "$pat" | LC_ALL=C grep -q '\\[bBdDsSwW<>]'; rc=$?
  printf '    %-46s (%s bytes)  pipeline rc=%s\n' "$label" "${#pat}" "$rc"
}
probe 'no backslash-class at all'            'no-escapes-here'
probe 'a real selector pattern'              '\bmain\b'
probe '200 kB of filler THEN the match'      "$(printf 'x%.0s' $(seq 1 200000))\\b"
echo '    (rc 0 = matched, 1 = no match, >=2 would be read by sel() as "the CHECK did not run")'
LONG=$(printf 'x%.0s' $(seq 1 400000))
set -uo pipefail
printf '%s' "\\b$LONG" | LC_ALL=C grep -q '\\[bBdDsSwW<>]'; RC=$?
echo "    match at the FRONT of a 400 kB argument (worst case for EPIPE): rc=$RC"
if [ "$RC" -ge 2 ]; then
  echo "  >>> *** INVERSE DEFECT REPRODUCED: a MATCH is reported as 'the check did not run'."
else
  echo "  >>> no misfire: bash does not surface printf's EPIPE as the pipeline status here."
fi
echo

echo '=== M3: a `\b` selector must be REFUSED, and a healthy sweep must still PASS ======='
python3 - "$W/sweep.sh" "$W/m3.sh" <<'PY'
import sys
src, dst = sys.argv[1], sys.argv[2]
text = open(src, encoding='utf-8').read()
anchor = 'echo\necho "END OF SWEEP.'
assert text.count(anchor) == 1, "anchor not unique"
probe = "sel \"ZZ-T386-PROBE a selector carrying a backslash-class\" -n -E '\\bmain\\b'\n"
text = text.replace(anchor, probe + anchor)
open(dst, 'w', encoding='utf-8').write(text)
# refuse unless the backslash-class survived the round trip
back = open(dst, encoding='utf-8').read()
assert "'\\bmain\\b'" in back, "the backslash-class did NOT survive insertion"
print("    probe selector inserted; backslash-class survived the round trip")
PY
[ $? -eq 0 ] || { echo "  M3: could not insert the probe. DRIVE FAILED."; exit 4; }
( cd "$REPO" && bash "$W/m3.sh" ) > "$W/m3.txt" 2>&1
M3=$?
grep -A4 'ZZ-T386-PROBE' "$W/m3.txt" | sed 's/^/    /'
grep 'SWEEP-RESULT' "$W/m3.txt" | sed 's/^/    /'
echo "  exit=$M3"
if grep -A4 'ZZ-T386-PROBE' "$W/m3.txt" | grep -q 'SELECTOR REFUSED' && [ "$M3" -eq 3 ]; then
  echo "  >>> CONFIRMED: the refusal fires on a real \`\\b\` selector and the run exits 3."
else
  echo "  >>> *** the refusal did NOT fire (exit $M3)."
fi
echo
echo '  --- CONTROL: the SAME shipped script, unmodified, on the SAME healthy corpus ---'
( cd "$REPO" && bash "$W/sweep.sh" ) > "$W/m3c.txt" 2>&1
M3C=$?
grep -E 'SWEEP CALIBRATE|SWEEP OBSERVE|SWEEP-RESULT' "$W/m3c.txt" | sed 's/^/    /'
echo "  control exit=$M3C"
if [ "$M3C" -eq 0 ]; then
  echo "  >>> CONTROL PASSES. The four new refusals do not refuse a healthy fire -- the inverse"
  echo "  >>> defect T383 shipped in this same fire is NOT present here."
else
  echo "  >>> *** THE HEALTHY CONTROL DOES NOT PASS (exit $M3C). That alone is a REJECT."
fi
