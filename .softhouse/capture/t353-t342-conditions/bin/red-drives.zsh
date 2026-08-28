#!/bin/zsh
# T353 — P-22: *"a guard, a canary, or a control that cannot fail is worse than none —
# because it is believed"* [`.softhouse/patterns.md:473`]. Every guard this task adds is
# driven RED here before it is believed GREEN anywhere else. Each mutation is applied to a
# COPY under $TMPDIR; the real wrapper is never written.
#
# A mutation that does not APPLY is a void result, not a pass, so every one is `cmp`-checked
# against the pristine copy first and reported as VOID if it did not change the bytes.
#
# usage: red-drives.zsh <path-to-fire-program.sh>
emulate -L zsh
set -uo pipefail
FP="${1:?usage: red-drives.zsh <fire-program.sh>}"
FP="${FP:A}"
HERE="${0:A:h}"
W="$(mktemp -d "${TMPDIR:-/tmp}/t353red.XXXXXX")"
trap "rm -rf $W" EXIT

typeset -i checked=0 wrong=0

mk() {  # $1 = variant name, $2.. = sed exprs
  local name="$1"; shift
  cp "$FP" "$W/$name.sh"
  local e
  for e in "$@"; do sed -i '' "$e" "$W/$name.sh"; done
  if cmp -s "$FP" "$W/$name.sh"; then
    print -r -- "  *** MUTATION $name DID NOT APPLY — result is VOID"
    wrong+=1
    return 1
  fi
  return 0
}

report() {  # $1 label  $2 expected(RED|GREEN)  $3 observed rc  $4 detail
  local label="$1" want="$2" rc="$3" detail="$4" got mark
  checked+=1
  (( rc == 0 )) && got=GREEN || got=RED
  if [[ "$got" == "$want" ]]; then mark="ok"; else mark="*** WRONG"; wrong+=1; fi
  printf '  %-46s want=%-6s got=%-6s rc=%-3s %-9s %s\n' "$label" "$want" "$got" "$rc" "$mark" "$detail"
}

selftest() { zsh "$1" --self-test-lock-readers 2>&1 }
selftest_rc() { zsh "$1" --self-test-lock-readers >/dev/null 2>&1; print -r -- $? }
counts() { selftest "$1" | sed -n 's/^ROWS=.*//p' >/dev/null; selftest "$1" | grep '^ROWS=' }

print -r -- "=== T353 RED DRIVES ==="
print -r -- "file under mutation: $FP"
print -r -- ""

# ---------------------------------------------------------------------------------------
print -r -- "--- 0. CONTROLS. The pristine file must be GREEN on both instruments, or every"
print -r -- "       RED below is meaningless (a red that is red for the wrong reason)."
cp "$FP" "$W/pristine.sh"
report "control: self-test on pristine" GREEN "$(selftest_rc "$W/pristine.sh")" "$(counts "$W/pristine.sh")"
zsh "$HERE/epoch-parity.zsh" "$W/pristine.sh" >/dev/null 2>&1
report "control: epoch-parity on pristine" GREEN $? ""
cp "$FP" "$W/comment.sh"
sed -i '' 's|^# T353 — THE RUNNING WRAPPER|# T353 MUTATED COMMENT — THE RUNNING WRAPPER|' "$W/comment.sh"
if cmp -s "$FP" "$W/comment.sh"; then print -r -- "  *** comment control did not apply — VOID"; wrong+=1; fi
report "control: comment-only change, must stay GREEN" GREEN "$(selftest_rc "$W/comment.sh")" "a guard that reddens on a comment is noise"

print -r -- ""
print -r -- "--- 1. _iso8601_epoch. The parser that replaced \`date -j\`."
if mk r01 's#^  \[\[ "\$s" == \[0-9\].*#  [[ -n "$s" ]] || return 1#'; then
  zsh "$HERE/epoch-parity.zsh" "$W/r01.sh" >/dev/null 2>&1
  report "r01 shape glob gutted -> epoch-parity" RED $? "accepts any non-empty string"
  report "r01 shape glob gutted -> self-test" RED "$(selftest_rc "$W/r01.sh")" "$(counts "$W/r01.sh")"
fi
if mk r02 's|(( (y % 4 == 0 \&\& y % 100 != 0) \|\| y % 400 == 0 )) \&\& leap=1|(( y % 4 == 0 )) \&\& leap=1|'; then
  zsh "$HERE/epoch-parity.zsh" "$W/r02.sh" >/dev/null 2>&1
  report "r02 leap rule -> plain %4 -> epoch-parity" RED $? "2100-02-29 wrongly accepted"
fi
if mk r03 's|(( days = era \* 146097 + doe - 719468 ))|(( days = era * 146097 + doe - 719467 ))|'; then
  zsh "$HERE/epoch-parity.zsh" "$W/r03.sh" >/dev/null 2>&1
  report "r03 epoch offset off by one day -> epoch-parity" RED $? "differs from BSD date and python"
fi

print -r -- ""
print -r -- "--- 2. lock_released_at. Direction OPEN — these are the P-85 safety mutations."
if mk r04 '/^  _iso8601_epoch "\$v" >\/dev\/null || return 0$/d'; then
  report "r04 shape gate removed (= T342 as reviewed)" RED "$(selftest_rc "$W/r04.sh")" "$(counts "$W/r04.sh")"
fi
if mk r05 's|^  v="\$(_lock_json_field released_at str)" .. return 0|  print -r -- "2026-01-01T00:00:00Z"; return 0|'; then
  report "r05 maximal fail-open: always released" RED "$(selftest_rc "$W/r05.sh")" "$(counts "$W/r05.sh")"
fi

print -r -- ""
print -r -- "--- 3. lock_started_age / lock_pid_state. Direction SHUT — liveness mutations."
if mk r06 's#^  e="\$(_iso8601_epoch .*#  e="$(TZ=UTC /bin/date -j -f "%Y-%m-%dT%H:%M:%SZ" "$iso" +%s 2>/dev/null)" || return 0#'; then
  report "r06 date -j restored -> self-test ON THIS MAC" GREEN "$(selftest_rc "$W/r06.sh")" "GREEN here is the finding: the Mac cannot see this defect"
  print -r -- "       (the same mutation is driven on Linux by 03-BEFORE-linux-arms.txt, where it is RED)"
fi
if mk r07 's|^  snap="\$(_lock_json_fields host:str pid:int)" .*$|  snap="!"|'; then
  report "r07 host/pid snapshot unreadable" RED "$(selftest_rc "$W/r07.sh")" "$(counts "$W/r07.sh")"
fi
if mk r08 's|^  \[\[ "\$pstate" == dead_here \]\]      \&\& { print -r -- TAKE-dead-pid;   return 0; }|  :|'; then
  report "r08 arm 2 deleted" RED "$(selftest_rc "$W/r08.sh")" "$(counts "$W/r08.sh")"
fi
if mk r09 's|(( sage >= LOCK_CEILING_SECS ))|(( sage < LOCK_CEILING_SECS ))|'; then
  report "r09 arm 3 ceiling comparison flipped" RED "$(selftest_rc "$W/r09.sh")" "$(counts "$W/r09.sh")"
fi

print -r -- ""
print -r -- "--- 4. THE WIRING. Does the FIRE actually refuse, or does it only print?"
print -r -- "       Each row runs the REAL preflight via --probe against a scratch repo."
probe_rc() { zsh "$HERE/probe-scratch.zsh" "$1" >"$W/probe.log" 2>&1; print -r -- $? }
if [[ -n "${T353_SKIP_PROBE:-}" ]]; then
  print -r -- "  (skipped: T353_SKIP_PROBE set)"
else
  rc=$(probe_rc "$W/pristine.sh")
  report "control: --probe on pristine reaches 'probe only'" GREEN "$rc" "$(grep -c 'probe only' "$W/probe.log") 'probe only' line(s)"
  rc=$(probe_rc "$W/r04.sh")
  report "r04 (fail-open reader) -> --probe must REFUSE" RED "$rc" "$(grep -o 'FATAL: the lock-reader self-test FAILED' "$W/probe.log" | head -1)"

  # interpreter absent: rewrite EVERY /usr/bin/python3 in the copy, so the preflight sees
  # what a host without it sees.
  if mk r10 's|/usr/bin/python3|/nonexistent/python3|g'; then
    rc=$(probe_rc "$W/r10.sh")
    report "r10 /usr/bin/python3 absent -> --probe must REFUSE" RED "$rc" "$(grep -o 'FATAL: /usr/bin/python3 is missing[^.]*\.' "$W/probe.log" | head -1)"
  fi
  # interpreter present but LYING on stdout (T346 F-3): every field read becomes its banner.
  printf '#!/bin/sh\necho SPURIOUS\nexit 0\n' > "$W/liar"; chmod +x "$W/liar"
  if mk r11 "s|/usr/bin/python3|$W/liar|g"; then
    rc=$(probe_rc "$W/r11.sh")
    report "r11 interpreter prints to stdout -> --probe must REFUSE" RED "$rc" "$(grep -o 'FATAL: /usr/bin/python3 exists but did not answer' "$W/probe.log" | head -1)"
  fi
fi

print -r -- ""
print -r -- "CHECKS=$checked WRONG=$wrong"
(( wrong == 0 )) || exit 1
exit 0
