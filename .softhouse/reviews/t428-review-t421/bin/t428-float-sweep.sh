#!/bin/bash
# T428 -- float sweep of T421's ENTIRE diff, with a WIDER regex than T421 used.
#
# T421 swept for: float64|float32|big.Float|ParseFloat|FormatFloat|%f|Double|math.Round
# This adds:      %g %e %E, strconv.Atof, json.Number, decimal, float( , /  division
#                 on money-shaped names, complex64/128, math/big Float, "e" exponent
#                 literals, and any bare decimal literal on an ADDED line.
# Nothing here decodes a number: this is grep over diff text.
set -u
repo="$1"; base="$2"; head="$3"; out="$4"
cd "$repo" || exit 9
{
  echo "T428 FLOAT SWEEP -- $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo "range: $base...$head"
  echo -n "added lines in the diff: "
} > "$out"
git diff "$base...$head" > /tmp/t428-full.diff
LC_ALL=C grep -c '^+' /tmp/t428-full.diff >> "$out"
LC_ALL=C grep '^+' /tmp/t428-full.diff | LC_ALL=C sed 's/^+//' > /tmp/t428-added.txt

emit() {
  label="$1"; pat="$2"
  n=$(LC_ALL=C grep -cE "$pat" /tmp/t428-added.txt || true)
  echo "" >> "$out"
  echo "### $label   HITS=$n" >> "$out"
  echo "    pattern: $pat" >> "$out"
  LC_ALL=C grep -nE "$pat" /tmp/t428-added.txt | LC_ALL=C sed 's/^/    /' | head -60 >> "$out"
}

emit "T421's own regex"           'float64|float32|big\.Float|ParseFloat|FormatFloat|%f|Double|math\.Round'
emit "WIDER: float verbs"         '%[0-9.+#-]*[eEgG][^a-zA-Z]|%\.[0-9]+f'
emit "WIDER: float constructors"  '\bfloat\(|\bAtof\b|json\.Number|strconv\.Parse|decimal\.|new\(big\.Float\)|complex(64|128)?\b'
emit "WIDER: any 'float' token"   '[Ff][Ll][Oo][Aa][Tt]'
emit "WIDER: division operator"   '[^/*][/][^/*=]'
emit "WIDER: decimal literal"     '[^A-Za-z0-9_.]-?[0-9]+\.[0-9]+([eE][-+]?[0-9]+)?'
emit "WIDER: exponent literal"    '[^A-Za-z0-9_][0-9]+[eE][-+]?[0-9]+'

{
  echo
  echo "### ADDED GO LINES ONLY (the population that can execute), non-comment"
} >> "$out"
LC_ALL=C awk '/^\+\+\+ b\// {f=substr($0,7)} /^\+[^+]/ {if (f ~ /\.go$/) print f ": " substr($0,2)}' /tmp/t428-full.diff \
  | LC_ALL=C grep -vE ':[[:space:]]*(//|\*|/\*)' > /tmp/t428-go-added.txt
{
  echo -n "    added non-comment Go lines: "; LC_ALL=C grep -c '' /tmp/t428-go-added.txt
  echo "    float-shaped hits among them:"
} >> "$out"
LC_ALL=C grep -nE 'float|Float|Atof|%[0-9.]*[fgeEG]|[^A-Za-z0-9_.][0-9]+\.[0-9]+' /tmp/t428-go-added.txt \
  | LC_ALL=C sed 's/^/       /' >> "$out"
echo "    (no line above means NONE)" >> "$out"
tail -40 "$out"
