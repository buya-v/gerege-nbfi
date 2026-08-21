#!/bin/bash
# T184: is the implemented property really "byte-preserved under a BINARY-DOUBLE round trip"?
# Probe the int branch, which defect_render() sends through int() and not through float().
W=/Users/buv/gerege-nbfi/.claude/worktrees/agent-ae0f13a1bbf7c82f8
cd "$W"
python3 - <<'PYEOF'
import sys, os
sys.path.insert(0, os.path.join('.softhouse', 'capture', 'lib'))
import check_wire_float_roundtrip as G

cases = [
    ('1200000',              'int money, exact'),
    ('1200000.00',           'the T163 defect'),
    ('21.6',                 'a rate'),
    ('1162502.5',            'the half-cent tie probe'),
    ('9007199254740993',     'INT token, 2**53+1 — a true double round trip LOSES this'),
    ('12345678901234567890', 'INT token, 20 digits — a true double round trip mangles this'),
    ('12345678901234567890.12', 'FLOAT token, same magnitude'),
    ('1e2',                  'exponent form'),
    ('-0',                   'negative zero as an int'),
    ('0.1',                  '0.1'),
]
print('%-26s %-6s %-26s %-26s %s' % ('token', 'kind', 'guard renders', 'TRUE double round trip', 'guard flags?'))
for t, why in cases:
    kind = 'float' if any(c in t for c in '.eE') else 'int'
    g = G.defect_render(kind, t)
    import json
    try:
        d = json.dumps(float(t))
    except Exception as e:
        d = 'ERR'
    print('%-26s %-6s %-26s %-26s %-5s   %s' % (t, kind, g, d, 'YES' if g != t else 'no', why))
PYEOF
