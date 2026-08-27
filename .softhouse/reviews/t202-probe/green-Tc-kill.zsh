#!/bin/zsh
# T202 RED+GREEN for the SIGKILL leg of T-c: a stranded lock whose holder pid is
# dead must be taken over NOW, and a lock we cannot positively judge must NOT be.
#   PRE  = shipped acquisition bytes (sed -n '96,105p' of main's file)
#   POST = patched bytes             (sed -n '115,142p' of the branch file)
#   KA   = POST but the host check dropped  (would steal ANOTHER MACHINE's lock)
#   KB   = POST but `kill -0` sense inverted (would steal a LIVE holder's lock)
set -uo pipefail
LOCK=/tmp/t202/tc-lock/LOCK
LOCK_MAX_AGE_SECS=21600
FORCE=0
LOGBUF=""
log() { LOGBUF="$LOGBUF$*"$'\n'; }
PASS=0; FAIL=0; CHECKED=0
ck() { (( CHECKED++ ))
  if [[ "$4" == "$5" ]]; then (( PASS++ )); print -r -- "    ok   [$1/$2] $3 = $5"
  else (( FAIL++ )); print -r -- "    FAIL [$1/$2] $3: expected $4, got $5"; fi }

DEADPID=""
LIVEPID=""
start_live() { /bin/sleep 120 & LIVEPID=$! }
make_dead()  { /bin/sleep 0.1 & local p=$!; wait $p; DEADPID=$p }

write_lock() {  # write_lock <host> <pid>
  mkdir -p "${LOCK:h}"
  print -r -- "{"                            >  "$LOCK"
  print -r -- "  \"holder\": \"local-launchd\","    >> "$LOCK"
  print -r -- "  \"host\": \"$1\","          >> "$LOCK"
  print -r -- "  \"pid\": $2,"               >> "$LOCK"
  print -r -- "  \"started_at\": \"2026-08-22T00:00:00Z\"" >> "$LOCK"
  print -r -- "}"                            >> "$LOCK"
  # fresh mtime -> the 6h age rule alone would say "held"
  /usr/bin/touch "$LOCK"
}

# verdict of the acquisition block: EXIT0 (deferred to the other orchestrator),
# TAKEOVER (proceeded), or ERROR
run_block() {  # run_block <blockfile>
  LOGBUF=""
  local rc
  ( source "$1"; print -r -- "REACHED-TAKEOVER" ) > /tmp/t202/acq-out.txt 2>&1
  rc=$?
  ACQ_OUT="$(cat /tmp/t202/acq-out.txt)"
  [[ "$ACQ_OUT" == *REACHED-TAKEOVER* ]] && print TAKEOVER || print EXIT0
}

make_dead
start_live

for V in PRE POST KA KB; do
  case $V in
    PRE)  B=/tmp/t202/prefix-acq.zsh ;;
    POST) B=/tmp/t202/postfix-acq.zsh ;;
    *)    B=/tmp/t202/acq-mut-$V.zsh ;;
  esac
  print -r -- "== variant $V ($B) =="

  # K1 THE SIGKILL CASE: fresh lock, this host, holder pid DEAD -> take it over
  write_lock "$(hostname -s)" "$DEADPID"
  ck $V K1-deadholder "verdict" TAKEOVER "$(run_block $B)"

  # K2 holder pid ALIVE on this host -> must defer (never steal a live lock)
  write_lock "$(hostname -s)" "$LIVEPID"
  ck $V K2-liveholder "verdict" EXIT0 "$(run_block $B)"

  # K3 lock written by ANOTHER machine -> must defer, whatever that pid means here
  write_lock "some-other-mac" "$DEADPID"
  ck $V K3-otherhost "verdict" EXIT0 "$(run_block $B)"

  # K4 unparseable pid -> must defer (fail-closed on junk)
  write_lock "$(hostname -s)" 'null'
  ck $V K4-junkpid "verdict" EXIT0 "$(run_block $B)"

  # K5 pid 0 -> must defer (not a takeable judgement)
  write_lock "$(hostname -s)" 0
  ck $V K5-pidzero "verdict" EXIT0 "$(run_block $B)"
  print -r -- ""
done
kill "$LIVEPID" 2>/dev/null
print -r -- "CHECKS INSPECTED=$CHECKED  PASS=$PASS  FAIL=$FAIL"
(( CHECKED > 0 )) || { print -r -- "ERROR: zero checks inspected (P-35)"; exit 3 }
