#!/usr/bin/env bash
# T411 item 3: enumerate EVERY selector in this repo that builds a corpus from
# file extensions, and separate the LIVE ones (a graded bar figure depends on
# them) from the DORMANT ones (a closed task's local instrument).
#
# T401 named four. This asks the question two ways so a miss in one shows in the
# other:
#   (A) every external script conformance.sh EXECUTES, then that script's corpus
#       selector -- catches a live census whose selector is not in conformance.sh
#   (B) every extension-shaped selector anywhere in the tracked corpus -- catches
#       a census that (A) would miss because it is reached indirectly
set -uo pipefail
GREP=/usr/bin/grep
CS=.softhouse/conformance.sh

echo "############ A. EXTERNAL SCRIPTS conformance.sh EXECUTES ############"
echo "selector: lines assigning or invoking a path under .softhouse/ ending .py/.sh,"
echo "          minus comment lines and minus the pin/table literals."
echo
# every .py/.sh path literal in conformance.sh, with the line, excluding pure-comment lines
$GREP -nE '\$REPO_ROOT/\.softhouse/[A-Za-z0-9_./-]+\.(py|sh)' "$CS" \
  | $GREP -vE '^[0-9]+:[[:space:]]*#' \
  | sed -E 's/^([0-9]+):[[:space:]]*/\1  /' | sort -u
echo
echo "-- of those, which are actually RUN (python3/bash/exec/\$( ) invocation) --"
$GREP -nE '(python3|bash|/usr/bin/env)[[:space:]]+"?\$(\{)?(lint|chk|rig|census|cen|probe|regen)' "$CS" | head -20
echo
echo "############ B. EVERY EXTENSION-SHAPED CORPUS SELECTOR, WHOLE TREE ############"
echo "selector: tracked *.sh/*.py/*.zsh, lines where an extension list meets a"
echo "          corpus builder (ls-files | git grep -- | --include | glob | endswith | find -name)"
echo
git grep -nE "endswith\(\(|ls-files[^|]*\*\.|git grep[^|]*-- *'\*\.|--include=?'?\*\.|:\(glob\)|-name *'\*\." \
   -- '*.sh' '*.py' '*.zsh' 2>/dev/null \
 | $GREP -E "\.(sh|py|go|zsh|bash)['\")]" \
 | sed -E 's/^([^:]+):([0-9]+):[[:space:]]*/\1:\2  /' \
 | sort
echo
echo "############ C. DOES THE SELECTOR ALREADY REACH .zsh? ############"
echo "any selector in the tree that ALREADY names .zsh (precedent):"
git grep -nE "['\"]\.?zsh['\"]|\*\.zsh" -- '*.sh' '*.py' 2>/dev/null \
 | $GREP -E "endswith|ls-files|git grep|--include|glob|-name" | sort
