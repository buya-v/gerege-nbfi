#!/bin/sh
# T99 — SWEEP FOR THE SAME SHAPE ELSEWHERE (P-12: a right fix in one place recurs everywhere the
# claim is restated).  Four defect shapes, each searched for across the whole Path B tree, and each
# reported with what the search CANNOT find.
#
# Every grep here is LC_ALL=C.  A BSD grep in a UTF-8 locale matches NOTHING in a file containing an
# invalid multibyte sequence AND RETURNS 0 — a silent zero that has already produced one
# "right numbers, wrong reason" result in this run.  `-a` alone does not fix it; the locale does.
set -u
T99=$(cd "$(dirname "$0")" && pwd)
W=$(cd "$T99/.." && pwd)
cd "$W"

hr() { echo; echo "=== $1"; }

hr "0. locale sanity — are there files here that would make a UTF-8 grep go silently blind?"
n=0
for f in $(LC_ALL=C find . -type f \( -name '*.sh' -o -name '*.py' -o -name '*.txt' -o -name '*.md' \) | sort); do
  if ! LC_ALL=en_US.UTF-8 grep -qa '' "$f" 2>/dev/null; then
    echo "  INVALID-MULTIBYTE (UTF-8 grep would return 0 lines here): $f"
    n=$((n+1))
  fi
done
echo "  files where a UTF-8 grep would go blind: $n"
echo "  (every grep below is LC_ALL=C, so this number does not change what the sweep can see)"

echo
echo "NOTE: greps 1-3 exclude t99/ itself.  This task's own proof scripts quote the defective"
echo "idioms verbatim in their headers, and a hit list dominated by the report about the defect"
echo "is not a hit list.  t99/ is syntax-checked and reviewed separately."

hr "1. basename-only comparisons — the F-1 shape"
echo "--- shell: basename used in a comparison rather than for display"
LC_ALL=C grep -rn 'basename' --include='*.sh' --exclude-dir=t99 . | sed 's|^\./||'
echo "--- python: os.path.basename feeding a name test"
LC_ALL=C grep -rn 'os.path.basename\|\.endswith(.-.\s*+\|realpath\|normpath' --include='*.py' --exclude-dir=t99 . | sed 's|^\./||'
echo "--- any other place a tenant id is compared against a path fragment"
LC_ALL=C grep -rn 'TENANT\"\?\s*)\|\*-\"\$TENANT\|-. + TENANT' --include='*.sh' --include='*.py' --exclude-dir=t99 . | sed 's|^\./||'

hr "2. tools resolved through \$PATH — the F-2 shape"
echo "--- digest tools"
LC_ALL=C grep -rn 'shasum\|sha256sum\|openssl dgst\|md5' --include='*.sh' --include='*.py' --exclude-dir=t99 . | sed 's|^\./||'
echo
echo "--- OTHER unpinned externals in the two scripts that decide whether a capture is admissible"
echo "    (reported, not fixed: see the handoff.  A poisoned \`docker\` defeats P1-P3 and P5-P13;"
echo "     a poisoned \`curl\` defeats P4 and the canary.  Both are far larger jobs than the digest"
echo "     pin, and neither is what T85 raised.)"
for tool in docker curl psql grep sed awk tr cut head unzip javap; do
  c=$(LC_ALL=C grep -c "\\b$tool\\b" t36/preconditions.sh t36/recapture.sh 2>/dev/null | LC_ALL=C awk -F: '{s+=$2} END {print s+0}')
  [ "$c" -gt 0 ] && printf '    %-8s %s occurrence(s) in preconditions.sh + recapture.sh\n' "$tool" "$c"
done
echo "    attest.py computes its digests with hashlib IN PROCESS, so it is not PATH-reachable at all."

hr "3. checks that can pass on an empty input set — the F-3 shape"
echo "--- loops over a glob with a [ -f ] || continue and no counter"
LC_ALL=C grep -rn 'for f in .*\*\|for d in .*\*\|glob(' --include='*.sh' --include='*.py' --exclude-dir=t99 . | sed 's|^\./||'
echo
echo "--- grep -c / wc -l results compared to 0 (a zero can mean 'clean' or 'read nothing')"
LC_ALL=C grep -rn 'grep -c\|grep -ac\|wc -l' --include='*.sh' --exclude-dir=t99 . | sed 's|^\./||'

hr "4. capture directories with no in-band provenance — the F-4 shape"
python3 - <<'EOF'
import json, os
root = os.getcwd()
idx = json.load(open(os.path.join(root, 'PROVENANCE-INDEX.json')))
rows = idx['directories']
print('  %-42s %-9s %-8s %s' % ('directory', 'stamp', 'tier-A', 'tenant'))
for r in rows:
    a = 'yes' if any(e['tier'] == 'A' for e in r['evidence']) else 'NO'
    print('  %-42s %-9s %-8s %s' % (r['path'], r['in_band_stamp'] or '-', a,
                                    r['tenant'] or 'NOT ESTABLISHED'))
print('  totals: %d directories, %d stamped, %d with tier-A evidence, %d with no tenant established'
      % (len(rows),
         sum(1 for r in rows if r['in_band_stamp']),
         sum(1 for r in rows if any(e['tier'] == 'A' for e in r['evidence'])),
         sum(1 for r in rows if not r['tenant'])))
EOF

hr "WHAT THIS SWEEP CANNOT FIND"
cat <<'EOF'
  * Anything outside .softhouse/capture/pathb/.  The sweep is scoped to this tree; sibling capture
    trees (.softhouse/capture/audit-t44/ is owned by another worker this fire) were not searched.
  * A basename comparison written some other way — `${x##*/}`, `awk -F/ '{print $NF}'`, a Python
    `split('/')[-1]`.  Greps 1 finds the idioms actually used here; it does not bound the space.
  * A tool invoked through a variable (`$DOCKER`, `$PY`) or through a shell function, since the
    literal name never appears at the call site.
  * A vacuous check whose emptiness comes from something other than a glob — an empty SQL result,
    an empty JSON array, a `for` over an unset variable.
  * Whether a capture's recorded tenant is TRUE.  The index records what the evidence says and what
    tier it is; it cannot promote tier-B prose into an observation, and it does not try.
EOF
