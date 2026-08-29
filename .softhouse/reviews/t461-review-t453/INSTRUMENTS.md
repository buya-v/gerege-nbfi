# T461 instruments

Shipped as fenced blocks, not as tracked `*.sh` / `*.py`. A tracked shell or python file
under the softhouse tree joins three corpora at once -- the dead-path census, the fail-open
lint and the host-state lint -- and a review is not the place to move three pins. Every
repository path below is assembled from a variable (`SH` carries no trailing slash, which is
what keeps it out of the census selector); nothing writes outside `$TMPDIR`; nothing touches
the live `pre-push` hook.

Save each block, then run it from a checkout of this repository.

## 1. `coverage.py` -- cheap-path coverage under four rules

```python
#!/usr/bin/env python3
"""Re-derive T453's cheap-path coverage numbers, independently."""
import subprocess, sys, fnmatch, collections

REPO = sys.argv[1]
REV  = sys.argv[2] if len(sys.argv) > 2 else "main"
N    = 400
SH   = ".softhouse"          # assembled, never spelled with a trailing slash literal

def git(*a):
    p = subprocess.run(["git","-C",REPO]+list(a), capture_output=True, text=True)
    if p.returncode != 0:
        raise SystemExit("git %s failed: %s" % (a, p.stderr[:400]))
    return p.stdout

# bash `case` semantics: fnmatch with * crossing '/'
def m(pat, s):
    return fnmatch.fnmatchcase(s, pat)

def state_path(p, variant):
    for d in ("vectors","guards","bin","toolchain"):
        if m(SH+"/"+d+"/*", p): return False
    if variant in ("t453","modonly"):
        for d in ("capture","reviews"):
            if m(SH+"/"+d+"/*", p): return False
    if variant == "caponly":
        if m(SH+"/capture/*", p): return False
    if p == SH+"/conformance.sh": return False
    if m("*/req/*", p): return False
    if p == SH+"/LOCK": return True
    for e in ("md","txt","json","log"):
        if m(SH+"/*."+e, p): return True
    return False

commits = git("rev-list","--first-parent","--no-merges","--max-count=%d"%N, REV).split()
print("commits examined:", len(commits))

stats = {}
for variant in ("t412","t453","caponly","modonly"):
    stats[variant] = 0

addcount = 0
lockadds = 0
nonstate_examples = collections.Counter()
added_in_covered = []

for c in commits:
    out = git("show","--pretty=format:","--name-status", c)
    ents = []
    for line in out.splitlines():
        if not line.strip(): continue
        parts = line.split("\t")
        st = parts[0]
        path = parts[-1]
        ents.append((st, path))
    for st,path in ents:
        if st.startswith("A"):
            addcount += 1
            if path == SH+"/LOCK": lockadds += 1
    for variant in ("t412","t453","caponly","modonly"):
        ok = True
        for st,path in ents:
            base = st[0]
            if variant == "modonly":
                if base != "M": ok=False; break
            else:
                if base not in ("A","M"): ok=False; break
            if not state_path(path, variant): ok=False; break
        if ok: stats[variant]+=1
    okA = all(s[0] in ("A","M") and state_path(p,"t453") for s,p in ents)
    okM = all(s[0]=="M" and state_path(p,"t453") for s,p in ents)
    if okA:
        for st,path in ents:
            if st[0]=="A": added_in_covered.append((c,path))
    if okA and not okM:
        for st,path in ents:
            if st[0]=="A": nonstate_examples[path]+=1

for variant in ("t412","t453","caponly","modonly"):
    n=stats[variant]
    print("%-9s covered %3d/%d = %.1f%%" % (variant, n, len(commits), 100.0*n/len(commits)))
print("total ADDITION entries across the %d commits: %d" % (len(commits), addcount))
print("A <LOCK> entries: %d" % lockadds)
print("additions inside t453-covered commits: %d" % len(added_in_covered))
print("top additions that modonly would newly block:", nonstate_examples.most_common(8))
with open("/tmp/t461/added-in-covered.txt","w") as f:
    for c,p in added_in_covered:
        f.write("%s\t%s\n" % (c,p))
```

## 2. `entries.py` -- the name-status population the coverage figure is drawn from

```python
#!/usr/bin/env python3
import subprocess, sys, collections
REPO=sys.argv[1]; REV=sys.argv[2]; SH=".softhouse"
def git(*a):
    p=subprocess.run(["git","-C",REPO]+list(a),capture_output=True,text=True)
    if p.returncode: raise SystemExit(p.stderr[:300])
    return p.stdout
commits=git("rev-list","--first-parent","--no-merges","--max-count=400",REV).split()
cap=0; rev=0; tot=0; st_counter=collections.Counter(); top=collections.Counter()
for c in commits:
    for line in git("show","--pretty=format:","--name-status",c).splitlines():
        if not line.strip(): continue
        parts=line.split("\t"); s=parts[0]; p=parts[-1]
        tot+=1; st_counter[s[0]]+=1
        if p.startswith(SH+"/capture/"): cap+=1
        if p.startswith(SH+"/reviews/"): rev+=1
        top[p.split("/")[0] if not p.startswith(SH+"/") else "/".join(p.split("/")[:2])]+=1
print("total name-status entries:",tot)
print("entries under capture/:",cap," under reviews/:",rev," sum:",cap+rev)
print("status histogram:",dict(st_counter))
print("top prefixes:",top.most_common(15))
```

## 3. `lockhist.py` -- how often the fire lock is added, deleted and modified

```python
#!/usr/bin/env python3
import subprocess, sys, collections
REPO=sys.argv[1]; REV=sys.argv[2]; SH=".softhouse"
def git(*a):
    p=subprocess.run(["git","-C",REPO]+list(a),capture_output=True,text=True)
    if p.returncode: raise SystemExit(p.stderr[:300])
    return p.stdout
commits=git("rev-list","--first-parent","--no-merges","--max-count=400",REV).split()
c=collections.Counter()
lockpath=SH+"/LOCK"
for sha in commits:
    for line in git("show","--pretty=format:","--name-status",sha).splitlines():
        if not line.strip(): continue
        parts=line.split("\t")
        if parts[-1]==lockpath: c[parts[0][0]]+=1
print("LOCK status histogram over 400 non-merge first-parent commits:", dict(c))
```

## 4. `lockguard.sh` -- C-T461-1, the frontier GUARD across the fire-lock cycle

```bash
#!/usr/bin/env bash
# T461 -- drive the FRONTIER GUARD (not the census) across the fire-lock cycle.
set -u
SRC="${1:?}"; REV="${2:?}"
SH='.softhouse'
GUARD="$SH/guards/check-dead-path-frontier.sh"
LOCKREL="$SH/LOCK"
W="$(mktemp -d "${TMPDIR:-/tmp}/t461-lg.XXXXXXXX")" || exit 90
GIT="git -c user.name=t461 -c user.email=t461@invalid -c commit.gpgsign=false"
$GIT clone --local --quiet --no-checkout "$SRC" "$W/wt" || exit 90
cd "$W/wt" || exit 90
SHA="$(git -C "$SRC" rev-parse --verify "$REV^{commit}")" || exit 90
$GIT checkout -q -B t461probe "$SHA" || exit 90
$GIT remote remove origin || exit 90

echo "=== CONTROL: the guard on the untouched tree (lock held)"
bash "$GUARD" >"$W/a.txt" 2>&1; echo "   exit=$?"
grep -aE 'T316-DEADPATH-FRONTIER' "$W/a.txt" | sed 's/^/   /'

echo "=== ARM: the same guard after the end-of-fire lock release ([D] of the lock)"
$GIT rm -q --cached "$LOCKREL" >/dev/null 2>&1 && rm -f "$LOCKREL"
$GIT commit -q -m "t461: end-of-fire lock release" || exit 91
bash "$GUARD" >"$W/b.txt" 2>&1; echo "   exit=$?"
grep -aE 'T316-DEADPATH-FRONTIER' "$W/b.txt" | sed 's/^/   /'
grep -aE '^\+ ' "$W/b.txt" | head -20 | sed 's/^/   /'
echo "scratch $W"
```

### 4b. `lockprobe.sh` -- the CENSUS behind the same finding

```bash
#!/usr/bin/env bash
# T461 -- does the dead-path frontier depend on whether .softhouse/LOCK is TRACKED?
# Everything happens in a throwaway clone under $TMPDIR. Paths are assembled from
# variables; no repo path is spelled as a literal here.
set -u
SRC="${1:?usage: lockprobe.sh <source-repo> <rev>}"
REV="${2:?}"
SH='.softhouse'
CEN="$SH/capture/t316-dead-path-guards/census_dead_paths.py"
LOCKREL="$SH/LOCK"

W="$(mktemp -d "${TMPDIR:-/tmp}/t461-lock.XXXXXXXX")" || exit 90
echo "universe $W"
GIT="git -c user.name=t461 -c user.email=t461@invalid -c commit.gpgsign=false"
$GIT clone --local --quiet --no-checkout "$SRC" "$W/wt" || exit 90
cd "$W/wt" || exit 90
SHA="$(git -C "$SRC" rev-parse --verify "$REV^{commit}")" || exit 90
$GIT checkout -q -B t461probe "$SHA" || exit 90
$GIT remote remove origin || exit 90

echo "--- A: baseline (LOCK tracked? $( git ls-files --error-unmatch "$LOCKREL" >/dev/null 2>&1 && echo YES || echo NO ))"
python3 "$CEN" 2>&1 | grep -aE '^T316-DEADPATH-CENSUS'

echo "--- B: remove the fire lock from the index, exactly as a fire-end push does"
$GIT rm -q --cached "$LOCKREL" >/dev/null 2>&1 || echo "  (LOCK was not tracked; nothing to remove)"
rm -f "$LOCKREL"
$GIT commit -q -m "t461 probe: end-of-fire lock release" || exit 91
echo "    LOCK tracked now? $( git ls-files --error-unmatch "$LOCKREL" >/dev/null 2>&1 && echo YES || echo NO )"
python3 "$CEN" 2>&1 | grep -aE '^T316-DEADPATH-CENSUS'

echo "--- C: which instruments name it"
python3 "$CEN" --json "$W/census.json" >/dev/null 2>&1 || true
echo "done. universe $W"
```

## 5. `cheapenv.sh` -- C-T461-3, which tree the namespace guard grades under the cheap subset

```bash
#!/usr/bin/env bash
# T461 -- FU-T453-1's claim, driven rather than read.
# T453 says: if the cheap tier were extended to run the two standalone inventory
# guards, cheap-subset.sh's read-tree+checkout-index materialisation would make
# check-capture-namespace.sh's `git rev-parse --show-toplevel` grade THE CALLER'S
# TREE (the T165/T201 defect). Reproduce the exact environment cheap-subset.sh
# establishes and ask git which root it reports.
set -u
SRC="${1:?usage: cheapenv.sh <repo> <rev>}"; REV="${2:?}"
SH='.softhouse'
NSGUARD="$SH/guards/check-capture-namespace.sh"

TOP="$(git -C "$SRC" rev-parse --show-toplevel)" || exit 90
COMMON="$(git -C "$SRC" rev-parse --git-common-dir)" || exit 90
case "$COMMON" in /*) : ;; *) COMMON="$TOP/$COMMON" ;; esac
TREE="$(git -C "$SRC" rev-parse --verify "$REV^{tree}")" || exit 90

D="$(mktemp -d "${TMPDIR:-/tmp}/t461-cheapenv.XXXXXXXX")" || exit 90
mkdir -p "$D/tree" || exit 90
export GIT_DIR="$COMMON"
export GIT_INDEX_FILE="$D/index"
export GIT_WORK_TREE="$D/tree"
git read-tree "$TREE"    || exit 90
git checkout-index -a -f || exit 90

echo "caller's toplevel     : $TOP"
echo "materialised tree at  : $D/tree"
echo "git rev-parse --show-toplevel under the cheap-subset environment:"
echo "   -> $(git rev-parse --show-toplevel 2>&1)"
echo "cd into the materialised tree first, then ask again:"
( cd "$D/tree" && echo "   -> $(git rev-parse --show-toplevel 2>&1)" )
echo ""
echo "and now the guard itself, exactly as a future cheap tier would call it:"
( cd "$D/tree" && bash "$NSGUARD" 2>&1 | grep -aE '^namespace:   root|^NAMESPACE-CENSUS|^namespace: (PASS|REFUSED|ABORT)' | sed 's/^/   /' )
echo ""
echo "scratch $D"
```

## 6. `tasksprobe.sh` -- clause (d), driven with a control

```bash
#!/usr/bin/env bash
# T461 -- can a STATE-set MODIFICATION of the driver's biggest write target
# (the task graph json, 235 of 629 name-status entries in the last 400 commits)
# redden guard_reconciler_ownership?  Clause (d) of the STATE set says no,
# because the rig reads that file at PINNED HISTORICAL SHAS.  MEASURED, not read.
set -u
SRC="${1:?usage}"; REV="${2:?}"
SH='.softhouse'
RIG="$SH/capture/t319-reconciler-f5/run-ownership-matrix.py"
TOOL="$SH/bin/ready-tasks.py"
TASKS="$SH/tasks.json"

W="$(mktemp -d "${TMPDIR:-/tmp}/t461-tasks.XXXXXXXX")" || exit 90
GIT="git -c user.name=t461 -c user.email=t461@invalid -c commit.gpgsign=false"
$GIT clone --local --quiet --no-checkout "$SRC" "$W/wt" || exit 90
cd "$W/wt" || exit 90
SHA="$(git -C "$SRC" rev-parse --verify "$REV^{commit}")" || exit 90
$GIT checkout -q -B t461probe "$SHA" || exit 90
$GIT remote remove origin || exit 90

echo "=== A: the rig on the untouched tree (the control -- without it every RED below is unearned)"
/usr/bin/python3 "$RIG" --repo "$PWD" --tool "$PWD/$TOOL" --selftest >"$W/a.txt" 2>&1
echo "   exit=$?  $(grep -ac '^SELFTEST OK:' "$W/a.txt") SELFTEST-OK line(s)"
grep -aE '^(GREEN LEG|RED LEG|SELFTEST OK)' "$W/a.txt" | sed 's/^/   /'

echo "=== B: the SAME rig after a STATE-set-confined [M] of the task graph -- total garbage"
printf 'not json at all { [ ,,,\n' >"$TASKS"
$GIT add -A >/dev/null 2>&1 || exit 91
$GIT commit -q -m "t461 probe: a STATE-set modification of the task graph" || exit 91
/usr/bin/python3 "$RIG" --repo "$PWD" --tool "$PWD/$TOOL" --selftest >"$W/b.txt" 2>&1
echo "   exit=$?  $(grep -ac '^SELFTEST OK:' "$W/b.txt") SELFTEST-OK line(s)"
grep -aE '^(GREEN LEG|RED LEG|SELFTEST OK)' "$W/b.txt" | sed 's/^/   /'
echo "universe $W"
```
