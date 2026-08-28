#!/bin/zsh
# T346. The new reader forks an interpreter. Enumerate the verdict for every arm when that
# interpreter is ABSENT / BROKEN / SLOW, by rewriting the hard-coded `/usr/bin/python3` in a
# COPY of the shipped file. Nothing here touches the real file or the real lock.
# usage: t346-no-python.zsh <path-to-fire-program.sh>
emulate -L zsh
set -uo pipefail
FP="$1"
W="$(mktemp -d)"; S="$(mktemp -d)"; mkdir -p "$S/.softhouse"
H="$(hostname -s)"
NOW="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
OLD="$(date -u -r $(( $(date +%s) - 360000 )) +%Y-%m-%dT%H:%M:%SZ)"
sleep 300 & LIVE=$!
sleep 0.1 & DEAD=$!; wait $DEAD 2>/dev/null
trap "kill $LIVE 2>/dev/null; rm -rf $W $S" EXIT

# Variant 1: interpreter ABSENT. Only the reader's fork is redirected; the preflight's other
# python3 call sites are irrelevant because --lock-signals exits before the preflight.
sed 's#^  /usr/bin/python3 - "\$LOCK"#  /nonexistent/python3 - "$LOCK"#' "$FP" > "$W/absent.sh"
# Variant 2: interpreter present but EXITS NONZERO without reading (a broken install).
print -r -- '#!/bin/sh\nexit 127' > "$W/broken"; printf '#!/bin/sh\nexit 127\n' > "$W/broken"; chmod +x "$W/broken"
sed "s#^  /usr/bin/python3 - \"\\\$LOCK\"#  $W/broken - \"\$LOCK\"#" "$FP" > "$W/broken.sh"
# Variant 3: interpreter present but prints a spurious value on stdout and exits 0.
printf '#!/bin/sh\necho SPURIOUS\nexit 0\n' > "$W/liar"; chmod +x "$W/liar"
sed "s#^  /usr/bin/python3 - \"\\\$LOCK\"#  $W/liar - \"\$LOCK\"#" "$FP" > "$W/liar.sh"

for v in absent broken liar; do
  grep -q "$( [[ $v == absent ]] && print /nonexistent/python3 || print "$W/$v" )" "$W/$v.sh" \
    || { print -r -- "SUBSTITUTION FAILED for $v -- test is void"; exit 2; }
done

probe() {  # $1 variant  $2 label  $3 body  $4 correct
  printf '%s' "$3" > "$S/.softhouse/LOCK"
  local out verdict
  out="$(GEREGE_NBFI_REPO=$S zsh "$W/$1.sh" --lock-signals 2>&1)"
  verdict="$(print -r -- "$out" | grep '^verdict' | sed 's/verdict=//')"
  local sig="$(print -r -- "$out" | grep '^lock_present')"
  local dir="-"
  if [[ "$verdict" != "$4" ]]; then
    case "$verdict" in
      FREE-*|TAKE-*) dir="FAIL-OPEN(safety)" ;;
      HELD-*)        dir="fail-shut(liveness)" ;;
    esac
  else dir="unchanged"; fi
  printf '  %-14s want=%-15s got=%-15s %s\n' "$2" "$4" "$verdict" "$dir"
  printf '                 %s\n' "$sig"
}

for v in absent broken liar; do
  print -r -- "=== /usr/bin/python3 is: $v"
  probe $v "live-holder"  "{\"host\": \"$H\", \"pid\": $LIVE, \"started_at\": \"$NOW\"}"              HELD-default
  probe $v "released"     "{\"host\": \"$H\", \"pid\": $LIVE, \"started_at\": \"$NOW\", \"released_at\": \"$NOW\"}" FREE-released
  probe $v "dead-holder"  "{\"host\": \"$H\", \"pid\": $DEAD, \"started_at\": \"$NOW\"}"              TAKE-dead-pid
  probe $v "over-ceiling" "{\"host\": \"$H\", \"pid\": $LIVE, \"started_at\": \"$OLD\"}"              TAKE-ceiling
  print -r -- ""
done

print -r -- "=== timing: how long does one --lock-signals (4 field reads) take with the real interpreter?"
printf '{"host": "%s", "pid": %s, "started_at": "%s"}' "$H" "$LIVE" "$NOW" > "$S/.softhouse/LOCK"
s=$(date +%s%N 2>/dev/null || print 0)
for i in 1 2 3 4 5; do GEREGE_NBFI_REPO=$S zsh "$FP" --lock-signals >/dev/null 2>&1; done
e=$(date +%s%N 2>/dev/null || print 0)
print -r -- "  5 invocations, total ms: $(( (e - s) / 1000000 ))"
