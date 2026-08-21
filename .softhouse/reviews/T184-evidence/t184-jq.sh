#!/bin/bash
# T184: cross-check the guard's numeric-token count with jq — a completely different parser.
W=/Users/buv/gerege-nbfi/.claude/worktrees/agent-ae0f13a1bbf7c82f8
cd "$W"
CAP=.softhouse/capture
find "$CAP" -type f -name '*.json' -path '*/req/*' | awk -F/ '{ if ($(NF-1)=="req") print }' | sort > /tmp/t184-bodies.txt
wc -l < /tmp/t184-bodies.txt | xargs echo "bodies:"
total=0
while IFS= read -r f; do
  n="$(jq '[.. | numbers] | length' "$f" 2>/dev/null)"
  [ -n "$n" ] || { echo "JQ FAILED on $f"; continue; }
  total=$((total + n))
done < /tmp/t184-bodies.txt
echo "jq numeric-scalar total: $total   (guard reports 3976)"

# float-shaped = the token text contains '.' or 'e'/'E'. Count with a raw source scan
# over the SAME body set, using python's parser but a rule I state myself.
python3 - <<'PYEOF'
import json, sys
tot = flt = 0
files_with_float = 0
keys = {}
for line in open('/tmp/t184-bodies.txt'):
    p = line.strip()
    toks = []
    def h(kind):
        def f(s):
            toks.append((kind, s)); return s
        return f
    # capture key context by walking the raw text is overkill; use object_pairs_hook
    pairs = []
    def oph(items):
        for k, v in items:
            pairs.append((k, v))
        return dict(items)
    json.loads(open(p, 'rb').read().decode('utf-8'),
               parse_float=h('float'), parse_int=h('int'), object_pairs_hook=oph)
    tot += len(toks)
    f_here = [s for kind, s in toks if kind == 'float']
    flt += len(f_here)
    if f_here:
        files_with_float += 1
    for k, v in pairs:
        if isinstance(v, str) and (('.' in v or 'e' in v or 'E' in v)) and v.replace('.','',1).replace('-','',1).isdigit():
            keys[k] = keys.get(k, 0) + 1
print('MY rule: numeric tokens total      %d   (guard reports 3976)' % tot)
print('MY rule: float-shaped tokens       %d   (guard reports 278)' % flt)
print('MY rule: bodies carrying >=1 float %d   (T173 handoff claims 221 of 320)' % files_with_float)
print('MY rule: float-valued keys by name:')
for k in sorted(keys, key=lambda k: -keys[k]):
    print('   %-28s %d' % (k, keys[k]))
PYEOF
