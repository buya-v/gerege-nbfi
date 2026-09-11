#!/bin/bash
# =============================================================================
# review.sh <worktree> <context> [impl]   — the driver's merge review, as one command.
#
# Every merge the driver ran the same ~10 checks by hand. This runs them from the
# DIFF (main..HEAD of the worktree), so nothing depends on what the run CLAIMS:
#
#   1. scope      — every changed path is inside the context, its vectors/capabilities,
#                   or a capture directory. Anything else is listed.
#   2. guards     — .softhouse/guards/ and .softhouse/conformance.sh untouched.
#   3. float      — no float32/float64/ParseFloat/math. on ADDED lines under nexus/.
#   4. hashes     — every ADDED vector's provenance.capture_ref re-hashed against
#                   capture_sha256, plus every "<name>.json … sha256 <hex>" pair its
#                   citation names (resolved next to capture_ref).
#   5. controls   — the four standing controls must read their known values; if one
#                   does not, the INSTRUMENT is wrong and nothing below is trusted.
#   6. drives     — every ADDED RegisterWrong("<ctx>-wrong-…") measured WITH the
#                   worktree's store and WITHOUT the added vectors (scratch copy).
#                   A drive that kills 0 WITH is inert; one that kills >0 WITHOUT
#                   was already killed and the new vector is not why.
#   7. corpus     — <impl> fails 0 vectors; redcount of the context.
#   8. coverage   — every function in a CHANGED non-test port file, from the graded
#                   corpus (committed-store test, -count=1).
#   9. the bar    — bash .softhouse/conformance.sh on the committed tree: exit 2 ONLY by
#                   the §4.4.2 recorded decision; any failed HARD guard is a FAIL. Added
#                   after review.sh PASSED OH-SAVRB-AB and the bar then refused it (SV-09
#                   cited a psql dump the wire-float guard cannot parse). A run's own
#                   reading of its exit 2 is not evidence.
#
# Exit 0 = every check PASS. Exit 1 = a check FAILED (listed). Exit 2 = a measurement
# could not be taken (the silent-zero rule: never read an absence as a zero).
# It never merges, pushes, or writes to the worktree.
# REVIEW_BASE=<rev> overrides the base (used to control-test on an already-merged run).
# =============================================================================
set -u
WT="${1:?usage: review.sh <worktree> <context> [impl]}"; CTX="${2:?context}"; IMPL="${3:-$CTX-go}"
T="$(cd "$(dirname "$0")" && pwd)"
[ -d "$WT/nexus" ] || { echo "review: $WT has no nexus/ — not a worktree of this repo" >&2; exit 2; }
cd "$WT" || exit 2
BASE=${REVIEW_BASE:-$(git merge-base HEAD main)} || { echo "review: no merge-base with main" >&2; exit 2; }
fail=0; unmeasured=0
say(){ printf '%s\n' "$*"; }
bad(){ say "  FAIL  $*"; fail=1; }
ok(){ say "  ok    $*"; }

say "== review $WT  context=$CTX impl=$IMPL  base=${BASE:0:8} head=$(git rev-parse --short HEAD)"
[ -z "$(git status --porcelain --untracked-files=no)" ] || say "  NOTE  uncommitted tracked changes exist — the review reads COMMITTED HEAD only"

say "-- 1 scope"
out=$(git diff --name-only "$BASE" HEAD | grep -v -E "^(nexus/internal/apps/$CTX/|\.softhouse/(vectors/$CTX/|vectors/capabilities-$CTX\.json|capabilities-$CTX\.json|capture/|findings/))")
[ -z "$out" ] && ok "all changes inside $CTX / its vectors / captures / findings" || { bad "outside scope:"; say "$out" | sed 's/^/          /'; }

say "-- 2 guards"
git diff --quiet "$BASE" HEAD -- .softhouse/guards .softhouse/conformance.sh && ok "guards and conformance.sh untouched" || bad "a guard file changed: $(git diff --name-only "$BASE" HEAD -- .softhouse/guards .softhouse/conformance.sh | tr '\n' ' ')"

say "-- 3 float"
out=$(git diff "$BASE" HEAD -- nexus | grep -E '^\+' | grep -v '^+++' | grep -E '\bfloat(32|64)\b|ParseFloat|\bmath\.' )
[ -z "$out" ] && ok "no float on added lines" || { bad "float on added lines:"; say "$out" | head -10 | sed 's/^/          /'; }

say "-- 4 hashes"
VECS=$(git diff --name-only --diff-filter=A "$BASE" HEAD -- ".softhouse/vectors/$CTX/" | grep '\.json$')
if [ -z "$VECS" ]; then say "  --    no vector added"; else
  for v in $VECS; do
    python3 - "$v" <<'PY' || fail=1
import json,hashlib,os,re,sys
v=sys.argv[1]; d=json.load(open(v)); p=d.get('provenance') or {}
ref=p.get('capture_ref'); want=p.get('capture_sha256'); rc=0
def h(f): return hashlib.sha256(open(f,'rb').read()).hexdigest()
if not ref or not want: print(f"  FAIL  {v}: provenance lacks capture_ref/capture_sha256"); sys.exit(1)
if not os.path.exists(ref): print(f"  FAIL  {v}: capture_ref {ref} does not exist"); sys.exit(1)
if h(ref)!=want: print(f"  FAIL  {v}: {ref} sha256 {h(ref)[:12]} != claimed {want[:12]}"); rc=1
else: print(f"  ok    {os.path.basename(v)}: capture_ref hash matches")
cit=json.dumps(p)
for name,hx in re.findall(r'([\w.-]+\.(?:json|txt))[^"]{0,80}?sha256[ :]*([0-9a-f]{64})',cit):
    # A citation that names the FULL path wins: two capture dirs can hold files with the SAME
    # name (provisioning/out/ENT-04… vs provisioning-upper-edge/out/ENT-04…, found on
    # OH-PROVGRADE-BC, where the beside-capture_ref guess hashed the wrong one).
    mfull=re.search(r'([\w./-]*/'+re.escape(name)+')',cit)
    cand=[mfull.group(1), '.softhouse/capture/'+mfull.group(1)] if mfull else []
    cand=[c for c in cand if os.path.exists(c)]
    # A citation relative to the CAPTURE's own root (Tier D: "product-mappings/create-request-X.json"
    # cited from a capture_ref under journalentries/) is found by walking up from capture_ref, never
    # above .softhouse/capture/ (OH-COJGRADE-BY .. OH-ACJGRADE-CH printed NOTE for every such file).
    if not cand:
        rel=mfull.group(1) if mfull else name
        d=os.path.dirname(ref)
        while d.startswith('.softhouse/capture/') and not cand:
            cand=[c for c in (os.path.join(d,rel), os.path.join(d,name)) if os.path.exists(c)]
            d=os.path.dirname(d)
    f=cand[0] if cand else os.path.join(os.path.dirname(ref),name)
    if not os.path.exists(f): print(f"  NOTE  cited {name} not found beside capture_ref"); continue
    if h(f)!=hx: print(f"  FAIL  cited {name} sha256 {h(f)[:12]} != claimed {hx[:12]}"); rc=1
    else: print(f"  ok    cited {name} hash matches")
sys.exit(rc)
PY
  done
fi

say "-- 5 controls (the instrument)"
ctl(){ local c="$1" i="$2" want="$3" got; got=$(bash "$T/kills.sh" "$c" "$i" "$WT" 2>/dev/null); if [ -z "$got" ]; then say "  UNMEASURED $c/$i"; unmeasured=1; elif [ "$got" = "$want" ]; then ok "$i = $got"; else bad "$i = $got, want $want — THE INSTRUMENT IS WRONG"; fi; }
ctl loanschedule loanschedule-wrong-days-in-year-365 48
ctl loanschedule loanschedule-wrong-half-even 5
ctl parties parties-wrong-iota-ordinals 12
ctl charges charges-wrong-rounding-half-even 1

say "-- 6 new drives, with and without the added vectors"
DRIVES=$(git diff "$BASE" HEAD -- "nexus/internal/apps/$CTX/conformance/" | grep -E '^\+' | grep -o -E "RegisterWrong\(\"$CTX-wrong-[a-z0-9-]+\"" | sed -E 's/RegisterWrong\("//; s/"$//' | sort -u)
if [ -z "$DRIVES" ]; then say "  --    no drive added"
elif [ "$CTX" = ledger ]; then say "  NOTE  ledger has no conformance binary: read the CENSUS block of conformance.sh for: $DRIVES"; unmeasured=1
else
  S=$(mktemp -d); rsync -a --exclude .git "$WT/" "$S/"; for v in $VECS; do rm -f "$S/$v"; done
  for d in $DRIVES; do
    w=$(bash "$T/kills.sh" "$CTX" "$d" "$WT" 2>/dev/null); wo=$(bash "$T/kills.sh" "$CTX" "$d" "$S" 2>/dev/null)
    if [ -z "$w" ] || [ -z "$wo" ]; then say "  UNMEASURED $d (with='$w' without='$wo')"; unmeasured=1
    elif [ "$w" -eq 0 ]; then bad "$d kills 0 WITH the store — inert"
    elif [ -n "$VECS" ] && [ "$wo" -ne 0 ]; then say "  NOTE  $d with=$w without=$wo — already killed before the new vector(s)"
    else ok "$d with=$w without=$wo"; fi
  done; rm -rf "$S"
fi

say "-- 7 corpus"
if [ "$CTX" = ledger ]; then say "  NOTE  ledger: corpus graded by conformance.sh only"; else
  c=$(bash "$T/capcount.sh" "$WT" "$CTX" "$IMPL" 2>/dev/null); r=$(bash "$T/redcount.sh" "$WT" "$CTX" 2>/dev/null)
  [ -z "$c" ] && { say "  UNMEASURED capcount"; unmeasured=1; } || { [ "$c" -eq 0 ] && ok "$IMPL fails 0 vectors" || bad "$IMPL fails $c vectors"; }
  [ -n "$r" ] && say "  info  $r $CTX drives kill (compare with main)"
fi

say "-- 8 coverage of changed port files, from the graded corpus"
FILES=$(git diff --name-only "$BASE" HEAD -- "nexus/internal/apps/$CTX/" | grep '\.go$' | grep -v -E '_test\.go$|/conformance/')
if [ -z "$FILES" ]; then say "  --    no port file changed"; else
  cov=$(mktemp); (cd nexus && go test -count=1 -coverpkg=./internal/apps/$CTX -coverprofile="$cov" ./internal/apps/$CTX/conformance/... >/dev/null 2>&1) || { say "  UNMEASURED coverage: go test failed"; unmeasured=1; }
  for f in $FILES; do (cd nexus && go tool cover -func="$cov" 2>/dev/null | grep "/${f#nexus/}:" | sed 's/^/  info  /; s/github.com\/[^ ]*\/internal/internal/'); done
  rm -f "$cov"
fi

say "-- 9 the full bar (conformance.sh) on the committed tree"
if [ "${REVIEW_SKIP_BAR:-0}" = 1 ]; then say "  UNMEASURED bar skipped by REVIEW_SKIP_BAR=1"; unmeasured=1; else
  bl=$(mktemp); (cd "$WT" && bash .softhouse/conformance.sh >"$bl" 2>&1); brc=$?
  if grep -q 'a HARD guard failed' "$bl"; then bad "the bar: a HARD guard failed —"; grep -A3 -E 'REFUSED' "$bl" | grep -v 'NAMED, NOT REFUSED' | head -8 | sed 's/^/          /'
  elif [ $brc -eq 2 ] && grep -q '§4.4.2-RECORDED-DECISION-EXIT' "$bl"; then ok "exit 2 by the §4.4.2 recorded decision (ledger findings == baseline)"
  elif [ $brc -eq 0 ]; then ok "exit 0"
  else bad "the bar exited $brc without the recorded-decision line — read $bl"; bl=; fi
  [ -n "$bl" ] && rm -f "$bl"
fi

say "== verdict: $([ $fail -ne 0 ] && echo FAIL || { [ $unmeasured -ne 0 ] && echo 'INCOMPLETE (a measurement did not happen)' || echo PASS; })"
[ $fail -ne 0 ] && exit 1; [ $unmeasured -ne 0 ] && exit 2; exit 0
