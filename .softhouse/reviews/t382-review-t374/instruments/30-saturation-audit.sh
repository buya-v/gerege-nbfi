#!/bin/bash
# T382 — is the SATURATION defect gone, or only gone at the one call site T362 named?
#
# T362's defect: section 4 is adjudicated RC 1, so an extra failure inside it cannot move the
# section and the aggregate cannot see it. T374 split the out/req integrity arm into section 10
# (adjudicated GREEN). But section 4 still carries FOUR OTHER live arms, and its adjudicated RC
# is still 1. This drives the question rather than arguing it.
#
# All work happens in /tmp/t382-pin, a throwaway clone at the T374 MERGE RESULT.
set -u
# HOST STATE IS A PARAMETER, NOT A LITERAL (guard_no_host_state_in_lint_corpus).
# A /tmp path assigned to a name in a tracked instrument is shared across worktrees,
# absent from every commit and deleted on reboot. Supply them:
#   T382_CLONE=<throwaway clone> T382_OUT=<scratch dir> bash <this script>
# The committed transcripts were produced with T382_OUT=/tmp/t382-out and the clone
# named in each transcript's first line.
SC="${T382_CLONE:?set T382_CLONE to a throwaway clone of this repo}"
O="${T382_OUT:?set T382_OUT to a scratch output directory}"
CAP=".softhouse/capture/tierA-a2"
FORK=12a7f8d9a3af4665fd5281a9f9c001d4f1276a53
mkdir -p "$O"

git -C "$SC" checkout -q pinmerge
git -C "$SC" reset --hard -q HEAD
git -C "$SC" clean -fdq
echo "at: $(git -C "$SC" log --oneline -1)"

echo
echo "### A. WHICH pre-existing files does section 4 guard that section 10 does NOT?"
git -C "$SC" show "$FORK:$CAP/MANIFEST.sha256" | grep -v '^#' | awk 'NF==2{print $2}' | sed 's/^\*//' | sort > "$O/man430.txt"
grep -vE '^(out|req)/' "$O/man430.txt" > "$O/man430-nonobs.txt"
echo "  entries in the fork-sha manifest      : $(wc -l < "$O/man430.txt" | tr -d ' ')"
echo "  of those, under out/ or req/ (sec 10) : $(grep -cE '^(out|req)/' "$O/man430.txt")"
echo "  NOT under out/ or req/ (sec 4 ONLY)   : $(wc -l < "$O/man430-nonobs.txt" | tr -d ' ')"
cat "$O/man430-nonobs.txt"

echo
echo "### B. CONTROL — unmutated merge result"
( cd "$SC" && bash .softhouse/reviews/A2-11/run-all.sh ) > "$O/sat-00-control.txt" 2>&1
echo "  run-all EXIT=$?"
grep -E '^  (4|10) ' "$O/sat-00-control.txt"
grep 'RUN-ALL VERDICT' "$O/sat-00-control.txt"
git -C "$SC" checkout -q -- .

echo
echo "### C. DRIVE — mutate a pre-existing capture INSTRUMENT (not an observation)."
TARGET="$CAP/mkreq7.py"
if ! grep -qx "$(basename "$TARGET")" "$O/man430-nonobs.txt"; then
  TARGET="$CAP/$(head -1 "$O/man430-nonobs.txt")"
fi
echo "  target: $TARGET"
printf '\n# T382-SATURATION-PROBE appended byte\n' >> "$SC/$TARGET"
( cd "$SC" && python3 .softhouse/reviews/A2-11/verify-manifest-independently.py ) > "$O/sat-01-sec4-only.txt" 2>&1
echo "  section 4 alone EXIT=$?  (adjudicated 1 -> cannot move)"
grep -E 'DIFF |byte-identical|DIFFER|MANIFEST MISMATCH' "$O/sat-01-sec4-only.txt" | head -8
( cd "$SC" && python3 .softhouse/reviews/A2-11/verify-capture-integrity.py ) > "$O/sat-02-sec10-only.txt" 2>&1
echo "  section 10 alone EXIT=$?  (does the NEW guard see it?)"
tail -3 "$O/sat-02-sec10-only.txt"
( cd "$SC" && bash .softhouse/reviews/A2-11/run-all.sh ) > "$O/sat-03-runall-mutated-instrument.txt" 2>&1
echo "  run-all EXIT=$?"
grep -E '^  (4|10) ' "$O/sat-03-runall-mutated-instrument.txt"
grep -E 'sections run|RUN-ALL VERDICT' "$O/sat-03-runall-mutated-instrument.txt"
git -C "$SC" checkout -q -- .

echo
echo "### D. DRIVE — LAUNDER: mutate the instrument AND update MANIFEST.sha256 to match"
printf '\n# T382-LAUNDER appended byte\n' >> "$SC/$TARGET"
python3 - "$SC" "$TARGET" <<'PY'
import hashlib, os, sys
root, rel = sys.argv[1], sys.argv[2]
name = rel[len('.softhouse/capture/tierA-a2/'):]
man = os.path.join(root, '.softhouse/capture/tierA-a2/MANIFEST.sha256')
h = hashlib.sha256(open(os.path.join(root, rel), 'rb').read()).hexdigest()
lines = open(man).read().split('\n'); out = []; hit = 0
for L in lines:
    p = L.split(None, 1)
    if len(p) == 2 and p[1].lstrip('*').strip() == name:
        out.append(h + '  ' + p[1]); hit += 1
    else:
        out.append(L)
open(man, 'w').write('\n'.join(out))
print('  manifest rows rewritten:', hit)
PY
( cd "$SC" && bash .softhouse/reviews/A2-11/run-all.sh ) > "$O/sat-04-runall-laundered.txt" 2>&1
echo "  run-all EXIT=$?"
grep -E '^  (4|10) ' "$O/sat-04-runall-laundered.txt"
grep -E 'sections run|RUN-ALL VERDICT' "$O/sat-04-runall-laundered.txt"
git -C "$SC" checkout -q -- .

echo
echo "### E. DRIVE — an UNTRACKED fabricated observation dropped into out/"
printf 'HTTP/1.1 200 OK\r\n\r\n{\"fabricated\":true}\n' > "$SC/$CAP/out/A2-999-T382-UNTRACKED.http"
( cd "$SC" && bash .softhouse/reviews/A2-11/run-all.sh ) > "$O/sat-05-runall-untracked.txt" 2>&1
echo "  run-all EXIT=$?"
grep -E '^  (4|10) ' "$O/sat-05-runall-untracked.txt"
grep -E 'sections run|RUN-ALL VERDICT' "$O/sat-05-runall-untracked.txt"
rm -f "$SC/$CAP/out/A2-999-T382-UNTRACKED.http"
git -C "$SC" checkout -q -- .

echo
echo "### F. CONTROL AGAIN — same command, unmutated"
( cd "$SC" && bash .softhouse/reviews/A2-11/run-all.sh ) > "$O/sat-06-control-again.txt" 2>&1
echo "  run-all EXIT=$?"
grep -E 'sections run|RUN-ALL VERDICT' "$O/sat-06-control-again.txt"
git -C "$SC" checkout -q -- .

echo
echo "### G. is any section OTHER than 4 adjudicated non-zero, and is it live or frozen?"
grep -nE '^  sec [0-9]+ ' "$SC/.softhouse/reviews/A2-11/run-all.sh"
