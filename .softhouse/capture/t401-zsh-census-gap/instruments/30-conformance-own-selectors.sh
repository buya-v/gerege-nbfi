#!/usr/bin/env bash
# T401 / F-T385-4 -- THE TASK NAMED TWO CENSUSES. THERE ARE FOUR SELECTORS, AND TWO OF THEM
# ARE INSIDE conformance.sh ITSELF.
#
# F-T385-4 says "the fail-open and dead-path censuses read .sh and .py only". True, and both
# of those selectors live in files OWNED BY OTHER TASKS -- T238's linter and T316's census --
# so a conformance.sh patch alone would not fix them. While measuring that I found two MORE
# `.sh`/`.py`-only selectors, and these two are spelled IN conformance.sh, in the file this
# task may only patch by request:
#
#   S3  guard_no_host_state_in_lint_corpus   conformance.sh:2131
#         `git grep -l -E "$rw" -- '*.sh' '*.py'`     -> pin HOSTSTATE_PIN_TEMP_ASSIGN_LIST
#   S4  the guards-directory unwired-checker census   conformance.sh:3267-3269
#         `:(glob)<guards>/**/*.sh|*.py|*.go`         -> declared-rows table
#
# S3 is the same defect in the same family: it hunts a NAME=/tmp/... assignment inside
# repo-wide search instruments, and a repo-wide search instrument written in zsh is invisible
# to it for exactly the reason the fail-open linter is blind.
#
# This measures the cost of widening BOTH, so the request that follows is costed and not
# guessed. It only READS conformance.sh (to transliterate the two selectors); it never writes.
set -u
cd "$(git rev-parse --show-toplevel)" || exit 9

p() { printf '%s\n' "$*"; }

p "T401 -- conformance.sh's OWN TWO .sh/.py-ONLY SELECTORS"
p "commit : $(git rev-parse --short HEAD)"
p ""

# ---- S3: the host-state census, transliterated VERBATIM from conformance.sh:2122-2126 ----
rw='(git[[:space:]]+(-[A-Za-z][[:space:]]+[^[:space:]]+[[:space:]]+|--[A-Za-z-]+=[^[:space:]]+[[:space:]]+|-[A-Za-z]+[[:space:]]+)*(grep|ls-files)|grep[[:space:]]+-[a-zA-Z]*[rR])'
as='^[[:space:]]*(export[[:space:]]+)?[A-Za-z_][A-Za-z0-9_]*=["'"'"']?/(tmp|private/tmp|var/tmp)/'
self='.softhouse/capture/t238-failopen/instruments/50-failopen-lint.py'

# THE TRANSLITERATION IS ASSERTED, NOT ASSUMED. If these two regexes have drifted from what
# conformance.sh actually holds, every number below is about a different search (P-70). Both
# are byte-compared against the live file, and a miss is a refusal, never a zero.
CONF=".softhouse/conformance.sh"
if ! LC_ALL=C grep -qF "$rw" "$CONF"; then
  p "T401 ABORT (2): the host-state SEARCH regex is not byte-present in $CONF."
  p "T401 ABORT (2): the selector drifted; these figures would describe a different search."
  exit 2
fi
# The ASSIGNMENT regex cannot be byte-compared WHOLE: conformance.sh spells its embedded
# quote-class as `["'"'"']?` (shell single-quote gymnastics) and my copy expands to `["']?`,
# so the two are equal AS REGEXES and different AS BYTES. Comparing the whole string would
# refuse forever, and "assert something that always fails" degrades into "delete the assert".
# So the two halves that DO survive the quoting are compared, on either side of the class.
as_head='^[[:space:]]*(export[[:space:]]+)?[A-Za-z_][A-Za-z0-9_]*='
as_tail=']?/(tmp|private/tmp|var/tmp)/'
for frag in "$as_head" "$as_tail"; do
  if ! LC_ALL=C grep -qF "$frag" "$CONF"; then
    p "T401 ABORT (2): host-state ASSIGNMENT regex fragment not byte-present in $CONF:"
    p "T401 ABORT (2):   $frag"
    exit 2
  fi
done
p "== S3. HOST-STATE CENSUS (conformance.sh:2131) =="
p "   both regexes VERIFIED byte-present in $CONF"

base_pop="$(LC_ALL=C git grep -l -E "$rw" -- '*.sh' '*.py' | LC_ALL=C grep -vxF "$self" | LC_ALL=C sort)"
zsh_pop="$(LC_ALL=C git grep -l -E "$rw" -- '*.sh' '*.py' '*.zsh' | LC_ALL=C grep -vxF "$self" | LC_ALL=C sort)"
nb="$(printf '%s\n' "$base_pop" | LC_ALL=C grep -c '' || true)"
nz="$(printf '%s\n' "$zsh_pop"  | LC_ALL=C grep -c '' || true)"
p "   population (repo-wide search instruments)   base $nb   +zsh $nz"
p "   .zsh files that ARE repo-wide search instruments:"
printf '%s\n' "$zsh_pop" | LC_ALL=C grep '\.zsh$' | sed 's/^/     /' || p "     (none)"

# The census itself, on each population.
printf '%s\n' "$base_pop" >/dev/null
b_rows="$(LC_ALL=C git grep -n -E "$as" -- '*.sh' '*.py' | LC_ALL=C grep -c '' || true)"
z_rows="$(LC_ALL=C git grep -n -E "$as" -- '*.sh' '*.py' '*.zsh' | LC_ALL=C grep -c '' || true)"
p "   NOTE: the figures below are the census over the WHOLE extension set, not the"
p "   population-restricted set conformance.sh uses; the population-restricted delta is"
p "   printed under it and is the one that matters."
p "   raw NAME=/tmp assignment lines   base $b_rows   +zsh $z_rows"

zonly="$(printf '%s\n' "$zsh_pop" | LC_ALL=C grep '\.zsh$' || true)"
if [ -n "$zonly" ]; then
  newrows="$(printf '%s\n' "$zonly" | while IFS= read -r f; do
      [ -n "$f" ] || continue
      LC_ALL=C git grep -n -E "$as" -- "$f" || true
    done)"
  n="$(printf '%s\n' "$newrows" | LC_ALL=C grep -c '' || true)"
  [ -n "$newrows" ] || n=0
  p "   NEW HOSTSTATE ROWS the pin would have to absorb : $n"
  [ -n "$newrows" ] && printf '%s\n' "$newrows" | sed 's/^/     + /'
else
  p "   NEW HOSTSTATE ROWS the pin would have to absorb : 0 (no .zsh is a search instrument)"
fi
p ""

# ---- S4: the guards-directory unwired-checker census ----
p "== S4. GUARDS-DIRECTORY UNWIRED-CHECKER CENSUS (conformance.sh:3267-3269) =="
gd=".softhouse/guards"
for ext in sh py go zsh; do
  n="$(git ls-files -- ":(glob)$gd/**/*.$ext" ":(glob)$gd/*.$ext" | LC_ALL=C grep -c '' || true)"
  p "   tracked *.$ext under $gd (any depth) : $n"
done
p "   => widening S4 to .zsh costs ZERO rows today, and is pure insurance."
p ""
p "== WHERE EACH OF THE FOUR SELECTORS LIVES =="
p "   S1 fail-open  .softhouse/capture/t238-failopen/instruments/50-failopen-lint.py:210-211"
p "   S2 dead-path  .softhouse/capture/t316-dead-path-guards/census_dead_paths.py:110"
p "   S3 host-state .softhouse/conformance.sh:2131            <- IN conformance.sh"
p "   S4 guards-dir .softhouse/conformance.sh:3267-3269       <- IN conformance.sh"
p "   S1 and S2 are outside this task's grant AND outside conformance.sh. A conformance.sh"
p "   patch cannot fix them; it can only stop conformance.sh from PRINTING a claim about"
p "   coverage those two selectors do not have."
