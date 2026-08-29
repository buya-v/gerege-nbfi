#!/usr/bin/env bash
# T440 point 5: INDEPENDENT re-adjudication of K8 on casualty-sweep.sh.
# I do not use T424's K8 regex. I enumerate every call of a state-mutating function and every
# SWEEP_* assignment, then ask of each one whether it executes in a SUBSHELL.
set -uo pipefail
REPO=$1; REF=$2
W=$(mktemp -d "${TMPDIR:-/tmp}/t440k8.XXXXXX"); trap 'rm -rf "$W"' EXIT
git -C "$REPO" show "$REF:.softhouse/capture/t363-oracle-baseline/instruments/casualty-sweep.sh" > "$W/f.sh" || exit 2
echo "ref=$REF  sha256=$(shasum -a 256 < "$W/f.sh" | cut -d' ' -f1)"
echo

# executable lines only
awk '{t=$0; sub(/^[[:space:]]+/,"",t); if (t ~ /^#/ || t=="") next; printf "%d\t%s\n", NR, $0}' \
  "$W/f.sh" > "$W/x.txt"
echo "executable lines: $(grep -c . "$W/x.txt")"
echo

for fn in sel calibrate _calib_refuse engine_count; do
  # CALL sites: the name followed by whitespace, not a definition line
  awk -F'\t' -v fn="$fn" '$2 ~ ("(^|[^A-Za-z_0-9])" fn "([[:space:]]|$)") && $2 !~ (fn "[[:space:]]*\\(\\)") {printf "%d\t%s\n",$1,$2}' \
    "$W/x.txt" > "$W/calls-$fn.txt"
  n=$(grep -c . "$W/calls-$fn.txt")
  echo "=== calls to $fn(): $n"
  # For each call, decide subshell context from the text BEFORE the call on that line.
  bad=0
  while IFS=$'\t' read -r ln txt; do
    [ -n "${ln:-}" ] || continue
    pre=${txt%%$fn*}
    verdict=BARE
    pre_nb=$(printf '%s' "$pre" | sed 's/||/@@/g')
    case "$pre_nb" in
      *'$('*|*'`'*)                        verdict='IN A COMMAND SUBSTITUTION' ;;
      *'|'*)                               verdict='DOWNSTREAM OF A PIPE' ;;
    esac
    # trailing: piped into something, or backgrounded
    post=${txt#*$fn}
    # strip quoted spans so a | inside the ERE argument is not mistaken for an operator
    stripped=$(printf '%s' "$post" | awk '{o="";q=0;qc="";for(i=1;i<=length($0);i++){c=substr($0,i,1);
      if(q){ if(c==qc){q=0}; o=o" "; continue }
      if(c=="\047"||c=="\""){q=1;qc=c;o=o" ";continue} o=o c} print o}')
    case "$stripped" in
      *'|'*) case "$stripped" in *'||'*) : ;; *) verdict="$verdict + PIPED INTO SOMETHING" ;; esac ;;
    esac
    case "$stripped" in *'&') verdict="$verdict + BACKGROUNDED" ;; esac
    if [ "$verdict" != BARE ]; then
      bad=$((bad+1)); printf '   *** %5s  %-28s %s\n' "$ln" "$verdict" "$(printf '%s' "$txt" | cut -c1-90)"
    fi
  done < "$W/calls-$fn.txt"
  printf '    -> non-bare call sites: %s\n' "$bad"
done
echo

echo "=== SWEEP_* assignments, and where the ASSIGNMENT itself happens"
awk -F'\t' '$2 ~ /(^|[^A-Za-z_0-9])SWEEP_[A-Z_]*=/ {printf "%d\t%s\n",$1,$2}' "$W/x.txt" > "$W/assign.txt"
tot=$(grep -c . "$W/assign.txt")
echo "  total lines carrying a SWEEP_* assignment: $tot"
inner=0
while IFS=$'\t' read -r ln txt; do
  [ -n "${ln:-}" ] || continue
  pre=${txt%%SWEEP_*}
  case "$pre" in
    *'$('*|*'`'*|*'|'*) inner=$((inner+1)); printf '   *** %5s ASSIGNMENT INSIDE A CHILD: %s\n' "$ln" "$(printf '%s' "$txt"|cut -c1-90)" ;;
  esac
done < "$W/assign.txt"
printf '  assignments that execute in a CHILD (real STATE-LOSS): %s\n' "$inner"
echo
echo "=== function bodies: is any state-mutating function invoked from inside \$( ) anywhere?"
grep -nE '\$\([^)]*\b(sel|calibrate|_calib_refuse|engine_count)\b' "$W/f.sh" | grep -v '^[0-9]*: *#' || echo "  none"
echo
echo "T440-K8-ADJUDICATION: state-loss sites found = 0 unless a *** line appears above"
