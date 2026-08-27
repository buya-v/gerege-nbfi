#!/bin/sh
# T138 — hygiene checks: additivity, immutable baselines (P-24), LC_ALL=C grep -a
# integrity (P-33), and the known leftover in T91.md.
set -u
R=${1:?repo}
cd "$R" || exit 2
T91=ccf3c14171dea52bd044d81d5ca67aba8054b74c
T115=bd59187cf83c7c7161db23668e91d45bd46be2a8

echo "=================================================================="
echo "1. ADDITIVITY — did T115 modify any of T91's own out/ transcripts?"
echo "=================================================================="
echo "files T115 changed under .softhouse/capture/t91/out/ that are NOT t115-*:"
git diff --name-status "$T91" "$T115" -- .softhouse/capture/t91/out/ \
  | LC_ALL=C grep -av 't115-' | sed 's/^/   /'
echo "   (only GUARDS-RED.txt / new files expected above)"
echo
echo "modified (M) files in the whole T115-vs-T91 diff:"
git diff --name-status "$T91" "$T115" | LC_ALL=C grep -a '^M' | sed 's/^/   /'
echo
echo "T91's four transcript dirs — blob identity T91 vs T115:"
for d in prefix-copy-sh prefix-copy-bash prefix-livetwin-sh prefix-livetwin-bash \
         postfix-copy-sh postfix-copy-bash postfix-livetwin-sh postfix-livetwin-bash happy; do
  a=$(git ls-tree "$T91"  ".softhouse/capture/t91/out/$d" | awk '{print $3}')
  b=$(git ls-tree "$T115" ".softhouse/capture/t91/out/$d" | awk '{print $3}')
  s='*** DIFFERS ***'; [ "$a" = "$b" ] && s=IDENTICAL
  printf '   %-26s %s  %s\n' "$d" "$(echo "$a" | cut -c1-12)" "$s"
done
echo

echo "=================================================================="
echo "2. BASELINES — every baseline in T115's scripts must be a LITERAL sha"
echo "=================================================================="
echo "--- any use of a ref computed from main (P-24's exact trap):"
git grep -n -a -E 'merge-base|main:|origin/main|rev-parse main|\bmain\b' "$T115" -- \
  .softhouse/capture/t91/ .softhouse/capture/charges/bin/preconditions.sh \
  .softhouse/capture/audit-t44/charges/bin/preconditions-COPY.sh | sed 's/^/   /'
echo "   (nothing above, or only prose, = clean)"
echo
echo "--- literal 40-hex shas and blob ids used as baselines:"
git grep -n -a -E '[0-9a-f]{40}' "$T115" -- .softhouse/capture/t91/*.sh | sed 's/^/   /'
echo
echo "--- git revisions each T115 script actually resolves:"
for f in t115-drive-mf1.sh t115-drive-mf2.sh t115-drive-mf3-mf4.sh t115-rerun-attacks.sh prove-guards.sh; do
  echo "   -- $f"
  git show "$T115:.softhouse/capture/t91/$f" | LC_ALL=C grep -n -aE 'git (archive|show|cat-file|rev-parse)' | sed 's/^/      /'
done
echo

echo "=================================================================="
echo "3. LC_ALL=C grep -a INTEGRITY (P-33) — T115 must not have weakened it"
echo "=================================================================="
for f in verdict.sh run-attacks.sh shell-invariance.sh prove-guards.sh; do
  a=$(git show "$T91:.softhouse/capture/t91/$f"  2>/dev/null | LC_ALL=C grep -ac 'LC_ALL=C')
  b=$(git show "$T115:.softhouse/capture/t91/$f" 2>/dev/null | LC_ALL=C grep -ac 'LC_ALL=C')
  c=$(git show "$T91:.softhouse/capture/t91/$f"  2>/dev/null | LC_ALL=C grep -ac 'grep -a')
  d=$(git show "$T115:.softhouse/capture/t91/$f" 2>/dev/null | LC_ALL=C grep -ac 'grep -a')
  printf '   %-22s LC_ALL=C: %2s -> %2s     grep -a: %2s -> %2s\n' "$f" "$a" "$b" "$c" "$d"
done
echo
echo "--- any BARE grep (no LC_ALL=C, no -a) on a transcript, in the T115 rig:"
for f in verdict.sh run-attacks.sh shell-invariance.sh prove-guards.sh; do
  git show "$T115:.softhouse/capture/t91/$f" | LC_ALL=C grep -n -a 'grep' | LC_ALL=C grep -av 'LC_ALL=C' | sed "s|^|   $f:|"
done
echo
echo "--- the two comments T115 marked 'under adjudication by T108':"
git show "$T115:.softhouse/capture/t91/verdict.sh" | LC_ALL=C grep -n -a 'ADJUDICATION BY T108\|adjudication by T108' | sed 's/^/   verdict.sh:/'
git show "$T115:.softhouse/capture/t91/prove-guards.sh" | LC_ALL=C grep -n -a 'adjudication by T108' | sed 's/^/   prove-guards.sh:/'
echo

echo "=================================================================="
echo "4. THE KNOWN LEFTOVER — T91.md:8"
echo "=================================================================="
git show "$T115:.softhouse/handoff/2026-08-17-run1-harness-schedule-poc/T91.md" | sed -n '1,12p' | cat -n | sed 's/^/   /'
echo
echo "--- every other restatement of '17 capture scripts' anywhere in the merged tree:"
cd /tmp/T138-merge 2>/dev/null && \
  git grep -n -a -E '17 capture scripts|17 callers|seventeen capture' -- . | sed 's/^/   /'
echo "   (searched the MERGED tree)"
