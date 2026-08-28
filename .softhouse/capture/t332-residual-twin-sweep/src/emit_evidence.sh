#!/usr/bin/env bash
# Regenerates every file under evidence/ from the instruments. Nothing under
# evidence/ is hand-written; if a figure in the handoff cannot be produced by this
# script it does not belong in the handoff.
set -u
if [ -z "${BASH_VERSION:-}" ]; then echo "run me with bash"; exit 3; fi
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../.." && pwd)"
cd "$ROOT" || exit 3
S=.softhouse/capture/t332-residual-twin-sweep/src
E=.softhouse/capture/t332-residual-twin-sweep/evidence
mkdir -p "$E"

python3 "$S/t332_twin_audit.py"  --selftest          > "$E/00-selftest.txt" 2>&1
python3 "$S/t332_twin_audit.py"  --scope t229corpus  > "$E/10-census-t229corpus.txt" 2>&1
python3 "$S/t332_twin_audit.py"  --scope all         > "$E/11-census-all.txt" 2>&1
python3 "$S/t332_twin_audit.py"  --seven             > "$E/20-seven-cells.txt" 2>&1
python3 "$S/t332_twin_audit.py"  --sites             > "$E/21-site-claims.txt" 2>&1
python3 "$S/t332_sweep_gates.py" --list              > "$E/30-sweep-gates.txt" 2>&1
bash    "$S/verify_t332.sh"                          > "$E/40-verify.txt" 2>&1

{
  echo "T332 — where I looked, verbatim, so 'not found' is a statement about the SEARCH."
  echo
  echo '$ grep -c . .softhouse/gates.md'; grep -c . .softhouse/gates.md
  echo
  echo '--- every symbolic form, repo-wide, over text files (REPORTED, NOT EDITED outside gates.md)'
  echo '$ grep -rn "min(B_minor\|max(0, B_minor\|B_minor − n·δ" --include=*.md --include=*.py --include=*.json --include=*.sh --include=*.go .'
  grep -rc 'min(B_minor\|max(0, B_minor\|B_minor − n·δ' \
    --include=*.md --include=*.py --include=*.json --include=*.sh --include=*.go . 2>/dev/null \
    | grep -v ':0$' | grep -v '^\./\.softhouse/capture/t332-residual-twin-sweep/' | sort
  echo
  echo '--- the ONE live, non-evidence file outside gates.md that carries the twin: FU-T332-2.'
  echo '    NOT EDITED -- outside T332 declared sole-writer scope. The guard already runs on it:'
  echo '$ python3 src/t332_sweep_gates.py --file .softhouse/gates-proposed-answers.md'
  python3 "$S/t332_sweep_gates.py" --file .softhouse/gates-proposed-answers.md 2>&1 \
    | sed -n '/UNCLASSIFIED restatement/,/scope it to the exception set/p'
  echo
  echo '--- .softhouse/vectors/ carries NO restatement of law (ii) or its twin'
  echo '$ grep -rn "n·δ\|n\*delta\|B_minor" .softhouse/vectors/'
  grep -rn 'n·δ\|n\*delta\|B_minor' .softhouse/vectors/ || echo '(no match)'
  echo
  echo '--- operator variants that do NOT occur in gates.md (searched, absent)'
  for v in 'nδ' 'n×δ' 'n · δ' 'n delta' 'n*delta'; do
    printf '%-10s ' "$v"; grep -cF "$v" .softhouse/gates.md
  done
} > "$E/50-where-i-looked.txt" 2>&1

echo "evidence regenerated under $E"
ls -1 "$E"
