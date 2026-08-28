#!/usr/bin/env bash
# T332 — the whole deliverable, RE-RUN. Not a transcribed table.
#
#   bash .softhouse/capture/t332-residual-twin-sweep/src/verify_t332.sh
#
# Exit 0 only when every POSITIVE passes AND every NEGATIVE trips. A guard that
# cannot fail proves nothing, so six mutations are applied and each must be caught.
#
# F-T278-2's remedy is implemented here rather than argued for: `mutate()` proves the
# mutant PARSES, not merely that the file changed. A mutation that produces a
# SyntaxError would otherwise be scored "tripped" for the wrong reason.
#
# bash, never sh/zsh/dash.
set -u
if [ -z "${BASH_VERSION:-}" ]; then echo "run me with bash"; exit 3; fi

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../.." && pwd)"
cd "$ROOT" || exit 3
SRC=.softhouse/capture/t332-residual-twin-sweep/src
EV=.softhouse/capture/t332-residual-twin-sweep/evidence
AUDIT="$SRC/t332_twin_audit.py"
SWEEP="$SRC/t332_sweep_gates.py"
GATES=.softhouse/gates.md
BASE="${T332_BASE:-main}"
mkdir -p "$EV"
FAILS=0

pass_case() {  # pass_case <name> <cmd...>
  local name="$1"; shift
  if "$@" >/dev/null 2>&1; then
    printf '  PASS-CASE  %-8s %s\n' ok "$name"
  else
    printf '  PASS-CASE  %-8s %s\n' 'FAILED' "$name"; FAILS=$((FAILS+1))
  fi
}

fail_case() {  # fail_case <name> <cmd...>   -- must exit non-zero
  local name="$1"; shift
  if "$@" >/dev/null 2>&1; then
    printf '  FAIL-CASE  %-8s DID NOT TRIP: %s\n' 'FAILED' "$name"; FAILS=$((FAILS+1))
  else
    printf '  FAIL-CASE  %-8s %s\n' 'tripped' "$name"
  fi
}

mutate() {  # mutate <src> <dst> <sed-expr>
  local src="$1" dst="$2" expr="$3"
  cp "$src" "$dst" || return 1
  perl -0pi -e "$expr" "$dst" || return 1
  if cmp -s "$src" "$dst"; then
    echo "ABORT: mutant $dst is byte-identical to $src -- the edit was a no-op." >&2
    return 1
  fi
  case "$dst" in
    *.py)
      python3 -c "import ast,sys;ast.parse(open(sys.argv[1]).read())" "$dst" || {
        echo "ABORT: mutant $dst does not PARSE -- a tripped negative would be meaningless." >&2
        return 1; }
      ;;
  esac
  return 0
}

echo "T332 VERIFY  (root $ROOT, base $BASE)"
echo
echo "POSITIVES — the measurement, re-run over the committed raw .json.gz"
pass_case "audit --selftest"                 python3 "$AUDIT" --selftest
pass_case "audit census t229corpus"          python3 "$AUDIT" --scope t229corpus
pass_case "audit census all"                 python3 "$AUDIT" --scope all
pass_case "audit --seven (full-tuple match)" python3 "$AUDIT" --seven
pass_case "audit --sites (per-site claims)"  python3 "$AUDIT" --sites
pass_case "sweep of $GATES"                  python3 "$SWEEP" --list

echo
echo "NEGATIVES — the guards, each shown to be capable of failing"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

# --- arithmetic guard ---------------------------------------------------------
if mutate "$AUDIT" "$TMP/m1.py" "s/'law_ii_fails': 7,\n        'law_ii_on_fact_a': 213/'law_ii_fails': 0,\n        'law_ii_on_fact_a': 220/"; then
  fail_case "M1 audit: law (ii) pinned 220/220 on FACT A (the rejected branch's claim)" \
            python3 "$TMP/m1.py" --scope t229corpus
else FAILS=$((FAILS+1)); echo "  M1 could not be built"; fi

if mutate "$AUDIT" "$TMP/m2.py" "s/2000, 999, 499, 500, 1, 0, 166, 999, 833/2000, 999, 499, 500, 1, 0, 165, 999, 833/"; then
  fail_case "M2 audit: 165 minor units expected where 166 is measured" \
            python3 "$TMP/m2.py" --seven
else FAILS=$((FAILS+1)); echo "  M2 could not be built"; fi

if mutate "$AUDIT" "$TMP/m3.py" "s/cell\.I1q = half_up\(B \* rnum, rden\)/cell.I1q = minor(rows[0]['interest'])/"; then
  fail_case "M3 audit: I1q READ FROM ROW 1 instead of computed (the FU-T277-4 trap)" \
            python3 "$TMP/m3.py" --scope t229corpus
else FAILS=$((FAILS+1)); echo "  M3 could not be built"; fi

# --- sweep guard --------------------------------------------------------------
cp "$GATES" "$TMP/g0.md"

cp "$TMP/g0.md" "$TMP/g1.md"
printf '\nThe residual of an unrescued family-B cell is `min(B_minor, n·δ)`.\n' >> "$TMP/g1.md"
cmp -s "$TMP/g0.md" "$TMP/g1.md" && { echo "  N1 no-op"; FAILS=$((FAILS+1)); }
fail_case "N1 sweep: a NEW unqualified restatement appended to gates.md" \
          python3 "$SWEEP" --file "$TMP/g1.md"

# N2 deletes the WHOLE scope note from the prescriptive site, not one phrase of it.
# The first draft of this negative removed only the "UPPER BOUND, NOT AN EQUALITY"
# phrase and DID NOT TRIP -- because the same note also cites `CORRECTION (T277)`,
# which is a scope mark in its own right, so the site stayed covered. The guard was
# right and the negative was weak; recorded here because a negative that trips for a
# reason you did not intend is the same defect as one that cannot trip at all.
if mutate "$TMP/g0.md" "$TMP/g2.md" "s/^> \*\*\[T332 — \`min\(B_minor, n·δ\)\` IS AN UPPER BOUND.*?seven sites and not one\.\]\*\*\n//sm"; then
  fail_case "N2 sweep: the ENTIRE scope note deleted from the PRESCRIPTIVE site" \
            python3 "$SWEEP" --file "$TMP/g2.md"
else FAILS=$((FAILS+1)); echo "  N2 could not be built"; fi

if mutate "$TMP/g0.md" "$TMP/g3.md" "s/^.*the term is only the cap; \*\*the principals asked are what the figure is.*\n//m"; then
  fail_case "N3 sweep: a ledgered site DELETED (the prose-only seventh site)" \
            python3 "$SWEEP" --file "$TMP/g3.md"
else FAILS=$((FAILS+1)); echo "  N3 could not be built"; fi

if mutate "$TMP/g0.md" "$TMP/g4.md" "s/#### T332 — THE SAME CLAIM, SWEPT/#### T332 — notes/"; then
  fail_case "N4 sweep: the T332 correction heading renamed (its own lines go unclassified)" \
            python3 "$SWEEP" --file "$TMP/g4.md"
else FAILS=$((FAILS+1)); echo "  N4 could not be built"; fi

echo
echo "G-8 INVARIANTS — byte comparison against $BASE, not an assertion"
git show "$BASE:$GATES" > "$TMP/base.md" 2>/dev/null || { echo "  cannot read $BASE:$GATES"; FAILS=$((FAILS+1)); }

extract_register() { grep -n '^| \*\*G-8\*\* |' "$1" | head -1 | cut -d: -f2-; }
extract_law()      { awk '/^last row EMI = E \+ B ;/{f=1} f{print} /^PARTIAL family B/{if(f)exit}' "$1"; }
extract_t277()     { awk '/^#### CORRECTION \(T277\)/{f=1} f{print} /^##### The rejected/{if(f)exit}' "$1"; }

for what in register law t277; do
  "extract_$what" "$TMP/base.md" > "$TMP/base.$what"
  "extract_$what" "$GATES"       > "$TMP/head.$what"
done

# the T277 block ends at a different heading on HEAD (T332's section is inserted
# between), so compare it up to the T332 heading instead.
awk '/^#### CORRECTION \(T277\)/{f=1} f{print} /^#### T332 —/{if(f)exit}' "$GATES" \
  | sed '$d' > "$TMP/head.t277"
sed '$d' "$TMP/base.t277" > "$TMP/base.t277.trim"
mv "$TMP/base.t277.trim" "$TMP/base.t277"

for what in register law t277; do
  if cmp -s "$TMP/base.$what" "$TMP/head.$what"; then
    printf '  cmp  %-38s IDENTICAL  (%s bytes)\n' "$what" "$(wc -c < "$TMP/head.$what" | tr -d ' ')"
  else
    printf '  cmp  %-38s DIFFERS\n' "$what"; diff "$TMP/base.$what" "$TMP/head.$what" | head -20
    FAILS=$((FAILS+1))
  fi
done

echo
echo "G-8 SUBSTANCE SENTENCES — present and unmoved OUTSIDE the T332 section"
# gates.md's own warning applies to this check: "never publish a figure whose subject
# includes the text stating it". T332's new section restates two of these sentences,
# so a bare count would MOVE by construction. The check therefore subtracts the
# occurrences inside the T332 section and requires the REMAINDER to be unchanged.
awk '/^#### T332 —/{f=1} f{print} /^##### The rejected/{if(f)exit}' "$GATES" > "$TMP/t332sec.md"
for s in 'options (b)/(c) STILL MUST NOT be put to Buyan' \
         'conservative superset** (`B_minor < 1.5·n`)' \
         'unproven conjecture `δ ≤ 1`' \
         'options (b) and (c) still MUST NOT be put to Buyan'; do
  b=$(grep -cF "$s" "$TMP/base.md"); h=$(grep -cF "$s" "$GATES"); t=$(grep -cF "$s" "$TMP/t332sec.md")
  r=$((h - t))
  if [ "$b" = "$r" ]; then printf '  %-52s outside-T332 %s == base %s  (T332 adds %s)\n' "${s:0:50}" "$r" "$b" "$t"
  else printf '  %-52s outside-T332 %s != base %s  MOVED\n' "${s:0:50}" "$r" "$b"; FAILS=$((FAILS+1)); fi
done

echo
if [ "$FAILS" -eq 0 ]; then echo "T332 VERIFY: PASS"; exit 0; fi
echo "T332 VERIFY: FAIL ($FAILS)"; exit 1
