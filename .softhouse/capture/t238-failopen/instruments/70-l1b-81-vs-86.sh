#!/bin/bash
# T238 -- CLOSE T234's L-1b: A2-33's two calibration transcripts report 81 unique rev-4 lines
# under `git grep` and 86 under ugrep. A measured 5-line engine divergence, committed, unexplained.
# T234 flagged it [UNVERIFIED] and did not chase it. This chases it.
#
# METHOD. rev 4 of the ADR is recoverable: A2-28 wrote it at 1b6b3cf and A2-32 replaced it with
# rev 5 at cab9e82. So `git show 1b6b3cf:docs/adr/DEC-2-gl-accounting-adapter.md` IS the exact
# corpus both calibrations measured. Re-run A2-33's 34 patterns against it and count unique
# matching line numbers, under every engine this machine actually has.
#
# READ-ONLY on docs/adr/ -- DEC-2 rev 5 is RATIFIED and amending it is a `user` gate. This
# script only READS a historical blob into /tmp. Nothing under docs/adr/ is written.
set -u
ROOT=$(git rev-parse --show-toplevel) || exit 90
cd "$ROOT" || exit 90
SWEEP=.softhouse/reviews/a2-33-dec2-rev5/sweep.sh
REV4_COMMIT=1b6b3cf
ADR=docs/adr/DEC-2-gl-accounting-adapter.md
T=$(mktemp -d /tmp/t238-l1b-XXXXXX)
trap 'rm -rf "$T"' EXIT

echo "T238 -- L-1b: THE 81 vs 86 DIVERGENCE"
echo "commit        : $(git rev-parse HEAD)"
echo

echo "=== 0. IS THE REV-4 CORPUS RECOVERABLE? ==="
if git cat-file -e "$REV4_COMMIT:$ADR" 2>/dev/null; then
  git show "$REV4_COMMIT:$ADR" > "$T/rev4.md"
  echo "  YES. $REV4_COMMIT:$ADR -> $(wc -l < "$T/rev4.md" | tr -d ' ') lines, sha256:"
  shasum -a 256 "$T/rev4.md" | sed 's/^/    /'
else
  echo "  NO -- cannot recover rev 4. L-1b is unresolvable from committed artefacts."; exit 91
fi
echo

echo "=== 1. VERIFY A2-33'S OWN AUDIT CLAIM: 'no \\b, \\d, \\s or \\w in ANY pattern' ==="
NPAT=$(grep -c '^run ' "$SWEEP")
BAD=$(grep '^run ' "$SWEEP" | grep -c -E '\\[bBdDsSwW]' || true)
echo "  patterns declared           : $NPAT"
echo "  patterns using \\b \\d \\s \\w  : $BAD"
if [ "$BAD" -eq 0 ]; then
  echo "  >>> A2-33's audit claim VERIFIED at this commit. The ERE-vs-PCRE escape defect"
  echo "  >>> (P-53 / P-12) CANNOT be the cause of the divergence. That was T234's implicit"
  echo "  >>> hypothesis and it is now excluded by measurement."
else
  echo "  >>> A2-33's audit claim is FALSE; the escape defect is a live candidate cause."
fi
echo

echo "=== 2. RE-MEASURE: unique rev-4 lines hit by all $NPAT patterns, per engine ==="
echo "    (A2-33 reported: git grep = 81, ugrep = 86)"
grep '^run ' "$SWEEP" | sed -E "s/^run +[A-Z0-9-]+ +'(.*)'$/\1/" > "$T/patterns.txt"
echo "  patterns extracted for replay: $(wc -l < "$T/patterns.txt" | tr -d ' ')"
echo

measure() { # measure <label> <engine-fn>
  local label fn slug out n err rc uniq
  label="$1"
  fn="$2"
  slug=$(printf '%s' "$label" | tr -c 'A-Za-z0-9' '_')
  out="$T/hits-$slug.txt"
  : > "$out"
  n=0; err=0
  while IFS= read -r re; do
    [ -n "$re" ] || continue
    n=$((n+1))
    if ! "$fn" "$re" >> "$out" 2>/dev/null; then
      rc=$?
      [ "$rc" -gt 1 ] && err=$((err+1))
    fi
  done < "$T/patterns.txt"
  uniq=$(sort -u -n "$out" | grep -c . || true)
  printf '  %-28s patterns=%-3s engine_errors=%-3s UNIQUE LINES = %s\n' "$label" "$n" "$err" "$uniq"
}

eng_bsd_ere()  { /usr/bin/grep -n -i -E "$1" "$T/rev4.md" | cut -d: -f1; }
eng_bsd_ere_nocase_off() { /usr/bin/grep -n -E "$1" "$T/rev4.md" | cut -d: -f1; }
eng_perl_pcre(){ perl -ne 'BEGIN{$p=shift} print "$.\n" if /$p/i' "$1" "$T/rev4.md"; }
eng_perl_cs()  { perl -ne 'BEGIN{$p=shift} print "$.\n" if /$p/'  "$1" "$T/rev4.md"; }

measure "BSD grep -n -i -E"        eng_bsd_ere
measure "BSD grep -n -E (no -i)"   eng_bsd_ere_nocase_off
measure "perl PCRE //i"            eng_perl_pcre
measure "perl PCRE // (no i)"      eng_perl_cs
echo
echo "  ugrep                      UNMEASURABLE -- ugrep is ABSENT from this machine."
echo "                             (transcripts/00-engines.txt: not on PATH, not in /opt/homebrew,"
echo "                              not in /usr/local. A2-33's ugrep leg cannot be re-run here.)"
echo

echo "=== 3. WHAT THE COMMITTED ARTEFACTS DO AND DO NOT RECORD ==="
echo "  sweep-recall-calibration-gitgrep.txt declares:"
echo "     engine  : git version 2.50.1 (Apple Git-155)      [DECLARED]"
echo "     flags   : git grep -n -I -i -E                    [DECLARED]"
echo "  sweep-recall-calibration-ugrep.txt declares:"
echo "     engine  : (nothing -- no version string anywhere in the file)   [NOT DECLARED]"
echo "     flags   : (nothing)                                            [NOT DECLARED]"
echo "  Instrument that computed either number:"
git grep -l 'unique rev4 lines' -- . | sed 's/^/     /'
echo "     ^^ these are the two TRANSCRIPTS and T234's census index. NO SCRIPT computes it."
echo
echo "=== 4. VERDICT ==="
echo "  See the handoff. In one line: the git-grep leg is re-derivable and the ugrep leg is not,"
echo "  because the ugrep transcript records neither its engine version nor its flags nor its"
echo "  command -- which is P-72 corollary 2 exactly: a sweep whose commands were not committed"
echo "  cannot be audited, only believed."
