#!/usr/bin/env python3
"""T182 INDEPENDENT re-derivation of T177's headline tallies, straight from the committed raw
per-process stdout. Deliberately does NOT import analyze_t177.py or sweep_integrity — if this
agrees with T177, the agreement is not circular. Zero trials read is an ERROR (P-35)."""
import glob, json, os, sys
from collections import defaultdict

out = sys.argv[1]
trials = []
procs = set()
for f in sorted(glob.glob(out + '/*/raw/*.stdout')):
    matrix = os.path.basename(os.path.dirname(os.path.dirname(f)))
    run = os.path.basename(f)[:-len('.stdout')]
    saw_footer = False
    for ln in open(f, errors='replace'):
        ln = ln.strip()
        if not ln.startswith('{'):
            continue
        d = json.loads(ln)
        if d.get('kind') == 'header':
            procs.add((matrix, run))
            d_hdr = d
        if d.get('kind') == 'footer':
            saw_footer = True
        if d.get('kind') != 'trial':
            continue
        d['_proc'] = (matrix, run)
        d['_flags'] = None
        trials.append(d)
    if not saw_footer:
        print('NO FOOTER:', f)

if not trials:
    sys.exit('ERROR: zero trials read (P-35)')

# flags come from the run-index, not from the analyzer
flags = {}
for idx in sorted(glob.glob(out + '/*/run-index.txt')):
    matrix = os.path.basename(os.path.dirname(idx))
    for ln in open(idx):
        if not ln.startswith('RUN '):
            continue
        kv = dict(p.split('=', 1) for p in ln.split() if '=' in p)
        # flags=[..] may contain spaces; re-parse
        f0 = ln.split('flags=[', 1)[1].split(']', 1)[0]
        flags[(matrix, '%s-%s' % (kv['series'], kv['idx']))] = f0
for t in trials:
    t['_flags'] = flags.get(t['_proc'], '?')

probes = [t for t in trials if t.get('phase') == 'probe']
print('processes with a header: %d ; trials: %d ; probe trials: %d' % (len(procs), len(trials), len(probes)))

# --- COLD START: probe is the process's seq==0 trial ---
cold = defaultdict(lambda: [0, 0])
for t in probes:
    if t['seq'] != 0:
        continue
    key = (t['cellId'], t['_flags'])
    cold[key][0 if t['outcome'] == 'observed' else 1] += 1
print('\nCOLD START (seq==0), keyed by (cell, EXACT jvm flags):')
for k in sorted(cold):
    print('   %-34s flags=%-32s observed=%-3d threw=%-3d' % (k[0], k[1] or '(none)', cold[k][0], cold[k][1]))

# --- step function strings, per process, per cell ---
print('\nPER-PROCESS OUTCOME STRING (o=observed, X=threw), probes only:')
byproc = defaultdict(list)
for t in probes:
    byproc[(t['_proc'], t['cellId'], t['_flags'])].append(t)
step5 = {'flip_at_5': 0, 'other': 0}
exact_XXXXoooo = 0
for k in sorted(byproc, key=lambda x: (x[1], x[0])):
    ts = sorted(byproc[k], key=lambda x: x['seq'])
    s = ''.join('o' if t['outcome'] == 'observed' else 'X' for t in ts)
    if len(ts) > 4:
        print('   %-9s %-22s %-30s flags=%-26s %s' % (k[0][0], k[0][1], k[1], k[2] or '(none)', s))
        if s == 'XXXXoooo':
            exact_XXXXoooo += 1
        if k[1] == 'T177-PROBE-R600p0-N3000-B10001' and 'TieredStop' not in (k[2] or ''):
            if s.startswith('XXXX') and s[4] == 'o':
                step5['flip_at_5'] += 1
            else:
                step5['other'] += 1
print('\n  disputed-cell JVMs (C2 on) with >4 attempts: flip exactly at attempt 5 = %d, other = %d'
      % (step5['flip_at_5'], step5['other']))
print('  processes whose probe string is LITERALLY "XXXXoooo" (any cell, any flags) = %d' % exact_XXXXoooo)

# --- errorStackDepthTotal by flags ---
print('\nerrorStackDepthTotal, grouped by EXACT flags:')
depth = defaultdict(set)
for t in trials:
    if t['outcome'] == 'observed':
        continue
    d = t.get('errorStackDepthTotal')
    if d is None:
        for kk in ('threw', 'error'):
            if isinstance(t.get(kk), dict):
                d = t[kk].get('errorStackDepthTotal')
    depth[t['_flags'] or '(none)'].add(d)
for k in sorted(depth, key=str):
    print('   flags=%-32s distinct depths=%s' % (k, sorted(x for x in depth[k] if x is not None)))

# --- money ---
print('\nMONEY — distinct totalInterestAmount / totalPrincipalAmount per cell over ALL observed trials:')
money = defaultdict(lambda: (defaultdict(int), defaultdict(int)))
for t in trials:
    if t['outcome'] != 'observed':
        continue
    o = t['observed']
    money[t['cellId']][0][o['totalInterestAmount']] += 1
    money[t['cellId']][1][o['totalPrincipalAmount']] += 1
    assert not isinstance(o['totalInterestAmount'], float), 'FLOAT in money field'
for cid in sorted(money):
    i, p = money[cid]
    print('   %-36s interest=%s principal=%s' % (cid, dict(i), dict(p)))
