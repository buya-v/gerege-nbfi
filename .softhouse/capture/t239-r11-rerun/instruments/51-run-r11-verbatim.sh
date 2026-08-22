#!/usr/bin/env bash
# T239 — run the FROZEN instrument .softhouse/reviews/T138-evidence/r11-hygiene.sh UNMODIFIED,
# through the route that actually invokes it, and capture what an operator would have read.
#
# The script itself is NOT edited: T138's review evidence is frozen (T114/T176) and T239's scope
# is report-don't-fix. This wrapper only invokes it and annotates the output.
set -u
R="${1:?repo}"
S="$R/.softhouse/reviews/T138-evidence/r11-hygiene.sh"
echo "instrument under test : .softhouse/reviews/T138-evidence/r11-hygiene.sh"
echo "blob sha              : $(cd "$R" && git hash-object .softhouse/reviews/T138-evidence/r11-hygiene.sh)"
echo "shebang               : $(head -1 "$S")"
echo "invoked as            : bash <script> <repo>"
echo "repo argument         : $R"
echo "does /tmp/T138-merge exist? -> $([ -d /tmp/T138-merge ] && echo YES || echo 'NO - section 4 will cd-fail')"
echo
echo "############### BEGIN VERBATIM OUTPUT ###############"
bash "$S" "$R" 2>&1
rc=$?
echo "############### END VERBATIM OUTPUT (exit=$rc) ###############"
echo
echo "ANNOTATIONS:"
echo " * Section 2's first sub-check printed NO hit lines, then its own reassurance"
echo "   '(nothing above, or only prose, = clean)'. Measured truth for that population:"
echo "   38 hit lines exist (git grep -P, BSD grep -E and python3 re all agree)."
echo " * Section 4 printed '(searched the MERGED tree)' with nothing above it, because"
echo "   'cd /tmp/T138-merge 2>/dev/null && git grep ...' short-circuited on a missing"
echo "   directory. The echo on the next line is UNCONDITIONAL. Fail-OPEN."
echo " * Script exit code was $rc."
