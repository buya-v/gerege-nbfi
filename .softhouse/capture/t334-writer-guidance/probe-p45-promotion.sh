#!/usr/bin/env bash
# T334 / FU-T301-3 - is the paraphrase quoted as `P-45` anywhere in the register,
# and what happens if it is RECORDED as its own rule?
#
# Run: bash .softhouse/capture/t334-writer-guidance/probe-p45-promotion.sh [REPO]
# All driving happens in a THROWAWAY CLONE under $TMPDIR. The live checkout is never written.
set -u
REPO="${1:-$(cd "$(dirname "$0")/../../.." && pwd)}"
CHK=".softhouse/capture/t282-pnumber-drift/bin/check-pnumber-citations.py"
SCRATCH="$(mktemp -d "${TMPDIR:-/tmp}/t334-p45.XXXXXX")"
PARA="a guard that only works when someone remembers to run it enforces nothing"

echo "REPO    : $REPO"
echo "HEAD    : $(git -C "$REPO" rev-parse --short HEAD 2>/dev/null)"
echo "SCRATCH : $SCRATCH"
echo

echo "=== 1. P-45's RECORDED TEXT, read from the register itself ==="
grep -n '^\*\*P-45' -A4 "$REPO/.softhouse/patterns.md"
echo

echo "=== 2. DOES ANY RECORDED RULE STATE THE PARAPHRASE? ==="
echo "grep for the paraphrase inside patterns.md (the register):"
printf '  hits in patterns.md: %s\n' "$(grep -c "$PARA" "$REPO/.softhouse/patterns.md")"
echo "  => 0 means the sentence is an UNRECORDED GLOSS: it is not P-45's text and it is not"
echo "     any other P-n's text either. This is NOT the T282 off-by-one shape (cited P-x,"
echo "     actually P-y); there is no P-y."
echo

echo "=== 3. WHO CITES IT AS P-45 (tracked tree, checker's own corpus) ==="
git -C "$REPO" grep -c -I "$PARA" -- . 2>/dev/null | sed 's/^/  /'
echo

git clone -q --local --no-hardlinks "$REPO" "$SCRATCH/clone" || { echo "CLONE FAILED"; exit 1; }

echo "=== 4. BEFORE: checker verdict on the tree as it stands ==="
python3 "$SCRATCH/clone/$CHK" --root "$SCRATCH/clone" 2>&1 | grep -E '^PNUMBER-CITATIONS: VERDICT'
python3 "$SCRATCH/clone/$CHK" --root "$SCRATCH/clone" --json "$SCRATCH/before.json" >/dev/null 2>&1
python3 - "$SCRATCH/before.json" <<'PY'
import json, sys
from collections import Counter
d = json.load(open(sys.argv[1]))
# Match on a SUBSTRING, not the whole sentence: several citations are LINE-WRAPPED and each
# half is a separate finding. Asking with the full sentence undercounts (16 vs 25) -- caught
# only by asking the same question two ways and refusing to accept the first answer.
hits = [f for f in d['findings'] if 'remembers to run' in (f.get('text', '') + f.get('detail', ''))]
print("  paraphrase findings: %d across %d files; kinds=%s; fatal=%d; cited ids=%s"
      % (len(hits), len({h['file'] for h in hits}), dict(Counter(h['kind'] for h in hits)),
         sum(h['fatal'] for h in hits), sorted({h['cited'] for h in hits})))
PY
echo "  => every one is BARE ('matches no registered rule', best trigram 1 < 6) and NON-FATAL."
echo "     The checker cannot bind the sentence because nothing defines it."
echo

echo "=== 5. THE TRAP: record the paraphrase as its own rule, then re-run ==="
cat >> "$SCRATCH/clone/.softhouse/patterns.md" <<'EOF'

**P-97 — A guard that only works when someone remembers to run it enforces nothing.** TEST INSERTION.

EOF
python3 "$SCRATCH/clone/$CHK" --root "$SCRATCH/clone" --show fatal 2>&1 \
  | grep -E '^PNUMBER-CITATIONS: (FATAL|VERDICT)' | sed -e 's/ matches P-97.*//' | sed 's/^/  /'
echo
echo "  => Recording the sentence turns 25 harmless BARE citations into MISDIRECTING ones,"
echo "     7 of them in the DIRECTIVE zone, which is FATAL and turns the bar RED -- in four"
echo "     files T334 is forbidden to edit. So the erratum is the correction, and promoting"
echo "     the gloss to a rule is a SEQUENCED change: fix the 25 citing sites FIRST."
rm -rf "$SCRATCH"
echo "DONE"
