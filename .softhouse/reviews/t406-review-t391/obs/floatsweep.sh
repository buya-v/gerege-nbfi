#!/bin/bash
# T406 float sweep. Runs over the ADDED lines of the full T391 diff, excluding
# COMMENT/PROSE lines, so what is left is executable code and vector data only.
set -u
D=/tmp/t406-full.diff

echo "=== 1. ADDED lines mentioning a float construct, EXCLUDING prose/comment lines ==="
grep '^+' "$D" \
 | grep -vE '^\+\+\+' \
 | grep -vE '^\+[[:space:]]*(//|#|\*|\|)' \
 | grep -vE '^\+[[:space:]]*$' \
 | grep -nE 'float64|float32|big\.Float|strconv\.ParseFloat|FormatFloat|%\.?[0-9]*f[^a-zA-Z]|\bDouble\b|math\.Round|\bfloat\(' \
 || echo "  (no hits)"

echo
echo "=== 2. ALL added lines containing the literal token 'float' (any case) ==="
grep -c -i 'float' <(grep '^+' "$D") || true
echo "  -- of which NOT prose/comment:"
grep '^+' "$D" \
 | grep -vE '^\+\+\+' \
 | grep -vE '^\+[[:space:]]*(//|#|\*|\|)' \
 | grep -i 'float' || echo "  (none)"

echo
echo "=== 3. Go division / multiplication in the touched Go files (money risk) ==="
for f in nexus/internal/apps/ledger/conformance/vector.go \
         nexus/internal/apps/ledger/conformance/admit.go \
         nexus/internal/apps/ledger/conformance/grade.go \
         nexus/internal/apps/ledger/conformance/impl.go; do
  echo "--- $f: added lines with / or * or e-notation outside comments"
  git diff main...softhouse/T391-accrual-promotion -- "$f" \
   | grep '^+' | grep -vE '^\+\+\+' \
   | grep -vE '^\+[[:space:]]*(//|\*)' \
   | grep -E '[^/*]/[^/*]|\*[[:space:]]*[0-9]|[0-9]e[-+][0-9]' || echo "    (none)"
done

echo
echo "=== 4. Vector JSON: every numeric-looking money token must be a STRING ==="
python3 - <<'PY'
import json, glob, os, sys
bad = 0
for p in sorted(glob.glob('.softhouse/reviews/t406-review-t391/vectors/LDG-ACC-*.json')):
    raw = open(p).read()
    d = json.loads(raw)          # default parse: a bare JSON number becomes float/int
    def walk(o, path=''):
        global bad
        if isinstance(o, dict):
            for k, v in o.items():
                walk(v, path + '.' + k)
        elif isinstance(o, list):
            for i, v in enumerate(o):
                walk(v, path + '[%d]' % i)
        elif isinstance(o, float):
            print('  FLOAT-TYPED JSON NUMBER at %s%s = %r' % (os.path.basename(p), path, o))
            bad += 1
    walk(d)
    # every money-bearing field must be a str
    for fld in ('amount_minor', 'amount_major_text', 'total_debits_minor',
                'total_credits_minor', 'margin_minor', 'transaction_amount_major_text'):
        for m in [x for x in raw.split('"') if x == fld]:
            pass
    e = d['expect']
    for i, l in enumerate(e['legs']):
        for fld in ('amount_minor', 'amount_major_text'):
            if not isinstance(l[fld], str):
                print('  NOT A STRING: %s expect.legs[%d].%s' % (p, i, fld)); bad += 1
    for fld in ('total_debits_minor', 'total_credits_minor'):
        if not isinstance(e[fld], str):
            print('  NOT A STRING: %s expect.%s' % (p, fld)); bad += 1
    for i, l in enumerate(d['request']['legs']):
        if not isinstance(l['amount_major_text'], str):
            print('  NOT A STRING: %s request.legs[%d].amount_major_text' % (p, i)); bad += 1
    for g in d.get('graded_against', []):
        if not isinstance(g['margin_minor'], str):
            print('  NOT A STRING: %s graded_against margin_minor' % p); bad += 1
print('  float-typed JSON numbers / non-string money fields: %d' % bad)
PY

echo
echo "=== 5. Third-decimal check on EVERY amount token in the three vectors ==="
grep -ohE '"[0-9]+\.[0-9]+"' .softhouse/reviews/t406-review-t391/vectors/LDG-ACC-*.json \
 | sort -u | while read -r t; do
     s=${t//\"/}
     frac=${s#*.}
     tail=${frac:2}
     if [ -n "${tail//0/}" ]; then echo "  NON-ZERO THIRD DECIMAL: $s"; else echo "  ok $s (tail='$tail')"; fi
   done
