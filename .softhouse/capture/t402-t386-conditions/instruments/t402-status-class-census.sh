#!/usr/bin/env bash
# T402 -- THE STATUS-LOSS CLASS CENSUS.
#
#   bash .softhouse/capture/t402-t386-conditions/instruments/t402-status-class-census.sh \
#        <repo-root> <ref> [path]
#
# WHY THIS EXISTS, AND IT IS THE WHOLE LESSON OF C-1
# --------------------------------------------------
# T381's `AUDIT.md` promised to classify "every `2>/dev/null` and every pipeline in the file".
# It delivered exactly that, and its counts were internally correct. But the DEFECT CLASS is
# every construct where an exit status can be LOST, and `err=$(cat "$SWEEP_ERRF")` is neither a
# `2>/dev/null` nor a pipeline. It had no row -- and it was carrying the defect.
#
#   A TAXONOMY NARROWER THAN THE DEFECT CLASS CERTIFIES ONLY THE PART OF THE FILE THE TAXONOMY
#   COULD SEE.
#
# So this census does not enumerate two syntactic forms. It enumerates SEVEN, chosen to cover
# the class rather than the last two defects, and it PRINTS EVERY SITE WITH ITS LINE TEXT so a
# reader adjudicates from the list instead of from prose -- and so a citation can be made BY
# CONTENT rather than by line number (P-86: 14 of T381's 16 audited line numbers had moved by
# the time T386 checked them).
#
#   K1  COMMAND SUBSTITUTION       $(...)  -- the form that carried C-1
#   K2  PIPELINE                   a | b   -- the form T381 did enumerate
#   K3  OUTPUT REDIRECTION         > >> 2> -- OPENED BY THE SHELL BEFORE THE COMMAND RUNS, so a
#                                  failure here returns 1 WITHOUT RUNNING ANYTHING
#   K4  COMMAND-AS-CONDITION       if/while/until <cmd> -- collapses "false" and "errored"
#   K5  ASSIGNMENT-MASKED STATUS   local/declare/export/readonly x=$(...) -- the BUILTIN's
#                                  status is returned, the substitution's is destroyed
#   K6  SUBSTITUTION IN AN ARGUMENT  printf/echo "$(...)" -- structurally unreadable: there is
#                                  no $? to consult, the empty string is the only symptom
#   K7  ARITHMETIC / NUMERIC TEST ON UNVALIDATED INPUT  $(( )) and [ x -gt n ] where x may be
#                                  empty or non-numeric
#
# ENGINE DECLARED (P-33/P-53): `grep -n -E` and `awk`, over ONE extracted file -- not over the
# repository. No backslash-class appears in any pattern below; POSIX classes are used instead,
# which is the same rule `casualty-sweep.sh` enforces on its own selectors.
#
# THIS CENSUS IS A LIST, NOT A VERDICT. Membership of K1..K7 is not a defect; it is a place a
# status CAN be lost. The adjudication -- fail-open / fail-closed / provenance-only -- is in
# AUDIT-CLASS.md beside this file, keyed by line CONTENT.
#
# EXIT: 0 the census ran and printed its sites; 2 it could not reach the file it grades.
set -uo pipefail

REPO=${1:?usage: <repo-root> <ref> [path]}
REF=${2:?usage: <repo-root> <ref> [path]}
SRC=${3:-.softhouse/capture/t363-oracle-baseline/instruments/casualty-sweep.sh}

WORK=$(mktemp -d "${TMPDIR:-/tmp}/t402-census.XXXXXXXX") || exit 2
trap 'rm -rf "$WORK"' EXIT

git -C "$REPO" show "$REF:$SRC" > "$WORK/f.sh" || exit 2
TOTAL_LINES=$(grep -c '' "$WORK/f.sh") || exit 2

echo "T402 STATUS-LOSS CLASS CENSUS"
echo "  ref     : $REF"
echo "  file    : $SRC"
echo "  sha256  : $(shasum -a 256 < "$WORK/f.sh" | cut -d' ' -f1)"
echo "  lines   : $TOTAL_LINES"
echo

# EXECUTABLE LINES ONLY. A comment cannot lose a status; counting comments is how an audit
# inflates itself. The predicate is stated here so a reader can disagree with one regex:
# a line whose first non-blank character is '#' is comment, everything else is executable.
awk '{ ln=NR; s=$0; t=s; sub(/^[[:space:]]+/,"",t);
       if (t ~ /^#/ || t == "") next;
       printf "%d\t%s\n", ln, s }' "$WORK/f.sh" > "$WORK/exec.txt"
EXEC_LINES=$(grep -c '' "$WORK/exec.txt")
echo "  executable (non-blank, non-comment) lines: $EXEC_LINES"
echo

emit() { # emit <kind> <label> <ERE over the executable-line text>
  local kind="$1" label="$2" pat="$3" n
  echo "--- $kind  $label"
  # field 1 is the ORIGINAL line number; match only against field 2 onwards.
  awk -F'\t' -v pat="$pat" '$2 ~ pat { printf "    %4d | %s\n", $1, substr($2,1,150) }' \
    "$WORK/exec.txt" > "$WORK/k.txt"
  n=$(grep -c '' "$WORK/k.txt")
  cat "$WORK/k.txt"
  printf '    == %s SITES: %s\n\n' "$kind" "$n"
  printf '%s %s\n' "$kind" "$n" >> "$WORK/counts.txt"
}

: > "$WORK/counts.txt"

emit K1 'COMMAND SUBSTITUTION  $(...)' '[$][(]'
emit K2 'PIPELINE  a | b (|| excluded)' '[^|][|][^|]'
emit K3 'OUTPUT REDIRECTION  > >> 2>  (opened by the SHELL, before the command runs)' '(^|[^0-9<>])[12]?>'
emit K4 'COMMAND-AS-CONDITION  if/while/until <cmd>' '^[[:space:]]*(if|while|until)[[:space:]]+[^[]'
emit K5 'ASSIGNMENT-MASKED STATUS  local/declare/export/readonly x=$(...)' '^[[:space:]]*(local|declare|export|readonly)[[:space:]]+[A-Za-z_][A-Za-z_0-9]*=[$][(]'
emit K6 'SUBSTITUTION IN AN ARGUMENT  printf/echo ... "$(...)"' '^[[:space:]]*(printf|echo)[[:space:]].*[$][(]'
emit K7 'ARITHMETIC / NUMERIC TEST  $(( )) or [ x -gt n ]' '[$][(][(]|-(eq|ne|lt|le|gt|ge)[[:space:]]'

# ---------------------------------------------------------------------------------------
# A CONVENIENCE VIEW, AND IT IS NOT THE CENSUS.
#
# K2 and K3 above match `|` and `>` wherever they appear -- including inside the SELECTORS'
# own quoted ERE patterns, which are not shell operators at all. That over-inclusion is
# DELIBERATE and it is the correct direction: the whole finding of C-1 is that a taxonomy
# narrowed to fit the last defect stops seeing the next one. The list above is authoritative
# and stays wide.
#
# What follows re-runs K2 and K3 over the SAME lines with single- and double-quoted spans
# blanked, so a reader can see the shell-operator subset without the census having been
# narrowed to produce it. If these two numbers and the two above ever get confused, the wide
# ones win.
echo '--- K2s / K3s  CONVENIENCE VIEW: quoted spans blanked (NOT the census) ---'
awk -F'\t' '{ n=$1; s=$2; out=""; q=0; qc="";
      for (i=1; i<=length(s); i++) { c=substr(s,i,1);
        if (q==0 && (c=="\047" || c=="\"")) { q=1; qc=c; out=out" "; }
        else if (q==1 && c==qc) { q=0; out=out" "; }
        else if (q==1) { out=out" "; }
        else out=out c; }
      printf "%d\t%s\n", n, out }' "$WORK/exec.txt" > "$WORK/stripped.txt"
K2S=$(awk -F'\t' '$2 ~ /[^|][|][^|]/' "$WORK/stripped.txt" | grep -c '')
K3S=$(awk -F'\t' '$2 ~ /(^|[^0-9<>])[12]?>/' "$WORK/stripped.txt" | grep -c '')
printf '    K2s pipelines in shell-operator position : %s\n' "$K2S"
printf '    K3s redirections in shell-operator position : %s\n\n' "$K3S"

echo '=== CENSUS TOTALS ========================================================='
sort "$WORK/counts.txt" | awk '{printf "  %-4s %s\n", $1, $2; t+=$2} END{printf "  ----\n  SITES (a line may belong to more than one kind): %d\n", t}'
echo
echo 'THE TWO KINDS T381 AUDITED WERE K2 AND (part of) K3. K1 -- the kind that carried C-1 --'
echo 'had no row in that taxonomy, and neither did K5, K6 or K7.'
echo 'CENSUS-RESULT: ref=' "$REF" ' exec_lines=' "$EXEC_LINES"
