#!/bin/zsh
# T353 / CONDITION 1 -- THE DECISIVE RUN, executed INSIDE a Linux container against the
# REAL wrapper via `--lock-signals`. Not a re-implementation and not a reading of the source.
#
# What it asks: on a non-BSD host, does `lock_started_age` read anything at all, and can
# arms 3 (CEILING) and 5 (both-stale) fire?
#
# Correct answers, in the same shape T346's census uses:
#   C01 live holder, started_at 100 h old   -> TAKE-ceiling   (arm 3). Anything else = FAIL-SHUT.
#   C02 same, compact separators            -> TAKE-ceiling   (arm 3).
#   D01 released_at a real UTC timestamp    -> FREE-released  (arm 1).
#   D02 released_at the STRING "None"       -> HELD-*         . FREE-* here = FAIL-OPEN (P-85).
#   A01 live holder, fresh started_at       -> HELD-*         .
#   B01 dead holder on this host            -> TAKE-dead-pid  (arm 2).
#
# usage: linux-arms-probe.zsh <path-to-fire-program.sh>
emulate -L zsh
set -uo pipefail
FP="${1:?usage: linux-arms-probe.zsh <fire-program.sh>}"

print -r -- "=== host ==="
uname -a
print -r -- "zsh $ZSH_VERSION"
print -r -- "/bin/date -> $(readlink -f /bin/date 2>/dev/null || print /bin/date)"
print -r -- "/usr/bin/python3: $( [[ -x /usr/bin/python3 ]] && /usr/bin/python3 -V 2>&1 || print ABSENT )"
print -r -- ""

S="$(mktemp -d)"; mkdir -p "$S/.softhouse"
export GIT_CONFIG_NOSYSTEM=1 HOME="$S/home"; mkdir -p "$HOME"
printf '[user]\n\tname = T353\n\temail = t353@local\n[init]\n\tdefaultBranch = main\n' > "$HOME/.gitconfig"
git init -q "$S" 2>/dev/null
( cd "$S" && echo x > .softhouse/x && git add -A >/dev/null 2>&1 && git commit -qm seed >/dev/null 2>&1 )

H="$(hostname -s 2>/dev/null || hostname)"
NOW="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
OLD_EPOCH=$(( $(date +%s) - 360000 ))                      # 100 h ago
OLD="$(date -u -d "@$OLD_EPOCH" +%Y-%m-%dT%H:%M:%SZ 2>/dev/null || /usr/bin/python3 -c 'import sys,datetime;print(datetime.datetime.fromtimestamp(int(sys.argv[1]),datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"))' "$OLD_EPOCH")"
sleep 600 & LIVE=$!
sleep 0.1 & DEAD=$!; wait $DEAD 2>/dev/null
trap "kill $LIVE 2>/dev/null; rm -rf $S" EXIT

print -r -- "host=$H live=$LIVE dead=$DEAD now=$NOW old=$OLD"
print -r -- ""

typeset -i open_fail=0 shut_fail=0 n=0
row() {   # $1 id  $2 want (HELD | exact verdict)  $3 body  $4 what
  local id="$1" want="$2" body="$3" what="$4" out sigs verdict mark
  printf '%s' "$body" > "$S/.softhouse/LOCK"
  out="$(GEREGE_NBFI_REPO="$S" zsh "$FP" --lock-signals 2>&1)"
  sigs="$(print -r -- "$out" | grep '^lock_present' || true)"
  verdict="$(print -r -- "$out" | sed -n 's/^verdict=//p' | head -1)"
  n+=1; mark="ok"
  if [[ "$want" == HELD ]]; then
    [[ "$verdict" == HELD-* ]] || { mark="*** FAIL-OPEN"; open_fail+=1; }
  else
    [[ "$verdict" == "$want" ]] || { mark="*** FAIL-SHUT"; shut_fail+=1; }
  fi
  printf '%-4s %-14s want=%-15s got=%-16s %s\n' "$id" "$mark" "$want" "${verdict:-<none>}" "$what"
  printf '     %s\n' "$sigs"
}

row A01 HELD          "{\"host\": \"$H\", \"pid\": $LIVE, \"started_at\": \"$NOW\"}"                                  "live holder, fresh started_at"
row B01 TAKE-dead-pid "{\"host\": \"$H\", \"pid\": $DEAD, \"started_at\": \"$NOW\"}"                                  "dead holder on this host (arm 2)"
row C01 TAKE-ceiling  "{\"host\": \"$H\", \"pid\": $LIVE, \"started_at\": \"$OLD\"}"                                  "100 h old -> arm 3 CEILING"
row C02 TAKE-ceiling  "{\"host\":\"$H\",\"pid\":$LIVE,\"started_at\":\"$OLD\"}"                                       "100 h old, compact separators"
row D01 FREE-released "{\"host\": \"$H\", \"pid\": $LIVE, \"started_at\": \"$NOW\", \"released_at\": \"$NOW\"}"       "genuinely released (arm 1)"
row D02 HELD          "{\"host\": \"$H\", \"pid\": $LIVE, \"started_at\": \"$NOW\", \"released_at\": \"None\"}"       "released_at is the STRING None (F-T346-1)"
row D03 HELD          "{\"host\": \"$H\", \"pid\": $LIVE, \"started_at\": \"$NOW\", \"released_at\": \"pending\"}"    "released_at is the STRING pending"

print -r -- ""
print -r -- "ROWS=$n FAIL_OPEN=$open_fail FAIL_SHUT=$shut_fail"
(( open_fail == 0 && shut_fail == 0 )) || exit 1
exit 0
