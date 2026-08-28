#!/usr/bin/env bash
# T401 / F-T385-4 -- RE-MEASURE THE FOUR COUNTS.
#
# T385's prose gives: 110 tracked .zsh, 98 of them under capture/ and reviews/, 626 .sh,
# 722 .py, corpus 1348. The bar today prints corpus=1395. P-86: a number restated in prose
# is the class that rots; re-measure and PRINT THE SELECTOR beside every figure (P-70).
#
# TWO DIFFERENT POPULATIONS ARE INVOLVED AND THEY ARE NOT THE SAME SET:
#   FAILOPEN corpus  = git ls-files (WHOLE REPO), filtered f.endswith((".sh",".py"))
#                      [.softhouse/capture/t238-failopen/instruments/50-failopen-lint.py:211]
#   DEADPATH corpus  = git ls-files '.softhouse/*.py' '.softhouse/*.sh'  -- .softhouse ONLY
#                      [.softhouse/capture/t316-dead-path-guards/census_dead_paths.py:110]
# git pathspec without ':(glob)' magic uses wildmatch WITHOUT FNM_PATHNAME, so '*' crosses
# '/' and '.softhouse/*.py' is ANY DEPTH. That is asserted in section D, not assumed.
set -u
cd "$(git rev-parse --show-toplevel)" || exit 9

p() { printf '%s\n' "$*"; }

p "T401 COUNT MEASUREMENT -- $(git rev-parse --short HEAD) $(date -u +%Y-%m-%dT%H:%M:%SZ)"
p "repo root : $(pwd)"
p ""
p "== A. WHOLE-REPO TRACKED FILES BY EXTENSION (selector: git ls-files | grep -c) =="
tot="$(git ls-files | LC_ALL=C grep -c '' || true)"
p "  tracked files, all                                      : $tot"
for e in sh py zsh go bash; do
  n="$(git ls-files | LC_ALL=C grep -c "\\.${e}\$" || true)"
  p "  tracked *.${e}                                            : $n"
done
p ""
p "== B. .zsh BREAKDOWN (whole repo, tracked) =="
git ls-files | LC_ALL=C grep '\.zsh$' > /tmp/t401-zsh-list.txt || true
zn="$(LC_ALL=C grep -c '' /tmp/t401-zsh-list.txt || true)"
p "  tracked .zsh, whole repo                                : $zn"
for d in .softhouse/capture/ .softhouse/reviews/ .softhouse/handoff/ .softhouse/guards/ .softhouse/bin/ .softhouse/hooks/; do
  n="$(LC_ALL=C grep -c "^$d" /tmp/t401-zsh-list.txt || true)"
  p "  ...under $d : $n"
done
n="$(LC_ALL=C grep -cE '^\.softhouse/(capture|reviews)/' /tmp/t401-zsh-list.txt || true)"
p "  ...under capture/ OR reviews/ (T385's '98')             : $n"
n="$(LC_ALL=C grep -c '^\.softhouse/' /tmp/t401-zsh-list.txt || true)"
p "  ...under .softhouse/ at any depth                       : $n"
n="$(LC_ALL=C grep -vc '^\.softhouse/' /tmp/t401-zsh-list.txt || true)"
p "  ...OUTSIDE .softhouse/                                  : $n"
p ""
p "== C. THE TWO CENSUS POPULATIONS AS THE INSTRUMENTS ACTUALLY SPELL THEM =="
# ERE, NOT BRE. `grep -c '\.sh$\|\.py$'` returned 738 (the .py count ALONE) under the
# /usr/bin/grep this script gets in a non-interactive bash, while the SAME pattern returned
# 1395 under the interactive zsh's grep. A BRE `\|` that silently drops a branch is a
# measuring instrument that UNDERCOUNTS AND EXITS 0 -- the fail-open shape, in the tool
# built to measure fail-opens. Every alternation here is `-E` and every count is asserted
# against its parts in 20-assert-counts.sh.
n="$(git ls-files | LC_ALL=C grep -cE '\.(sh|py)$' || true)"
p "  FAILOPEN corpus  git ls-files, endswith .sh/.py (repo)  : $n"
n="$(git ls-files | LC_ALL=C grep -cE '\.(sh|py|zsh)$' || true)"
p "  FAILOPEN corpus IF .zsh were added                      : $n"
n="$(git ls-files '.softhouse/*.py' '.softhouse/*.sh' | LC_ALL=C grep -c '' || true)"
p "  DEADPATH corpus  git ls-files '.softhouse/*.py' '*.sh'  : $n"
n="$(git ls-files '.softhouse/*.py' '.softhouse/*.sh' '.softhouse/*.zsh' | LC_ALL=C grep -c '' || true)"
p "  DEADPATH corpus IF .zsh were added                      : $n"
p ""
p "== D. PATHSPEC DEPTH ASSERTION (is '*' crossing '/' in the deadpath selector?) =="
a="$(git ls-files '.softhouse/*.py' | LC_ALL=C grep -c '/' || true)"
b="$(git ls-files '.softhouse/*.py' | LC_ALL=C grep -c '^\.softhouse/[^/]*$' || true)"
p "  rows containing '/'                                     : $a"
p "  rows at depth 1 (.softhouse/X.py, no deeper)            : $b"
if [ "$a" -gt "$b" ]; then p "  => '*' DOES cross '/': the selector is ANY-DEPTH."; else p "  => depth-1 only."; fi
p ""
p "== E. THE TWO SELECTORS ARE SPELLED DIFFERENTLY; THE OVERLAP IS ASSERTED, NOT ARGUED =="
p "  failopen : PYTHON f.endswith(('.sh', '.py')) over unfiltered \`git ls-files\`."
p "  deadpath : a GIT PATHSPEC, wildmatch, no ':(glob)' magic (see D)."
p "  A '.zsh' name ends in 'sh' but NOT in '.sh', so neither selector reaches it today."
p "  NO EXAMPLE PATH IS SPELLED IN THIS COMMENT. An illustrative fake path in a tracked"
p "  instrument is a DEAD-PATH ROW: the first draft of this file wrote one and moved"
p "  deadOccurrences 108 -> 109 by itself. The census does not know prose from intent."
p "  ASSERTED instead, by running it:"
n="$(git ls-files '.softhouse/*.sh' | LC_ALL=C grep -c '\.zsh$' || true)"
p "    rows ending .zsh returned by the '.softhouse/*.sh' pathspec : $n  (must be 0)"
p ""
p "== F. .zsh FILE LIST (whole repo, tracked) =="
cat /tmp/t401-zsh-list.txt
