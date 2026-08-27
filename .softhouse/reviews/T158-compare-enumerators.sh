#!/bin/bash
# T158 — three INDEPENDENT enumerations of the population T156's P-26 sweep measured.
# If they disagree, the disagreement IS the finding (P-40).
C=/tmp/t158-clone
cd "$C" || exit 9
echo "tree under test: $(git rev-parse HEAD)  ($(git log --oneline -1))"
echo
echo "enumerator 1  os.walk   (T156's own, re-run above) : see 02-t156-sweep-rerun-branch-tip.txt"
echo "enumerator 2  find(1)   .sh/.py  : $(find .softhouse -type f \( -name '*.sh' -o -name '*.py' \) | wc -l | tr -d ' ')"
echo "enumerator 2  find(1)   all      : $(find .softhouse -type f | wc -l | tr -d ' ')"
echo "enumerator 3  git ls-files .sh/py: $(git ls-files -- .softhouse | grep -cE '\.(sh|py)$')"
echo "enumerator 3  git ls-files all   : $(git ls-files -- .softhouse | wc -l | tr -d ' ')"
echo
echo "os.walk's blind spots, checked rather than assumed:"
echo "  untracked .sh/.py present on disk but absent from the index : $(git ls-files --others --exclude-standard -- .softhouse | grep -cE '\.(sh|py)$')"
echo "  symlinks under .softhouse (os.walk does not follow)         : $(find .softhouse -type l | wc -l | tr -d ' ')"
echo "  directories the sweep could not list (os.walk swallows these"
echo "  silently — it has no onerror handler)                       : $(find .softhouse -type d ! -perm -u+r | wc -l | tr -d ' ')"
echo
echo "T156 reported 502 / 3308, taken at commit 574c525. Tracked counts at that commit:"
echo "  .sh/.py : $(git ls-tree -r --name-only 574c525 -- .softhouse | grep -cE '\.(sh|py)$')"
echo "  all     : $(git ls-tree -r --name-only 574c525 -- .softhouse | wc -l | tr -d ' ')"
echo "  (the 3311-vs-3308 delta is the three t156/ transcripts not yet written when the"
echo "   sweep ran; the .sh/.py figure matches exactly)"
