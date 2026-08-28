#!/bin/zsh
# T353 — "a RED for the wrong reason is not a pass." `red-drives.zsh` reports rc only; this
# prints the last lines of the --probe transcript for the two interpreter mutations, so the
# refusal can be attributed to the guard that is supposed to have fired and not to something
# unrelated exiting 2 earlier in the preflight.
# usage: why-red.zsh <path-to-fire-program.sh>
emulate -L zsh
set -uo pipefail
FP="${1:?usage: why-red.zsh <fire-program.sh>}"; FP="${FP:A}"
HERE="${0:A:h}"
W="$(mktemp -d "${TMPDIR:-/tmp}/t353why.XXXXXX")"; trap "rm -rf $W" EXIT

printf '#!/bin/sh\necho SPURIOUS\nexit 0\n' > "$W/liar"; chmod +x "$W/liar"

for v in absent liar; do
  cp "$FP" "$W/$v.sh"
  if [[ $v == absent ]]; then
    sed -i '' 's|/usr/bin/python3|/nonexistent/python3|g' "$W/$v.sh"
    grep -q '/nonexistent/python3' "$W/$v.sh" || { print -r -- "SUBSTITUTION FAILED for $v -- VOID"; exit 2; }
  else
    sed -i '' "s|/usr/bin/python3|$W/liar|g" "$W/$v.sh"
    grep -q "$W/liar" "$W/$v.sh" || { print -r -- "SUBSTITUTION FAILED for $v -- VOID"; exit 2; }
  fi
  print -r -- "=== variant: /usr/bin/python3 is $v"
  zsh "$HERE/probe-scratch.zsh" "$W/$v.sh" > "$W/$v.log" 2>&1
  print -r -- "    PROBE_EXIT=$(sed -n 's/^PROBE_EXIT=//p' "$W/$v.log")"
  print -r -- "    last 3 lines:"
  grep -v '^$' "$W/$v.log" | tail -3 | sed 's/^/      /'
  print -r -- ""
done
