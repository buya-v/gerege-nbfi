import re, os, sys, collections
ADR='docs/adr/DEC-1-schedule-generator-adapter.md'
ROOT='/Users/buv/fineract'
txt=open(ADR).read()
# build index of java file basenames -> paths (main sources preferred)
idx=collections.defaultdict(list)
for dp,dn,fn in os.walk(ROOT):
    if '/.git/' in dp: continue
    for f in fn:
        if f.endswith('.java'):
            idx[f].append(os.path.join(dp,f))
pat=re.compile(r'([A-Za-z][A-Za-z0-9_]*\.java):(\d+)(?:-(\d+))?')
bad=[];amb=[];ok=0
seen=set()
for m in pat.finditer(txt):
    key=m.group(0)
    f,a,b=m.group(1),int(m.group(2)),m.group(3)
    b=int(b) if b else a
    cands=idx.get(f,[])
    mains=[c for c in cands if '/src/main/' in c]
    use=mains if mains else cands
    if not use:
        bad.append((key,'NO SUCH FILE')); continue
    if len(set(use))>1:
        amb.append((key,len(use)))
    p=sorted(use)[0]
    n=sum(1 for _ in open(p,encoding='utf-8',errors='replace'))
    if a<1 or b>n or a>b:
        bad.append((key,f'OUT OF RANGE (file has {n} lines)'))
    else:
        ok+=1
    seen.add(key)
print('distinct citations:',len(seen),'in-range checks passed:',ok)
print('AMBIGUOUS basenames (multiple main files):')
for k,c in sorted(set(amb)): print('  ',k,c)
print('BAD:')
for k,r in sorted(set(bad)): print('  ',k,r)
