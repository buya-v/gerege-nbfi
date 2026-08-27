#!/bin/sh
# T99 — SWEEP FOR THE SAME SHAPE ELSEWHERE (P-12: a right fix in one place recurs everywhere the
# claim is restated).  Four defect shapes, each searched for across the whole Path B tree, and each
# reported with what the search CANNOT find.
#
# Every grep here is LC_ALL=C.  A BSD grep in a UTF-8 locale matches NOTHING in a file containing an
# invalid multibyte sequence AND RETURNS 0 — a silent zero that has already produced one
# "right numbers, wrong reason" result in this run.  `-a` alone does not fix it; the locale does.
set -u
T99=$(cd "$(dirname "$0")" && pwd)
W=$(cd "$T99/.." && pwd)
cd "$W"

hr() { echo; echo "=== $1"; }

hr "0. locale sanity — are there files here that would make a UTF-8 grep go silently blind?"
n=0
for f in $(LC_ALL=C find . -type f \( -name '*.sh' -o -name '*.py' -o -name '*.txt' -o -name '*.md' \) | sort); do
  if ! LC_ALL=en_US.UTF-8 grep -qa '' "$f" 2>/dev/null; then
    echo "  INVALID-MULTIBYTE (UTF-8 grep would return 0 lines here): $f"
    n=$((n+1))
  fi
done
echo "  files where a UTF-8 grep would go blind: $n"
echo "  (every grep below is LC_ALL=C, so this number does not change what the sweep can see)"

echo
echo "NOTE: greps 1-3 exclude t99/ itself.  This task's own proof scripts quote the defective"
echo "idioms verbatim in their headers, and a hit list dominated by the report about the defect"
echo "is not a hit list.  t99/ is syntax-checked and reviewed separately."

hr "1. basename-only comparisons — the F-1 shape"
echo "--- shell: basename used in a comparison rather than for display"
LC_ALL=C grep -rn 'basename' --include='*.sh' --exclude-dir=t99 . | sed 's|^\./||'
echo "--- python: os.path.basename feeding a name test"
LC_ALL=C grep -rn 'os.path.basename\|\.endswith(.-.\s*+\|realpath\|normpath' --include='*.py' --exclude-dir=t99 . | sed 's|^\./||'
echo "--- any other place a tenant id is compared against a path fragment"
LC_ALL=C grep -rn 'TENANT\"\?\s*)\|\*-\"\$TENANT\|-. + TENANT' --include='*.sh' --include='*.py' --exclude-dir=t99 . | sed 's|^\./||'

hr "2. tools resolved through \$PATH — the F-2 shape"
echo "--- digest tools"
LC_ALL=C grep -rn 'shasum\|sha256sum\|openssl dgst\|md5' --include='*.sh' --include='*.py' --exclude-dir=t99 . | sed 's|^\./||'
echo
echo "--- OTHER unpinned externals in the two scripts that decide whether a capture is admissible"
echo "    (reported, not fixed: see the handoff.  A poisoned \`docker\` defeats P1-P3 and P5-P13;"
echo "     a poisoned \`curl\` defeats P4 and the canary.  Both are far larger jobs than the digest"
echo "     pin, and neither is what T85 raised.)"
for tool in docker curl psql grep sed awk tr cut head unzip javap; do
  c=$(LC_ALL=C grep -c "\\b$tool\\b" t36/preconditions.sh t36/recapture.sh 2>/dev/null | LC_ALL=C awk -F: '{s+=$2} END {print s+0}')
  [ "$c" -gt 0 ] && printf '    %-8s %s occurrence(s) in preconditions.sh + recapture.sh\n' "$tool" "$c"
done
echo "    attest.py computes its digests with hashlib IN PROCESS, so it is not PATH-reachable at all."

hr "3. checks that can pass on an empty input set — the F-3 shape"
echo "--- loops over a glob with a [ -f ] || continue and no counter"
LC_ALL=C grep -rn 'for f in .*\*\|for d in .*\*\|glob(' --include='*.sh' --include='*.py' --exclude-dir=t99 . | sed 's|^\./||'
echo
echo "--- 3a. counting invocations (a zero can mean 'clean' or 'read nothing')"
# T99b CORRECTION.  This pattern used to be the three literals `grep -c`, `grep -ac`, `wc -l`, and
# it therefore COULD NOT SEE `grep -icE`, which is how preconditions.sh:105 and :111 — the
# Oracle-Database / MySQL / MariaDB prohibition assertions, a CLAUDE.md non-negotiable — were
# written.  Both counted over a stream that is empty whenever `docker` answers nothing, and both
# printed PASS for it.  A sweep for a defect shape that cannot match the shape as actually written
# is the same failure as the guards it is looking for: it reported 0 hits having not looked.
# The flag letters are now a character class, so any -c/-ic/-ac/-icE spelling is caught.
#
# T152 CORRECTION (T135-3).  The character class was still not enough.  T135 built ten spellings of
# the same vacuous shape, ALL TEN of which fire on empty input, and measured that T99b's two
# patterns matched ONE line each.  Widened here to also match SPLIT flag clusters (`grep -i -c`),
# the long form (`grep --count`), and `wc -c` as well as `wc -l`.  Reproduced by T152 against a
# rebuild of T135's corpus: 10/10 probes fire on empty input; old patterns 1 line each;
# 3a+3b+3c below match all ten.  The residual limit is stated in WHAT THIS SWEEP CANNOT FIND — and
# it is NOT closable by widening.
LC_ALL=C grep -rnE 'grep([[:space:]]+-[A-Za-z]+)*[[:space:]]+(-[A-Za-z]*c[A-Za-z]*|--count)([[:space:]]|$)|wc[[:space:]]+-[lc]' --include='*.sh' --exclude-dir=t99 . | sed 's|^\./||'
echo
echo "--- 3b. absence assertions: a count or an empty string treated as PROOF OF CLEANLINESS"
echo "    (each of these needs a LIVENESS OPERAND — evidence that the input was non-empty)"
# T152: widened from `[ "$lower_case" = "0" ]` / `[ -z "$lower_case" ]` to also match UPPERCASE and
# mixed-case variable names, `==` and `-eq` as well as `=`, the `[ "x$out" = "x" ]` idiom, the
# `[ ${#out} -eq 0 ]` length idiom, `[[ ... ]]`, and bracketless `test -z`.  It is deliberately
# broader than "absence assertion": it now also matches ordinary exit-status checks such as
# `[ "$rc" = 0 ]`.  That noise is the honest price of breadth — this is a REPORT a human reads, not
# a guard that gates anything, so a false positive costs a glance and a false negative cost two P0s.
LC_ALL=C grep -rnE '\[+[[:space:]]+"?(x)?\$\{?#?[A-Za-z_][A-Za-z0-9_]*\}?"?[[:space:]]+(=|==|-eq)[[:space:]]+"?(0|x)"?[[:space:]]+\]|\[+[[:space:]]+-z[[:space:]]|(^|[;&|[:space:]])test[[:space:]]+-z[[:space:]]' --include='*.sh' --exclude-dir=t99 . | sed 's|^\./||'
echo
echo "--- 3c. the same verdict written WITHOUT a count and WITHOUT a string test"
echo "    (grep -q as an absence test, [ -s file ], awk NR==0, case-on-empty)"
# T152: these four spellings never mention a number or an empty-string comparison at all, so
# neither 3a nor 3b can see them, and every one of them is TRUE on empty input.
LC_ALL=C grep -rnE '(^|[;&|(!][[:space:]]*|[[:space:]]!?[[:space:]]*)grep([[:space:]]+-[A-Za-z]+)*[[:space:]]+-[A-Za-z]*q[A-Za-z]*([[:space:]]|$)|\[+[[:space:]]+-s[[:space:]]|NR[[:space:]]*==[[:space:]]*0|case[[:space:]]+"?\$[A-Za-z_][A-Za-z0-9_]*"?[[:space:]]+in[[:space:]]+"?\)|in[[:space:]]+""\)' --include='*.sh' --exclude-dir=t99 . | sed 's|^\./||'
echo
echo "--- 3d. the Python side of the same shape (len()==0, not x, == [], no counter)"
LC_ALL=C grep -rnE 'len\([A-Za-z_][A-Za-z0-9_.]*\)[[:space:]]*==[[:space:]]*0|if[[:space:]]+not[[:space:]]+[A-Za-z_][A-Za-z0-9_.]*[[:space:]]*:|==[[:space:]]*\[\]|==[[:space:]]*\{\}|\.count\([^)]*\)[[:space:]]*==[[:space:]]*0' --include='*.py' --exclude-dir=t99 . | sed 's|^\./||'

hr "4. capture directories with no in-band provenance — the F-4 shape"
python3 - <<'EOF'
import json, os
root = os.getcwd()
idx = json.load(open(os.path.join(root, 'PROVENANCE-INDEX.json')))
rows = idx['directories']
print('  %-42s %-9s %-8s %s' % ('directory', 'stamp', 'tier-A', 'tenant'))
for r in rows:
    a = 'yes' if any(e['tier'] == 'A' for e in r['evidence']) else 'NO'
    print('  %-42s %-9s %-8s %s' % (r['path'], r['in_band_stamp'] or '-', a,
                                    r['tenant'] or 'NOT ESTABLISHED'))
print('  totals: %d directories, %d stamped, %d with tier-A evidence, %d with no tenant established'
      % (len(rows),
         sum(1 for r in rows if r['in_band_stamp']),
         sum(1 for r in rows if any(e['tier'] == 'A' for e in r['evidence'])),
         sum(1 for r in rows if not r['tenant'])))
EOF

hr "WHAT THIS SWEEP CANNOT FIND"
cat <<'EOF'
  * Anything outside .softhouse/capture/pathb/.  The sweep is scoped to this tree; sibling capture
    trees (.softhouse/capture/audit-t44/ is owned by another worker this fire) were not searched.
  * A basename comparison written some other way — `${x##*/}`, `awk -F/ '{print $NF}'`, a Python
    `split('/')[-1]`.  Greps 1 finds the idioms actually used here; it does not bound the space.
  * A tool invoked through a variable (`$DOCKER`, `$PY`) or through a shell function, since the
    literal name never appears at the call site.
  * A vacuous check whose emptiness comes from something other than a glob — an empty SQL result,
    an empty JSON array, a `for` over an unset variable.

  * >>> THE ONE THAT ALREADY BIT THIS PROGRAM, AND THE ONE WIDENING CANNOT CLOSE <<<
    A VACUOUS CHECK WRITTEN IN A SPELLING GREP 3 DOES NOT ENUMERATE.  Grep 3 is a LIST OF IDIOMS,
    not a decision procedure, and the set of ways to write "I found nothing wrong" in shell is
    unbounded.  ZERO HITS FROM GREP 3 IS THEREFORE NOT EVIDENCE OF ABSENCE.  This is not a
    hypothetical limit: it is the exact failure that produced two P0s in this tree.

    T99's original pattern was the three literals `grep -c`, `grep -ac`, `wc -l`.  It found ONE
    line in preconditions.sh — and that line (`pgdrv`) was the one site in the block that is NOT
    vacuous, because it asserts PRESENCE.  The two Oracle-Database/MySQL/MariaDB prohibition
    assertions it existed to find were written `grep -icE`, and it could not match them.

    T135 then measured the widened pattern against a corpus of TEN alternate spellings of the same
    shape.  ALL TEN pass vacuously on empty input; T99b's two patterns matched 1 line each.  The
    ten, named so a later reader can re-run them rather than trust this paragraph:

      1.  grep -i -c 'x'                      split flag cluster — `-c` is not adjacent to `grep -`
      2.  grep --count 'x'                    the GNU long form
      3.  [ "$n" -eq 0 ]                      -eq instead of =
      4.  BANNED=$(... ); [ "$BANNED" = "0" ] an UPPERCASE variable name
      5.  if ! grep -q 'x'; then ...          no count and no number anywhere
      6.  [ "x$out" = "x" ]                   the x-prefix empty-string idiom
      7.  [ ${#out} -eq 0 ]                   the string-length idiom
      8.  [ -s scan.txt ] || ...              a file test, not a variable test
      9.  awk 'END{if(NR==0) print "PASS"}'   the verdict inside another language
      10. case "$out" in "") echo PASS ;;     a case arm, not a test

    Grep 3 was widened by T152 (3a split flags + `--count` + `wc -c`; 3b uppercase, `==`, `-eq`,
    `x$`, `${#}`, `[[`, bracketless `test -z`; 3c `grep -q`, `[ -s ]`, `NR==0`, case-on-empty; 3d
    the Python forms) and now matches all ten.  THAT DOES NOT MAKE IT A DETECTOR.  It makes it a
    list of eleven idioms instead of two.  Number twelve — a helper function `is_clean()`, a
    `[ $(...) -lt 1 ]`, a Python `sum(1 for ...) < 1`, a jq `length == 0`, a check whose emptiness
    is delivered through a variable this sweep never reads — is invisible here and will stay
    invisible.

    THE ONLY THING THAT ACTUALLY CLOSES THIS CLASS IS NOT A SWEEP.  Per P-35: write the assertion
    POSITIVELY — "N items were inspected, and each equalled its expected value" — and make ZERO
    INSPECTED an error.  The reviewer's one-line test is "would the PASS sentence still print on
    empty input?"  A sweep can only ever suggest where to ask that question.
  * Whether a capture's recorded tenant is TRUE.  The index records what the evidence says and what
    tier it is; it cannot promote tier-B prose into an observation, and it does not try.
EOF
