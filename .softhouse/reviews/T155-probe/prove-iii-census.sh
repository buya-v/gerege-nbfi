#!/bin/bash
# T155 probe (iii) — INDEPENDENT. Eight ways to get a `.json` under the vector
# store root that the harness never loads, and therefore never checks.
#
# DESIGN CHOICE THAT MAKES THIS AN HONEST TEST OF THE CENSUS: wherever possible
# the planted file contains NO float at all. `conformance.sh` runs `run_guards`
# (the shell no-float grep) BEFORE the binary, so a refusal on a float-carrying
# fixture could be the shell guard's and would say nothing about the census.
# A clean fixture can only be refused by StoreFileCensus / CaseIDIntegrity.
#
# NO COUNT IS HARD-CODED (P-24). The control arm MEASURES the baseline on each
# tree and every other row is stated relative to it. `main` moved from 42 to 43
# parity vectors after T154's fork point and a literal would be wrong on merge.
#
#   PRE  = fork point 187e972 (the inherited holes)
#   POST = SCRATCH MERGE of softhouse/T154-nofloat-guards into CURRENT main
set -u
PRE=/tmp/t155/pre
POST=/tmp/t155/post
OUTD=/tmp/t155/out
EVIL=/tmp/t155/evil
mkdir -p "$OUTD"
. /Users/buv/gerege-nbfi/.softhouse/bin/go-env.sh

# ---------------------------------------------------------------------------
# T155's own poison fixtures
# ---------------------------------------------------------------------------
rm -rf "$EVIL"; mkdir -p "$EVIL/evilctx"
# a float-carrying "vector" for the symlinked-context rows
printf '{\n  "schema": "gerege.loanschedule.vector/v1",\n  "case_id": "T155-EVIL",\n  "context": "evilctx",\n  "class": "parity",\n  "rate_pct": 3.6\n}\n' > "$EVIL/evilctx/T155-EVIL.json"

SRC=""   # a real committed vector, resolved per tree
mkvariant() { # $1 tree, $2 dest path, $3 new case_id
  local tree="$1" dest="$2" cid="$3"
  mkdir -p "$(dirname "$dest")"
  sed "s/\"case_id\": \"P-00\"/\"case_id\": \"$cid\"/" \
      "$tree/.softhouse/vectors/loanschedule/P-00-baseline-6x7pct.json" > "$dest"
  LC_ALL=C grep -aq "\"case_id\": \"$cid\"" "$dest" || { echo "REFUSE: case_id rewrite failed for $cid"; exit 9; }
}

# ---------------------------------------------------------------------------
# runner
# ---------------------------------------------------------------------------
run() { # $1 tree, $2 label -> prints "exit:parity:cells" and stashes output
  local tree="$1" label="$2" rc out parity cells
  out="$OUTD/iii-$label.txt"
  ( cd "$tree" && bash "$tree/.softhouse/conformance.sh" ) > "$out" 2>&1
  rc=$?
  parity="$(LC_ALL=C grep -aE '^ +parity vectors +PASS' "$out" | head -1 | awk '{print $4}')"
  cells="$(LC_ALL=C grep -aE '^ +cells compared' "$out" | head -1 | awk '{print $3}')"
  echo "$rc:${parity:-NA}:${cells:-NA}"
}
why() { # $1 label — one line saying WHO refused
  local out="$OUTD/iii-$1.txt"
  LC_ALL=C grep -aE 'STORE FILE CENSUS|CASE_ID INTEGRITY|FLOAT-SHAPED NUMBER|FLOATING-POINT IDENTIFIER|FLOATING POINT ON A MONEY PATH|could not be loaded|refus' "$out" \
    | head -1 | sed 's/^ *//' | cut -c1-150
}

FAILS=0
row() { # 1 label 2 pre 3 post 4 want_pre_rel 5 want_post_exit 6 note
  printf '%-34s %-16s %-16s %s\n' "$1" "$2" "$3" "$6"
}

echo "grep this script gets: $(command -v grep)"
echo

for ARM in PRE POST; do
  tree=$PRE; [ "$ARM" = POST ] && tree=$POST
  echo "======================================================================"
  echo "ARM $ARM   tree=$tree"
  echo "======================================================================"

  base="$(run "$tree" "$ARM-control")"
  BASE_EXIT="${base%%:*}"; rest="${base#*:}"; BASE_P="${rest%%:*}"; BASE_C="${rest##*:}"
  echo "CONTROL (unmutated): exit=$BASE_EXIT parity=$BASE_P cells=$BASE_C   [MEASURED, never assumed]"
  if [ "$BASE_EXIT" != 0 ]; then echo "REFUSE: control arm is not exit 0 on $tree"; exit 9; fi
  echo
  printf '%-34s %-24s %s\n' CASE 'exit:parity:cells' 'who refused / meaning'
  printf '%-34s %-24s %s\n' ---- ------------------- ---------------------

  V="$tree/.softhouse/vectors"

  # --- C1 symlinked EXTRA context directory, holding a float ---------------
  ln -s "$EVIL/evilctx" "$V/evilctx"
  r="$(run "$tree" "$ARM-C1")"; printf '%-34s %-24s %s\n' "C1 symlinked EXTRA context" "$r" "$(why "$ARM-C1")"
  rm -f "$V/evilctx"

  # --- C2 the WHOLE real context reached through a symlink -----------------
  mv "$V/loanschedule" "$EVIL/loanschedule-real"
  ln -s "$EVIL/loanschedule-real" "$V/loanschedule"
  r="$(run "$tree" "$ARM-C2")"; printf '%-34s %-24s %s\n' "C2 symlinked WHOLE context" "$r" "$(why "$ARM-C2")"
  rm -f "$V/loanschedule"; mv "$EVIL/loanschedule-real" "$V/loanschedule"

  # --- C3 a NESTED subdirectory, clean vector (no float anywhere) ----------
  mkvariant "$tree" "$V/loanschedule/sub/T155-NESTED.json" "T155-NESTED"
  r="$(run "$tree" "$ARM-C3")"; printf '%-34s %-24s %s\n' "C3 nested subdir, CLEAN vector" "$r" "$(why "$ARM-C3")"
  rm -rf "$V/loanschedule/sub"

  # --- C4 UPPER.JSON, clean vector -----------------------------------------
  mkvariant "$tree" "$V/loanschedule/T155-UPPER.JSON" "T155-UPPER"
  r="$(run "$tree" "$ARM-C4")"; printf '%-34s %-24s %s\n' "C4 UPPER.JSON, CLEAN vector" "$r" "$(why "$ARM-C4")"
  rm -f "$V/loanschedule/T155-UPPER.JSON"

  # --- C5 case-only case_id variant ----------------------------------------
  mkvariant "$tree" "$V/loanschedule/T155-case-clash.json" "p-00"
  r="$(run "$tree" "$ARM-C5")"; printf '%-34s %-24s %s\n' "C5 case-only case_id (P-00/p-00)" "$r" "$(why "$ARM-C5")"
  rm -f "$V/loanschedule/T155-case-clash.json"

  # --- C6 NFC / NFD spellings of one case_id -------------------------------
  mkvariant "$tree" "$V/loanschedule/T155-nfc.json" "$(printf 'T155-caf\xc3\xa9')"
  mkvariant "$tree" "$V/loanschedule/T155-nfd.json" "$(printf 'T155-cafe\xcc\x81')"
  r="$(run "$tree" "$ARM-C6")"; printf '%-34s %-24s %s\n' "C6 NFC + NFD spellings of one id" "$r" "$(why "$ARM-C6")"
  rm -f "$V/loanschedule/T155-nfc.json" "$V/loanschedule/T155-nfd.json"

  # --- C7 store-root .json, NO float at all --------------------------------
  printf '{ "note": "planted at the store root", "amount": "1250000" }\n' > "$V/T155-ROOT-CLEAN.json"
  r="$(run "$tree" "$ARM-C7")"; printf '%-34s %-24s %s\n' "C7 store-root .json, NO float" "$r" "$(why "$ARM-C7")"
  rm -f "$V/T155-ROOT-CLEAN.json"

  # --- C8 store-root .json, float behind ONE invalid byte ------------------
  printf '{\n  "note": "x", \xe2 "rate_pct": 3.6\n}\n' > "$V/T155-ROOT-POISON.json"
  r="$(run "$tree" "$ARM-C8")"; printf '%-34s %-24s %s\n' "C8 store-root, float behind 0xE2" "$r" "$(why "$ARM-C8")"
  rm -f "$V/T155-ROOT-POISON.json"

  # --- C9 store-root .json, PLAIN float (control: shell guard sees this) ---
  printf '{\n  "rate_pct": 3.6\n}\n' > "$V/T155-ROOT-PLAINFLOAT.json"
  r="$(run "$tree" "$ARM-C9")"; printf '%-34s %-24s %s\n' "C9 store-root, PLAIN float" "$r" "$(why "$ARM-C9")"
  rm -f "$V/T155-ROOT-PLAINFLOAT.json"

  echo
  echo "$ARM store left clean? git-independent check:"
  find "$V" -name '*T155*' -o -name '*.JSON' -o -type l | sed 's/^/  LEFTOVER /'
  echo
done
