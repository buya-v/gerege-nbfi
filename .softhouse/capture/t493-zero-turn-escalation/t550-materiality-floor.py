import subprocess, re, datetime, collections, hashlib, sys
REF=sys.argv[1] if len(sys.argv)>1 else 'origin/main'
CWD=sys.argv[2] if len(sys.argv)>2 else '/home/user/wt/T550'
def run(a): return subprocess.run(a,capture_output=True,text=True,cwd=CWD,errors='replace').stdout
raw=run(['git','log',REF,'--no-merges','--numstat','--format=@@%H|%cI'])
commits=[];cur=None
for line in raw.splitlines():
    if line.startswith('@@'):
        sha,ts=line[2:].split('|',1); cur={'sha':sha,'ts':ts,'files':[],'stat':[]}; commits.append(cur)
    elif line.strip() and cur:
        p=line.split('\t')
        if len(p)>=3:
            cur['files'].append(p[2]); cur['stat'].append((p[2],0 if p[0]=='-' else int(p[0]),0 if p[1]=='-' else int(p[1])))
commits.reverse()
SURF=re.compile(r'^nexus/|^\.softhouse/(capture|vectors|handoff|reviews|guards|bin)/|^\.claude/|^docs/adr/')
NULL=re.compile(r'^[\s{}()\[\];,.:*=_~`>|+-]*(//+|\#+|--+|<!--|-->|/\*+|\*+/|\*+)?[\s{}()\[\];,.:*=_~`>|+-]*$')
p=subprocess.run(['bash','-c',"git log %s --no-merges -p -U0 --no-color --format='@COMMIT@%%H' | awk '/^@COMMIT@/{n=0;print;next} /^\\+\\+\\+ /{print;next} /^\\+/{if(n<200){print;n++} next}'"%REF],capture_output=True,text=True,cwd=CWD,errors='replace').stdout
pay=collections.defaultdict(list); sha=None; on=False
for line in p.splitlines():
    if line.startswith('@COMMIT@'): sha=line[8:].strip(); on=False
    elif line.startswith('+++ '):
        q=line[4:].strip();  q=q[2:] if q.startswith('b/') else q
        on = q!='/dev/null' and bool(SURF.search(q))
    elif on and sha and line.startswith('+'): pay[sha].append(line[1:])
for c in commits:
    c['dt']=datetime.datetime.fromisoformat(c['ts']); c['off']=c['ts'][-6:]
    c['anchor']=[f for f in c['files'] if SURF.search(f)]
    c['subst']=[l for l in pay.get(c['sha'],[]) if not NULL.match(l)]
    c['earned']=bool(c['anchor'] and c['subst'])
LOCK='.softhouse/LOCK'
def lev(c):
    if not c['stat'] or any(x!=LOCK for x,_,_ in c['stat']): return None
    i=sum(a for _,a,_ in c['stat']); d=sum(b for _,_,b in c['stat'])
    if i>0 and d==0: return 'take'
    if d>0 and i==0: return 'release'
    return 'take' if i else None
for off,label in [('+08:00','local'),('+00:00','cloud')]:
    pool=[c for c in commits if c['off']==off]
    fires=[c for c in pool if lev(c)=='take']; fires.sort(key=lambda c:c['dt'])
    reals=[c for c in pool if c['earned']]
    now=commits[-1]['dt']
    runs=[]; cur_run=0; best=0; bestwin=None
    hist=collections.Counter(); mins=[]
    for i,f in enumerate(fires):
        end = fires[i+1]['dt'] if i+1<len(fires) else now
        r=[c for c in reals if f['dt']<=c['dt']<end]
        if not r: cur_run=0; continue   # a fully no-op fire: AXIS 1 already covers it
        m=max(len(c['subst']) for c in r)
        hist[min(m,10)]+=1
        mins.append(m)
        if m<=2:
            cur_run+=1
            if cur_run>best: best=cur_run; bestwin=(f['dt'],end)
        else: cur_run=0
    print(f"{label}: fires={len(fires)} longest run of CLEARED-BUT-THIN(<=2 subst lines) fires = {best} {bestwin}")
    print(f"   min over cleared fires of (max substantive lines in its promotions) = {min(mins) if mins else None}; cleared fires={len(mins)}")
