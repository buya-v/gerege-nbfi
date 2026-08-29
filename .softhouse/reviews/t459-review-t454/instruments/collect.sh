#!/bin/bash
# T459 -- rebuild the per-arm evidence transcripts from the bar logs each arm left behind.
set -u
OUT="$1"
SH=".soft""house"; CONF="$SH/conformance"".sh"
row() { # $1 arm dir, $2 arm label, $3 base, $4 outfile
  local d="$1"; local a="$2"; local base="$3"; local f="$4"
  local log="$d/bar.log"
  if [ ! -s "$log" ]; then echo "INSTRUMENT FAILURE: no bar log for $a" >&2; return 3; fi
  local rc n v
  n="$( LC_ALL=C grep -c 'probe = ' "$log" )"
  v="-"; if [ "$n" -gt 0 ]; then v="$( LC_ALL=C grep -m1 'probe = ' "$log" | sed 's/.*probe = //' )"; fi
  {
    printf 'T459 arm %s, base %s\n' "$a" "$base"
    printf 'host: macOS 26.5.1 (25F80), APFS case- and fold-INSENSITIVE, git 2.50.1 (Apple Git-155),\n'
    printf '      GNU bash 3.2.57(1); core.ignorecase=true core.precomposeunicode=true\n'
    printf 'cwd for the run: a scratch directory OUTSIDE every repository involved\n'
    printf -- '---------------------------------------------------------------------------\n'
    printf 'probe line COUNT (read BEFORE its value, P-84) : %s\n' "$n"
    printf 'probe value                                    : %s\n' "$v"
    printf 'VERDICT line                                   : %s\n' \
      "$( LC_ALL=C grep -m1 '^VERDICT' "$log" || printf '<absent>' )"
    printf 'guards-dir census                              : %s\n' \
      "$( LC_ALL=C grep -m1 'GUARDS-DIR-REGISTRATION: population' "$log" | sed 's/.*population/population/' )"
    printf -- '--- every REFUSED / FAILED line in the log --------------------------------\n'
    LC_ALL=C grep -n 'FAILED:\|REFUSED$\|THE DECISIVE LINE\|substituted path' "$log" | head -25
    printf -- '--- the HARNESS-TEXT census, verbatim -------------------------------------\n'
    LC_ALL=C grep -n 'HARNESS-TEXT\|this harness .*committed .* on disk' "$log" | head -12
    printf -- '--- guard-cost census ------------------------------------------------------\n'
    LC_ALL=C grep -n 'GUARD-COST CENSUS\|guard-cost:' "$log" | head -8
  } > "$f"
  printf '  wrote %s\n' "$f"
}
row /tmp/t459/arms/Z-cbc8733c Z cbc8733c "$OUT/10-RED-main-Z-control.txt"
row /tmp/t459/arms/CTL-cbc8733c CTL cbc8733c "$OUT/11-RED-main-CTL.txt"
row /tmp/t459/arms/LONGS-cbc8733c LONGS cbc8733c "$OUT/12-RED-main-LONGS-failopen.txt"
row /tmp/t459/arms/RWB3-CTL-cbc8733c RWB3CTL cbc8733c "$OUT/13-RED-main-RWB3CTL.txt"
row /tmp/t459/arms/RWB3-MUT-cbc8733c RWB3    cbc8733c "$OUT/14-RED-main-RWB3-failopen.txt"
row /tmp/t459/arms/LONGSTRIP1-02fb1af4   LONGSTRIP1   02fb1af4 "$OUT/22-GREEN-tip-LONGSTRIP1-refuses.txt"
row /tmp/t459/arms/LONGSTRIP-02fb1af4    LONGSTRIP    02fb1af4 "$OUT/23-OPEN-tip-LONGSTRIP-seventh-route.txt"
row /tmp/t459/arms/LONGNOP-02fb1af4      LONGNOP      02fb1af4 "$OUT/24-OPEN-tip-LONGNOP-EIGHTH-one-line.txt"
row /tmp/t459/arms/SYMFORGE-02fb1af4     SYMFORGE     02fb1af4 "$OUT/25-CLOSED-tip-SYMFORGE-refuted.txt"
row /tmp/t459/arms/SKIPWT-skip-worktree-02fb1af4    SKIPWT     02fb1af4 "$OUT/26-OPEN-tip-SKIPWT.txt"
row /tmp/t459/arms/SKIPWT-assume-unchanged-02fb1af4 SKIPWT-AU  02fb1af4 "$OUT/27-OPEN-tip-SKIPWT-assume-unchanged.txt"
row /tmp/t459/arms/SMUDGE-02fb1af4       SMUDGE       02fb1af4 "$OUT/28-OPEN-tip-SMUDGE.txt"
row /tmp/t459/arms/Z-02fb1af4 Z-tip 02fb1af4 "$OUT/20-GREEN-tip-Z-control.txt"
row /tmp/t459/arms/LONGS-02fb1af4 LONGS-tip 02fb1af4 "$OUT/21-GREEN-tip-LONGS-refuses.txt"
