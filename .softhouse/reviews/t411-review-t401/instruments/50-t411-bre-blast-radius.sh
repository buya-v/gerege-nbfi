#!/usr/bin/env bash
# T411 item 2: the measuring-instrument defect, and how far it reaches.
#
# T401 reports the effect correctly and the CAUSE wrongly. Its handoff says
# "a BRE `\|` silently drops a branch". It does not. What actually happens in
# BSD grep 2.6.0-FreeBSD is that `$` is an anchor ONLY at the END of the whole
# pattern -- so in `A$\|B$` the FIRST `$` is a literal dollar character and
# branch A can never match a line ending in A. Alternation itself is fine.
#
# The distinction decides the sweep. "Grep for `\|`" -- the sweep T401's
# diagnosis implies -- both over-reports (unanchored `\|` is harmless) and
# under-reports (a mid-pattern anchor is broken with or without `\|`, e.g.
# inside `\(...\)`). So this instrument scores the two separately.
set -uo pipefail
GREP=/usr/bin/grep
ROOT="$(git rev-parse --show-toplevel)" || exit 9
cd "$ROOT" || exit 9

echo "############ 1. THE MECHANISM, DEMONSTRATED ############"
echo "engine under test: $($GREP --version 2>&1 | head -1)"
echo "shim in an interactive shell: $(command -v grep) -> a ugrep shell function (GNU-compatible)"
echo "shim in \`bash script.sh\`   : NOT inherited; scripts get /usr/bin/grep"
echo
FIX='a.sh
b.py
c.zsh'
printf '%s\n' "$FIX" > /dev/null
t() { printf 'a.sh\nb.py\nc.zsh\n' | $GREP -c "$@"; }
printf '  %-34s -> %s   (2 lines should match)\n' "BRE  '\\.sh\$\\|\\.py\$'"  "$(t '\.sh$\|\.py$')"
printf '  %-34s -> %s   exit=%s  <-- undercounts AND reports SUCCESS\n' "  ...its exit status" "" "$( printf 'a.sh\nb.py\nc.zsh\n' | $GREP -c '\.sh$\|\.py$' >/dev/null; echo $?)"
printf '  %-34s -> %s   (alternation ALONE is fine: not a dropped branch)\n' "BRE  '\\.sh\\|\\.py'" "$(t '\.sh\|\.py')"
printf '  %-34s -> %s   (order swapped: the OTHER branch survives)\n' "BRE  '\\.py\$\\|\\.sh\$'" "$(t '\.py$\|\.sh$')"
printf '  %-34s -> %s   (mid-pattern \$ matched a LITERAL dollar: the proof)\n' "BRE  vs line 'a.sh\$X'" "$(printf 'a.sh$X\n' | $GREP -c '\.sh$\|\.py$')"
printf '  %-34s -> %s   (ERE: correct)\n' "ERE  -E '\\.sh\$|\\.py\$'" "$(t -E '\.sh$|\.py$')"
echo
echo "  CONCLUSION: in BSD BRE, \`\$\` is an anchor only at the END of the pattern and"
echo "  \`^\` only at the START. Any earlier occurrence is a literal character. The"
echo "  first branch of an anchored BRE alternation is therefore DEAD, silently, at exit 0."

echo
echo "############ 2. BLAST RADIUS ############"
echo "corpus: tracked *.sh / *.zsh (BRE is a shell-tool concern), $(git ls-files '*.sh' '*.zsh' | $GREP -c .) files"
echo

# CLASS A: a grep/sed invocation WITHOUT -E whose pattern contains \| AND an anchor
#          that is not at the pattern boundary. These are BROKEN TODAY.
# CLASS B: \| without an anchor. Portable-ish; works in BSD and GNU. Not broken.
CA="$(mktemp)"; CB="$(mktemp)"; trap 'rm -f "$CA" "$CB"' EXIT

git grep -n -E '(grep|sed)([[:space:]]+-[A-Za-z]+)*[[:space:]]+[^|]*\\\|' -- '*.sh' '*.zsh' 2>/dev/null \
  > "$CA.all" || true
[ -s "$CA.all" ] || { echo "REFUSE: the idiom search returned NOTHING over a non-empty corpus."; exit 1; }

# split: does the invocation carry -E / -P (then \| is literal, different bug) or not
$GREP -vE 'grep[[:space:]]+(-[A-Za-z]*[EP][A-Za-z]*)|sed[[:space:]]+-E|--extended-regexp' "$CA.all" > "$CA" || true
$GREP -E 'grep[[:space:]]+(-[A-Za-z]*[EP][A-Za-z]*)|sed[[:space:]]+-E|--extended-regexp' "$CA.all" > "$CB" || true

echo "  BRE sites using \\| (no -E/-P)            : $($GREP -c . "$CA" || true)"
echo "  sites using \\| INSIDE an -E/-P pattern   : $($GREP -c . "$CB" || true)   <-- there \\| is a LITERAL pipe, the mirror-image bug"
echo
echo "  -- of the BRE sites, which carry a NON-TERMINAL anchor (BROKEN TODAY)? --"
BROKEN=0
while IFS= read -r line; do
  # a non-terminal $ : a '$' that is followed by more pattern before the closing quote
  if printf '%s' "$line" | $GREP -qE '\$\\\|'; then
    BROKEN=$((BROKEN+1)); echo "    BROKEN  $line"
  fi
done < "$CA"
echo "  BROKEN-TODAY sites: $BROKEN"
echo
echo "  -- do any live in a graded path (conformance.sh or a guard)? --"
$GREP -E '^\.softhouse/(conformance\.sh|guards/)' "$CA" | sed 's/^/    LIVE  /' > "$CA.live" || true
echo "    live sites: $($GREP -c . "$CA.live" || true)"
[ -s "$CA.live" ] && cat "$CA.live"
echo
echo "############ 3. THE SED VARIANT, AND A LIVE DEAD EXPRESSION ############"
echo "  BSD sed is STRICTER than BSD grep: it does not implement \\| as alternation at all."
echo "  (\`.softhouse/guards/check-capture-namespace.sh:95\` already says so in a comment; nothing"
echo "  enforces it.) So a sed BRE using \\| matches a LITERAL PIPE and therefore matches nothing."
echo
printf '  alternation in BSD sed  : %s rows  (2 if it works, 0 if \\| is literal)\n' \
  "$(printf 'a\nb\n' | LC_ALL=C /usr/bin/sed -n 's/^\(a\|b\)$/HIT/p' | $GREP -c . || true)"
printf '  literal-pipe check      : %s  <-- it matched the literal string a|b\n' \
  "$(printf 'a|b\n' | LC_ALL=C /usr/bin/sed -n 's/^\(a|b\)$/LITERAL/p')"
echo
echo "  -- every LIVE (conformance.sh or guards/) sed BRE using \\| --"
$GREP -nE "sed[^|]*\\\\\|" .softhouse/conformance.sh .softhouse/guards/*.sh 2>/dev/null \
  | $GREP -vE ':[0-9]+:[[:space:]]*#' | sed 's/^/    /' > "$CA.sed" || true
if [ -s "$CA.sed" ]; then cat "$CA.sed"; else echo "    (none)"; fi
echo
echo "  -- exercised against the shape of output it is meant to summarise --"
printf '  ledger parity  PASS 46  FAIL 0\n  ledger oracle-refusal  PASS 3  FAIL 0\n  ledger harness errors 0\n  unrelated\n' > "$CA.fix"
printf '    rows the expression prints: %s   (it is meant to print 3)\n' \
  "$(LC_ALL=C /usr/bin/sed -n 's/^\( *ledger \(parity\|oracle-refusal\|inadmissible\|harness errors\).*\)$/\1/p' "$CA.fix" | $GREP -c . || true)"
echo "    SEVERITY: this sits in the SURVIVED branch of the wrong-implementation gate, AFTER"
echo "    bad=1 is already set. It gates nothing; it is the diagnostic that tells an operator"
echo "    WHY a wrong implementation survived, and it has never once produced a line. Losing"
echo "    evidence on a failing path is MINOR, not a fail-open -- but it is dead code that"
echo "    only a red run would ever have revealed, which is why five years of green never did."
echo
echo "  -- the sibling expressions that ARE load-bearing use no \\| and are CORRECT --"
echo "     (found by GREPPING THE SENTENCE, not by line number -- P-86; a line number in a"
echo "      file another task is editing is stale before it is read)"
$GREP -n 'pfail="$(LC_ALL=C sed\|rfail="$(LC_ALL=C sed' .softhouse/conformance.sh | cut -c1-150 | sed 's/^/    /'
echo
echo "  -- all BRE \\| sites, for the record --"
sed 's/^/    /' "$CA"
