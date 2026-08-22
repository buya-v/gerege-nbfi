#!/usr/bin/env bash
# T239 — RE-RUN r11-hygiene.sh's check #2 (line 35) with a SOUND instrument.
#
# ORIGINAL (verbatim from .softhouse/reviews/T138-evidence/r11-hygiene.sh:35-37):
#   git grep -n -a -E 'merge-base|main:|origin/main|rev-parse main|\bmain\b' "$T115" -- <3 paths>
#
# Engines used, per the calibration in transcripts/00-engines.txt:
#   ORIGINAL  git grep -E   — reads \b as literal b   (DEFECTIVE; the engine T138 actually got)
#   SOUND     git grep -P   — PCRE, honours \b        (CALIBRATED: hits fixture line 1)
# BSD /usr/bin/grep -E is also sound but cannot take a commit argument, so it cannot search the
# T115 tree directly; it is used in 21-crosscheck.sh against `git show` output instead.
set -u
cd "${1:?repo}" || { echo "FATAL: cd failed — INSTRUMENT IS VOID"; exit 2; }
T115=bd59187cf83c7c7161db23668e91d45bd46be2a8
P1=.softhouse/capture/t91/
P2=.softhouse/capture/charges/bin/preconditions.sh
P3=.softhouse/capture/audit-t44/charges/bin/preconditions-COPY.sh
FIVE='merge-base|main:|origin/main|rev-parse main|\bmain\b'
FOUR='merge-base|main:|origin/main|rev-parse main'
TERM='\bmain\b'
OUT=.softhouse/capture/t239-r11-rerun/evidence

echo "PWD=$(pwd)  HEAD=$(git rev-parse HEAD)"
echo "population: T115 tree ($T115), 3 pathspecs — 200 files / 8170 lines [10-population.sh]"
echo

echo "=================================================================="
echo "A. THE ORIGINAL INSTRUMENT, VERBATIM — git grep -E, five alternatives"
echo "=================================================================="
git grep -n -a -E "$FIVE" "$T115" -- "$P1" "$P2" "$P3" > "$OUT/hits-original-E-five.txt" 2>&1 || true
a=$(wc -l < "$OUT/hits-original-E-five.txt" | tr -d ' ')
echo "hit lines: $a"
cat "$OUT/hits-original-E-five.txt" | sed 's/^/   /'
echo

echo "=================================================================="
echo "B. FOUR ALTERNATIVES ONLY (the literal ones) — isolates the 5th term"
echo "=================================================================="
git grep -n -a -E "$FOUR" "$T115" -- "$P1" "$P2" "$P3" > "$OUT/hits-original-E-four.txt" 2>&1 || true
b=$(wc -l < "$OUT/hits-original-E-four.txt" | tr -d ' ')
echo "hit lines: $b"
echo "  => under git grep -E the 5th term contributes $((a-b)) lines"
echo

echo "=================================================================="
echo "C. THE SOUND INSTRUMENT — git grep -P, five alternatives, SAME TREE"
echo "=================================================================="
git grep -n -a -P "$FIVE" "$T115" -- "$P1" "$P2" "$P3" > "$OUT/hits-sound-P-five.txt" 2>&1 || true
c=$(wc -l < "$OUT/hits-sound-P-five.txt" | tr -d ' ')
echo "hit lines: $c"
git grep -n -a -P "$FOUR" "$T115" -- "$P1" "$P2" "$P3" > "$OUT/hits-sound-P-four.txt" 2>&1 || true
d=$(wc -l < "$OUT/hits-sound-P-four.txt" | tr -d ' ')
echo "four-alternative under -P: $d"
echo "  => under git grep -P the 5th term contributes $((c-d)) lines"
echo

echo "=================================================================="
echo "D. THE RATIO — BOTH TERMS NAMED, BOTH COUNTED IN THE LIVE ARTEFACT (P-67)"
echo "=================================================================="
echo "  NUMERATOR   (hit lines the sound instrument found that the original did NOT) = $((c-a))"
echo "  DENOMINATOR (hit lines the sound instrument found in total)                  = $c"
if [ "$c" -gt 0 ]; then
  echo "  recall of the ORIGINAL instrument = $a / $c = $(python3 -c "print('%.1f%%' % (100.0*$a/$c))")"
  echo "  RECALL LOSS                       = $((c-a)) / $c = $(python3 -c "print('%.1f%%' % (100.0*($c-$a)/$c))")"
fi
echo "  counted in: $OUT/hits-original-E-five.txt and $OUT/hits-sound-P-five.txt, both committed."
echo

echo "=================================================================="
echo "E. THE DELTA — exactly what the check NEVER SAW"
echo "=================================================================="
sort "$OUT/hits-original-E-five.txt" > /tmp/t239-a.txt
sort "$OUT/hits-sound-P-five.txt"    > /tmp/t239-c.txt
comm -13 /tmp/t239-a.txt /tmp/t239-c.txt > "$OUT/delta-unseen.txt"
comm -23 /tmp/t239-a.txt /tmp/t239-c.txt > "$OUT/delta-original-only.txt"
echo "lines the SOUND instrument found and the ORIGINAL missed : $(wc -l < "$OUT/delta-unseen.txt" | tr -d ' ')"
echo "lines the ORIGINAL found and the SOUND one does NOT      : $(wc -l < "$OUT/delta-original-only.txt" | tr -d ' ')"
echo "  (the second number is NOT necessarily zero: git grep -E's \\bmain\\b matches the literal"
echo "   string 'bmainb', so the defective engine can produce a FALSE POSITIVE as well as misses)"
echo
echo "--- ORIGINAL-ONLY lines, if any ---"
cat "$OUT/delta-original-only.txt" | sed 's/^/   /'
echo

echo "=================================================================="
echo "F. WHICH MECHANISM KILLED IT? (P-72 — two mechanisms, one zero)"
echo "=================================================================="
echo "Mechanism 2 (engine reads \\b as literal b):"
echo -n "   git grep -E -c 'bmainb' over the population : "
git grep -c -a -E -- 'bmainb' "$T115" -- "$P1" "$P2" "$P3" 2>/dev/null | awk -F: '{s+=$NF} END{print s+0}'
echo -n "   git grep -E -c '\\bmain\\b' over the population: "
git grep -c -a -E -- "$TERM" "$T115" -- "$P1" "$P2" "$P3" 2>/dev/null | awk -F: '{s+=$NF} END{print s+0}'
echo -n "   git grep -P -c '\\bmain\\b' over the population: "
git grep -c -a -P -- "$TERM" "$T115" -- "$P1" "$P2" "$P3" 2>/dev/null | awk -F: '{s+=$NF} END{print s+0}'
echo
echo "Mechanism 1 (right-anchoring an inflected stem — T224's killer):"
echo "   'main' is not a stem being inflected here. Control: does the population contain"
echo "   tokens where \\bmain\\b would wrongly fail but a stem match would succeed?"
echo -n "   -P 'main[a-z]+' (main as a PREFIX of a longer word, which \\bmain\\b correctly excludes): "
git grep -c -a -P -- 'main[a-z]+' "$T115" -- "$P1" "$P2" "$P3" 2>/dev/null | awk -F: '{s+=$NF} END{print s+0}'
echo -n "   -P '[a-z]+main' (main as a SUFFIX, e.g. domain):                                      "
git grep -c -a -P -- '[a-z]+main' "$T115" -- "$P1" "$P2" "$P3" 2>/dev/null | awk -F: '{s+=$NF} END{print s+0}'
