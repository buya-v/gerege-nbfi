#!/bin/sh
# T152 — DRIVE THE SWEEP'S OWN PATTERNS AGAINST THE INPUT THAT DEFEATS THEM.
#
# T135-3.  T99's sweep pattern for the vacuous-check shape was the three literals `grep -c`,
# `grep -ac`, `wc -l`.  Over `main`'s preconditions.sh it found ONE line — and that line, `pgdrv`,
# is the one site in the block that is NOT vacuous, because it asserts PRESENCE.  The two
# Oracle-Database/MySQL/MariaDB prohibition assertions it existed to find were written `grep -icE`
# and it could not match them.  T99b widened it once; T135 then built TEN alternate spellings of
# the same shape, showed all ten pass vacuously on empty input, and measured that the widened
# patterns matched ONE LINE EACH.
#
# A sweep whose stated limits omit the limit that already bit it reads as exhaustive.  So this
# script does two things, neither of which is a claim:
#
#   LEG 1  runs the ten spellings and shows that every one of them PRINTS A PASS ON EMPTY INPUT.
#          If any of them did not, the corpus would not be a corpus of the defect.
#   LEG 2  runs the sweep's patterns — EXTRACTED FROM sweep.sh ITSELF, never retyped, so there is
#          no second copy to drift (P-27) — over that corpus, for the OLD patterns (read from git
#          at the pre-T152 T99 head) and the NEW ones side by side.
#
# What this script does NOT establish, and neither does the widening: that the patterns are a
# DETECTOR.  They are a list of idioms and the space of idioms is unbounded.  See sweep.sh's
# "WHAT THIS SWEEP CANNOT FIND".
#
# Hermetic: no oracle, no network, no docker, no git write.  Corpus is built under /tmp.
#
# Usage:  sh prove-sweep-patterns.sh
# Exit:   0 = 10/10 fire on empty input AND the new patterns cover all ten AND the old ones do not;
#         1 = otherwise; 2 = setup failed.
set -u

T99=$(cd "$(dirname "$0")" && pwd)
REPO=$(git -C "$T99" rev-parse --show-toplevel)
PB=.softhouse/capture/pathb
WORK=${T152_SWEEP_WORK:-/tmp/t152-sweep}
# The pre-T152 sweep.sh, as a LITERAL sha for the reason FORK-POINT-SHA gives.
T99_HEAD=8474bf0cc613e577cfa344428eb4b79c24a004c9

die() { printf 'SWEEP PATTERN PROOF ABORT: %s\n' "$1" >&2; exit 2; }

rm -rf "$WORK" || die "cannot clear $WORK"
mkdir -p "$WORK/corpus" || die "cannot create $WORK"

# --------------------------------------------------------------------- the corpus (T135's ten)
cat > "$WORK/corpus/missprobe.sh" <<'PROBE'
#!/bin/sh
# Ten spellings of "I found nothing wrong".  Every one is TRUE on empty input.
hits=$(printf '%s' "" | grep -i -c 'mariadb')          # 1  split flag cluster
[ "$hits" = "0" ] && echo PASS1
n=$(printf '%s' "" | grep --count 'ojdbc')             # 2  long flag
[ "$n" -eq 0 ] && echo PASS2                           #    -eq instead of =
BANNED=$(printf '%s' "" | grep -icE 'oracle')          # 3  UPPERCASE variable name
[ "$BANNED" = "0" ] && echo PASS3
if ! printf '%s' "" | grep -q 'mysql-connector'; then echo PASS4; fi   # 4  no count at all
out=$(printf '%s' "")
[ "x$out" = "x" ] && echo PASS5                        # 5  x-prefix idiom
[ ${#out} -eq 0 ] && echo PASS6                        # 6  string-length idiom
printf '' > scan.txt
[ -s scan.txt ] || echo PASS7                          # 7  a file test, not a variable test
awk 'END{if(NR==0) print "PASS8"}' scan.txt            # 8  verdict inside another language
case "$out" in "") echo PASS9 ;; esac                  # 9  a case arm, not a test
test -z "$out" && echo PASS10                          # 10 bracketless `test -z`
PROBE

echo "=== LEG 1 — every spelling in the corpus PASSES ON EMPTY INPUT"
( cd "$WORK/corpus" && sh missprobe.sh ) > "$WORK/fired.txt" 2>&1
FIRED=$(LC_ALL=C grep -ac '^PASS' "$WORK/fired.txt")
echo "  PASS lines printed with nothing to scan: $FIRED of 10"
sed 's/^/    /' "$WORK/fired.txt"
echo "  (this is the corpus validating itself — a spelling that did not fire would not be an"
echo "   instance of the defect, and including it would inflate the miss count below)"

# ------------------------------------------- the patterns, EXTRACTED, never retyped (no 2nd copy)
git -C "$REPO" show "$T99_HEAD:$PB/t99/sweep.sh" > "$WORK/sweep-old.sh" \
  || die "cannot read the pre-T152 sweep.sh from $T99_HEAD"
cp "$T99/sweep.sh" "$WORK/sweep-new.sh" || die "cannot read the shipped sweep.sh"

extract() {   # <file> -> the section-3 recursive grep lines, one per line
  LC_ALL=C awk '/^hr "3\./{s=1} /^hr "4\./{s=0} s && /^LC_ALL=C grep -rnE/' "$1"
}

run_patterns() {   # <label> <file>  — prints the hits, and leaves the matched LINE NUMBERS in a file
  : > "$WORK/raw-$1.txt"
  _i=0
  extract "$2" > "$WORK/pat-$1.txt"
  while IFS= read -r _line; do
    _i=$((_i+1))
    _cmd=$(printf '%s' "$_line" | sed -e "s|--exclude-dir=t99 \.|$WORK/corpus|")
    printf '  pattern %s:\n' "$_i"
    ( cd "$WORK/corpus" && eval "$_cmd" ) 2>/dev/null | tee -a "$WORK/raw-$1.txt" \
      | sed -e 's|.*/corpus/||' -e 's/^/      /'
  done < "$WORK/pat-$1.txt"
  LC_ALL=C awk -F: '{print $2}' "$WORK/raw-$1.txt" | sort -n -u > "$WORK/hits-$1.txt"
}

echo
echo "=== LEG 2a — the PRE-T152 patterns ($T99_HEAD), over that corpus"
echo "  patterns extracted from sweep.sh section 3: $(extract "$WORK/sweep-old.sh" | wc -l | tr -d ' ')"
run_patterns old "$WORK/sweep-old.sh"
OLD_LINES=$(sort -n -u "$WORK/hits-old.txt" | LC_ALL=C grep -c '[0-9]')
echo "  distinct corpus lines matched: $OLD_LINES"

echo
echo "=== LEG 2b — the SHIPPED patterns, over the same corpus"
echo "  patterns extracted from sweep.sh section 3: $(extract "$WORK/sweep-new.sh" | wc -l | tr -d ' ')"
run_patterns new "$WORK/sweep-new.sh"
NEW_LINES=$(sort -n -u "$WORK/hits-new.txt" | LC_ALL=C grep -c '[0-9]')
echo "  distinct corpus lines matched: $NEW_LINES"

# Which of the ten spellings is REACHABLE by the sweep?  A spelling is reachable if the sweep
# prints a line a reader would land on for it — the line carrying its verdict, or (for the three
# whose value is computed on the preceding line) that producer line.
#
# The line numbers are DERIVED FROM THE CORPUS AT RUN TIME, never hard-coded: the first draft of
# this script hard-coded them, the corpus gained a header line, and the whole table came out one
# row wrong — reporting 7 of 10 for patterns that in fact reach all ten.  A guard whose reference
# data is a transcribed constant is green or red for reasons that have nothing to do with the
# thing under test (P-29).
echo
echo "=== COVERAGE — one row per spelling (line numbers derived from the corpus, not transcribed)"
covered=0
old_covered=0
i=1
while [ "$i" -le 10 ]; do
  v=$(LC_ALL=C grep -n "PASS$i\\b" "$WORK/corpus/missprobe.sh" | LC_ALL=C awk -F: 'NR==1{print $1}')
  [ -n "$v" ] || die "corpus does not contain a PASS$i line"
  case $i in 1|2|3) lines="$((v-1)) $v" ;; *) lines="$v" ;; esac
  o=no; n=no
  for l in $lines; do
    LC_ALL=C grep -qx "$l" "$WORK/hits-old.txt" && o=yes
    LC_ALL=C grep -qx "$l" "$WORK/hits-new.txt" && n=yes
  done
  printf '  spelling %-2s  line(s) %-6s  pre-T152: %-3s  shipped: %s\n' "$i" "$lines" "$o" "$n"
  [ "$n" = yes ] && covered=$((covered+1))
  [ "$o" = yes ] && old_covered=$((old_covered+1))
  i=$((i+1))
done
echo "  spellings reachable, pre-T152: $old_covered of 10   shipped: $covered of 10"

echo
echo "=== VERDICT"
rc=0
[ "$FIRED" = 10 ] || { echo "  the corpus does not demonstrate the defect ($FIRED of 10 fired)"; rc=1; }
[ "$covered" = 10 ] || { echo "  the shipped patterns cover only $covered of 10"; rc=1; }
[ "$OLD_LINES" -lt "$NEW_LINES" ] || { echo "  the widening did not widen anything ($OLD_LINES -> $NEW_LINES)"; rc=1; }
if [ "$rc" = 0 ]; then
  echo "  10 of 10 spellings pass vacuously on empty input."
  echo "  Pre-T152: 2 patterns, $OLD_LINES corpus line(s) matched, $old_covered of 10 spellings reachable."
  echo "  Shipped:  4 patterns, $NEW_LINES corpus line(s) matched, $covered of 10 spellings reachable."
  echo
  echo "RESULT: sweep patterns WIDENED — measured against the corpus that defeated them, both"
  echo "        before and after.  THIS IS NOT A CLAIM THAT THE SWEEP IS A DETECTOR: it is a list"
  echo "        of eleven idioms where it was two, and spelling number twelve is still invisible."
  echo "        That residual limit is stated in sweep.sh's WHAT THIS SWEEP CANNOT FIND, and the"
  echo "        only thing that actually closes the class is a POSITIVE assertion (P-35)."
else
  echo "RESULT: NOT DEMONSTRATED."
fi
exit $rc
